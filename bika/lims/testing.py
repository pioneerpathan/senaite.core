# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

import Products.ATExtensions
import collective.js.jqueryui
import plone.app.iterate
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.setuphandlers import setupPortalContent
from Testing.makerequest import makerequest
from plone.app.testing import FunctionalTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.testing import logout
from plone.testing import z2
from plone.testing.z2 import Browser

import bika.lims
from bika.lims import logger
from bika.lims.exportimport.load_setup_data import LoadSetupData


class SimpleTestLayer(PloneSandboxLayer):
    """Configure a default site with bika.lims addon installed,
    and with no data or settings loaded.
    """
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        self.loadZCML(package=Products.ATExtensions)
        self.loadZCML(package=plone.app.iterate)
        self.loadZCML(package=collective.js.jqueryui)
        self.loadZCML(package=bika.lims)

        # Required by Products.CMFPlone:plone-content
        z2.installProduct(app, 'Products.PythonScripts')
        z2.installProduct(app, 'bika.lims')

    def setUpPloneSite(self, portal):
        login(portal.aq_parent, 'admin')

        wf = getToolByName(portal, 'portal_workflow')
        wf.setDefaultChain('plone_workflow')
        setupPortalContent(portal)

        # make sure we have folder_listing as a template
        portal.getTypeInfo().manage_changeProperties(
            view_methods=['folder_listing'],
            default_view='folder_listing')
        from AccessControl import getSecurityManager

        user = getSecurityManager().getUser()
        user.getRolesInContext(portal)
        applyProfile(portal, 'bika.lims:default')

        # Add some test users
        for role in ('LabManager',
                     'LabClerk',
                     'Analyst',
                     'Verifier',
                     'Sampler',
                     'Preserver',
                     'Publisher',
                     'Member',
                     'Reviewer',
                     'RegulatoryInspector'):
            for user_nr in range(2):
                if user_nr == 0:
                    username = "test_%s" % (role.lower())
                else:
                    username = "test_%s%s" % (role.lower(), user_nr)
                try:
                    member = portal.portal_registration.addMember(
                        username,
                        username,
                        properties={
                            'username': username,
                            'email': username + "@example.com",
                            'fullname': username}
                    )
                    # Add user to all specified groups
                    group_id = role + "s"
                    group = portal.portal_groups.getGroupById(group_id)
                    if group:
                        group.addMember(username)
                    # Add user to all specified roles
                    member._addRole(role)
                    # If user is in LabManagers, add Owner local role on clients folder
                    if role == 'LabManager':
                        portal.clients.manage_setLocalRoles(username,
                                                            ['Owner', ])
                except ValueError:
                    pass  # user exists

        # Force the test browser to show the site always in 'en'
        ltool = portal.portal_languages
        ltool.manage_setLanguageSettings('en', ['en'],
                                         setUseCombinedLanguageCodes=False,
                                         startNeutral=True)

        logout()


def getBrowser(portal, loggedIn=True, username=TEST_USER_NAME,
               password=TEST_USER_PASSWORD):
    """Instantiate and return a testbrowser for convenience
    This is done weirdly because I could not figure out how else to
    pass the browser to the doctests"""
    browser = Browser(portal)
    browser.addHeader('Accept-Language', 'en')
    browser.handleErrors = False
    if loggedIn:
        browser.open(portal.absolute_url())
        browser.getControl('Login Name').value = username
        browser.getControl('Password').value = password
        browser.getControl('Log in').click()
        assert ('You are now logged in' in browser.contents)
    return browser


BIKA_SIMPLE_FIXTURE = SimpleTestLayer()
BIKA_SIMPLE_FIXTURE['getBrowser'] = getBrowser
BIKA_SIMPLE_TESTING = FunctionalTesting(
    bases=(BIKA_SIMPLE_FIXTURE,),
    name="SimpleTestingLayer:Functional"
)


class BikaTestLayer(SimpleTestLayer):
    """
    Loads setupdata file, so you will have a site with initial data.
    """
    def setUpZope(self, app, configurationContext):
        super(BikaTestLayer, self).setUpZope(app, configurationContext)

    def setUpPloneSite(self, portal):
        super(BikaTestLayer, self).setUpPloneSite(portal)

        login(portal, 'admin')  # again
        # load test data
        self.request = makerequest(portal.aq_parent).REQUEST
        self.request.form['setupexisting'] = 1
        self.request.form['existing'] = "bika.lims:test"
        lsd = LoadSetupData(portal, self.request)
        logger.info('Loading datas...')
        lsd()
        logger.info('Loading data finished...')
        logout()

BIKA_FUNCTIONAL_FIXTURE = BikaTestLayer()
BIKA_FUNCTIONAL_FIXTURE['getBrowser'] = getBrowser
BIKA_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(BIKA_FUNCTIONAL_FIXTURE,),
    name="BikaTestingLayer:Functional"
)
