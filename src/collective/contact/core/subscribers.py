from Acquisition import aq_get
from collective.contact.core.behaviors import IContactDetails
from collective.contact.core.content.directory import IDirectory
from collective.contact.core.content.organization import IOrganization
from collective.contact.core.content.person import IPerson
from collective.contact.core.content.position import IPosition
from collective.contact.core.interfaces import IContactCoreParameters
from collective.contact.core.interfaces import IHeldPosition
from collective.contact.widget.interfaces import IContactContent
from five import grok
from plone import api
from plone.app.iterate.interfaces import IWorkingCopy
from plone.app.linkintegrity.handlers import referencedObjectRemoved as baseReferencedObjectRemoved
from plone.app.linkintegrity.interfaces import ILinkIntegrityInfo
from plone.registry.interfaces import IRecordModifiedEvent
from z3c.form.interfaces import NO_VALUE
from zc.relation.interfaces import ICatalog
from zope import component
from zope.container.contained import ContainerModifiedEvent
from zope.interface import providedBy
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.schema import getFields


try:
    from plone.app.referenceablebehavior.referenceable import IReferenceable
except ImportError:
    from zope.interface import Interface

    class IReferenceable(Interface):
        pass


# update indexes of related content when a content is modified
# you can monkey patch this value if you have an index that needs this
indexes_to_update = ['SearchableText']


@grok.subscribe(IHeldPosition, IObjectAddedEvent)
@grok.subscribe(IHeldPosition, IObjectModifiedEvent)
def update_related_with_held_position(obj, event=None):
    if isinstance(event, ContainerModifiedEvent):
        return

    obj.get_person().reindexObject(idxs=indexes_to_update)


@grok.subscribe(IPosition, IObjectModifiedEvent)
def update_related_with_position(obj, event=None):
    if isinstance(event, ContainerModifiedEvent):
        return

    for held_position in obj.get_held_positions():
        held_position.reindexObject(idxs=indexes_to_update)
        update_related_with_held_position(held_position)


@grok.subscribe(IPerson, IObjectModifiedEvent)
def update_related_with_person(obj, event=None):
    if isinstance(event, ContainerModifiedEvent):
        return

    for held_position in obj.get_held_positions():
        held_position.reindexObject(idxs=indexes_to_update)


@grok.subscribe(IOrganization, IObjectModifiedEvent)
def update_related_with_organization(obj, event=None):
    if isinstance(event, ContainerModifiedEvent):
        return

    for held_position in obj.get_held_positions():
        held_position.reindexObject(idxs=indexes_to_update)
        update_related_with_held_position(held_position)

    for position in obj.get_positions():
        position.reindexObject(idxs=indexes_to_update)
        for held_position in position.get_held_positions():
            held_position.reindexObject(idxs=indexes_to_update)
            update_related_with_held_position(held_position)

    for child in obj.values():
        if IOrganization.providedBy(child):
            child.reindexObject(idxs=indexes_to_update)
            update_related_with_organization(child)


def referenceRemoved(obj, event, toInterface=IContactContent):
    """Store information about the removed link integrity reference.
    """
    # inspired from z3c/relationfield/event.py:breakRelations
    # and plone/app/linkintegrity/handlers.py:referenceRemoved
    # if the object the event was fired on doesn't have a `REQUEST` attribute
    # we can safely assume no direct user action was involved and therefore
    # never raise a link integrity exception...
    request = aq_get(obj, 'REQUEST', None)
    if not request:
        return
    storage = ILinkIntegrityInfo(request)

    catalog = component.queryUtility(ICatalog)
    intids = component.queryUtility(IIntIds)
    if catalog is None or intids is None:
        return

    # find all relations that point to us
    obj_id = intids.queryId(obj)
    if obj_id is None:
        return

    rels = list(catalog.findRelations({'to_id': obj_id}))
    for rel in rels:
        if toInterface.providedBy(rel.to_object):
            storage.addBreach(rel.from_object, rel.to_object)


def referencedObjectRemoved(obj, event):
    allowed_interfaces = set([
        IDirectory,
        IOrganization,
        IPerson,
        IHeldPosition,
        IPosition,
    ])
    if len(allowed_interfaces.intersection([i for i in providedBy(obj)])) == 0:
        return
    # Avoid an error when we try to remove a working copy (plone.app.iterate)
    if IWorkingCopy.providedBy(obj):
        return
    if not IReferenceable.providedBy(obj):
        baseReferencedObjectRemoved(obj, event)


@grok.subscribe(IContactDetails, IObjectModifiedEvent)
@grok.subscribe(IContactDetails, IObjectAddedEvent)
def clear_fields_use_parent_address(obj, event):
    """If 'use parent address' has been selected,
    ensure content address fields are cleared
    """
    if obj.use_parent_address and obj.use_parent_address != NO_VALUE:
        upa_field = getFields(IContactDetails)['use_parent_address']
        slave_ids = [f['name'] for f in upa_field.slave_fields]
        for field_name in slave_ids:
            try:
                delattr(obj, field_name)
            except AttributeError:
                pass


def recordModified(event):
    """
        Manage configuration change in registry
    """
    if (IRecordModifiedEvent.providedBy(event) and event.record.interfaceName and
            event.record.interface == IContactCoreParameters):
        if event.record.fieldName == 'contact_source_metadata_content':
            pc = api.portal.get_tool('portal_catalog')
            for brain in pc(object_provides=IContactContent.__identifier__):
                brain.getObject().reindexObject(idxs=['contact_source'])
