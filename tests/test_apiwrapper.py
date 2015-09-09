#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ardydedase
# @Date:   2015-08-30 11:19:30
# @Last Modified by:   ardydedase
# @Last Modified time: 2015-09-09 23:40:54

"""
test_apiwrapper
----------------------------------

Tests for `apiwrapper` module.
"""

import unittest

from apiwrapper import APIWrapper


class TestApiWrapper(unittest.TestCase):

    def setUp(self):
        # API Key that's meant for unit tests only
        self.api_key = 'py495888586774232134437415165965'
        self.api_base_url = 'http://partners.api.skyscanner.net'

    def test_make_request(self):
        api = APIWrapper()
        service_url = "{api_base_url}/apiservices/reference/v1.0/countries/en-GB".format(
            api_base_url=self.api_base_url)
        resp = api.make_request(url=service_url, apiKey=self.api_key).parsed
        self.assertTrue('Countries' in resp)

    def tearDown(self):
        pass
