# -*- coding: utf8 -*-
from collective.contact.core import logged_actions
from collective.contact.core.testing import FUNCTIONAL
from ecreall.helpers.testing.base import BaseTest
from plone import api
from plone.app.testing.interfaces import TEST_USER_NAME

import unittest


def rmv_uid(idx):
    return logged_actions[idx][logged_actions[idx].index(" PATH=") + 1:]


class TestBrowserUtils(unittest.TestCase, BaseTest):

    layer = FUNCTIONAL

    def setUp(self):
        super(TestBrowserUtils, self).setUp()
        self.login(TEST_USER_NAME)
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        mydirectory = self.portal['mydirectory']
        self.degaulle = mydirectory['degaulle']
        self.adt = self.degaulle['adt']
        self.gadt = self.degaulle['gadt']
        self.pepper = mydirectory['pepper']
        self.sergent_pepper = self.pepper['sergent_pepper']
        self.rambo = mydirectory['rambo']
        self.armeedeterre = mydirectory['armeedeterre']
        self.corpsa = self.armeedeterre['corpsa']
        self.divisionalpha = self.corpsa['divisionalpha']
        self.regimenth = self.divisionalpha['regimenth']
        self.brigadelh = self.regimenth['brigadelh']
        self.general_adt = self.armeedeterre['general_adt']
        self.sergent_lh = self.brigadelh['sergent_lh']
        self.draper = mydirectory['draper']
        self.captain_crunch = self.draper['captain_crunch']
        self.mydirectory = mydirectory

    def call_view(self, obj, view_name):
        view = obj.restrictedTraverse(view_name)
        view.update()
        view.request["PARENTS"].insert(0, obj)
        view.request["URL"] = "{}/{}".format(obj.absolute_url(), view_name)
        view.render()

    def test_audit_access(self):
        self.call_view(self.armeedeterre, "view")
        self.assertEqual(len(logged_actions), 0)
        # we set the registry record to True
        api.portal.set_registry_record("collective.contact.core.interfaces.IContactCoreParameters."
                                       "audit_contact_access", True)
        # check organisation view
        self.call_view(self.armeedeterre, "view")
        self.assertEqual(len(logged_actions), 2)
        self.assertEqual(rmv_uid(0), "PATH=/plone/mydirectory/armeedeterre "
                         "CTX_PATH=/plone/mydirectory/armeedeterre CTX=contact_view")
        self.assertEqual(rmv_uid(1), "PATH=/plone/mydirectory/degaulle/adt "
                         "CTX_PATH=/plone/mydirectory/armeedeterre CTX=contact_view")
        # check sub organization view
        logged_actions[:] = []  # clear
        self.call_view(self.brigadelh, "view")
        self.assertEqual(len(logged_actions), 2)
        self.assertEqual(rmv_uid(0), "PATH=/plone/mydirectory/armeedeterre/corpsa/divisionalpha/regimenth/brigadelh "
                         "CTX_PATH=/plone/mydirectory/armeedeterre/corpsa/divisionalpha/regimenth/brigadelh "
                         "CTX=contact_view")
        self.assertEqual(rmv_uid(1), "PATH=/plone/mydirectory/rambo/brigadelh "
                         "CTX_PATH=/plone/mydirectory/armeedeterre/corpsa/divisionalpha/regimenth/brigadelh "
                         "CTX=contact_view")
        # check person view
        logged_actions[:] = []  # clear
        self.call_view(self.degaulle, "view")
        self.assertEqual(len(logged_actions), 5)
        self.assertEqual(rmv_uid(0), "PATH=/plone/mydirectory/degaulle "
                         "CTX_PATH=/plone/mydirectory/degaulle CTX=contact_view")
        self.assertEqual(rmv_uid(1), "PATH=/plone/mydirectory/degaulle/adt "
                         "CTX_PATH=/plone/mydirectory/degaulle CTX=contact_view")
        self.assertEqual(rmv_uid(2), "PATH=/plone/mydirectory/armeedeterre "
                         "CTX_PATH=/plone/mydirectory/degaulle CTX=contact_view")
        self.assertEqual(rmv_uid(3), "PATH=/plone/mydirectory/degaulle/gadt "
                         "CTX_PATH=/plone/mydirectory/degaulle CTX=contact_view")
        self.assertEqual(rmv_uid(4), "PATH=/plone/mydirectory/armeedeterre "
                         "CTX_PATH=/plone/mydirectory/degaulle CTX=contact_view")
        # check position view
        logged_actions[:] = []  # clear
        self.call_view(self.general_adt, "view")
        self.assertEqual(len(logged_actions), 1)
        self.assertEqual(rmv_uid(0), "PATH=/plone/mydirectory/armeedeterre/general_adt "
                         "CTX_PATH=/plone/mydirectory/armeedeterre/general_adt CTX=contact_view")