# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.utils import DisplayList
from bika.lims.browser import BrowserView
from bika.lims.browser.widgets.serviceswidget import ServicesView
import json


class AJAXGetWorksheetTemplateInstruments(BrowserView):
    """
    Returns a vocabulary with the instruments available for the selected method
    """
    def __call__(self):
        if 'method_uid' in self.request.keys():
            method_uid = str(json.loads(self.request.get('method_uid', '')))
            cfilter = {
                'portal_type': 'Instrument',
                'inactive_state': 'active',
                'getMethodUID': method_uid}
            bsc = getToolByName(self, 'bika_setup_catalog')
            items = [{'uid': '', 'm_title': 'No instrument'}] + [
                {'uid': o.UID, 'm_title': o.Title} for o in
                bsc(cfilter)]
            items.sort(lambda x, y: cmp(x['m_title'], y['m_title']))
            return json.dumps(items)
