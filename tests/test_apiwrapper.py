#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ardydedase
# @Date:   2015-08-30 11:19:30
# @Last Modified by:   ardydedase
# @Last Modified time: 2015-09-20 15:26:17

"""
test_apiwrapper
----------------------------------

Tests for `apiwrapper` module.
"""

import unittest

from datetime import datetime, timedelta

from apiwrapper import (
    APIWrapper,
    STRICT,
    GRACEFUL,
    IGNORE)


class Flights(APIWrapper):

    """
    Skyscanner Flights Live Pricing
    http://business.skyscanner.net/
    portal/en-GB/Documentation/FlightsLivePricingList
    """
    API_HOST = 'http://partners.api.skyscanner.net'
    PRICING_SESSION_URL = '{api_host}/apiservices/pricing/v1.0'.format(
        api_host=API_HOST)

    def __init__(self, api_key):
        self.api_key = api_key
        super(Flights, self).__init__(response_format='json')

    def make_request(self, url, method='get', headers=None,
                     data=None, callback=None, errors=STRICT,
                     verify=False, timeout=None, **params):
        """
        Call the `make_request` method from apiwrapper.
        So we can inject the apikey when it's not available.
        """
        if 'apikey' not in url.lower():
            params.update({
                'apiKey': self.api_key
            })
        return super(Flights, self).make_request(url, method, headers,
                                                 data, callback, errors,
                                                 verify, **params)

    def create_session(self, **params):
        """
        Create the session
        date format: YYYY-mm-dd
        location: ISO code.
        After creating the session,
        this method will return the poll_url.
        """
        service_url = self.PRICING_SESSION_URL
        return self.make_request(service_url,
                                 method='post',
                                 headers=self._headers(),
                                 callback=lambda resp: resp.headers[
                                     'location'],
                                 data=params)

    def get_result(self, errors=STRICT, **params):
        """
        Get all results, no filtering,
        etc. by creating and polling the session.
        """
        service_url = self.create_session(**params)
        return self.poll(service_url, errors=errors)


class TestApiWrapper(unittest.TestCase):

    def setUp(self):
        # API Key that's meant for unit tests only
        self.api_key = 'py495888586774232134437415165965'
        self.api_base_url = 'http://partners.api.skyscanner.net'

        datetime_format = '%Y-%m-%d'
        outbound_datetime = datetime.now() + timedelta(days=7)
        inbound_datetime = outbound_datetime + timedelta(days=3)
        self.outbound_days = outbound_datetime.strftime(datetime_format)
        self.inbound_days = inbound_datetime.strftime(datetime_format)

    def test_make_request(self):
        api = APIWrapper()
        service_url = "{api_base_url}/apiservices/reference/v1.0/countries/en-GB".format(
            api_base_url=self.api_base_url)
        resp = api.make_request(url=service_url, apiKey=self.api_key).parsed
        self.assertTrue('Countries' in resp)

    def test_callback(self):
        def mycallback(resp):
            print("resp from callback: %s" % resp)
            return resp.json()

        api = APIWrapper()
        service_url = "{api_base_url}/apiservices/reference/v1.0/countries/en-GB".format(
            api_base_url=self.api_base_url)
        resp = api.make_request(
            url=service_url, apiKey=self.api_key, callback=mycallback)
        self.assertTrue('Countries' in resp)

    def test_skyscanner_create_session(self):
        flights_service = Flights(self.api_key)
        poll_url = flights_service.create_session(
            country='UK',
            currency='GBP',
            locale='en-GB',
            originplace='SIN-sky',
            destinationplace='KUL-sky',
            outbounddate=self.outbound_days,
            inbounddate=self.inbound_days,
            adults=1)

        print(poll_url)
        self.assertTrue(poll_url)

    def test_skyscanner_get_result(self):
        flights_service = Flights(self.api_key)
        result = flights_service.get_result(
            errors=GRACEFUL,
            country='UK',
            currency='GBP',
            locale='en-GB',
            originplace='SIN-sky',
            destinationplace='KUL-sky',
            outbounddate=self.outbound_days,
            inbounddate=self.inbound_days,
            adults=1).parsed

        print(result)

    def tearDown(self):
        pass
