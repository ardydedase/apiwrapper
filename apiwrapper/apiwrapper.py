#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ardydedase
# @Date:   2015-08-30 11:19:30
# @Last Modified by:   ardydedase
# @Last Modified time: 2015-09-03 15:11:32

import time
import requests
import logging
import sys

from requests.exceptions import ConnectionError

def configure_logger(log_level=logging.DEBUG):
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    try:
        sa = logging.StreamHandler(stream=sys.stdout)
    except TypeError:
        sa = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')
    sa.setFormatter(formatter)
    logger.addHandler(sa)
    return logger


log = configure_logger()


class EmptyResponse(Exception):

    """Is thrown when API returns an empty response."""
    pass


class InvalidResponse(ValueError):

    """Is thrown when API returns a truncated or invalid json response."""
    pass


class MissingParameter(KeyError):

    """Is thrown when expected request parameter is missing."""
    pass


class InvalidParameter(KeyError):

    """Is thrown when invalid request parameter is present."""
    pass

STRICT, GRACEFUL, IGNORE = 'strict', 'graceful', 'ignore'


class APIWrapper(object):

    def _default_resp_callback(self, resp, **params):

        log.debug("resp: %s" % resp)
        try:
            return resp.json()
        except ValueError as e:
            log.debug(e)
            raise InvalidResponse

    def make_request(self, service_url, method='get', headers=None, data=None, callback=None, errors=STRICT, **params):
        error_modes = (STRICT, GRACEFUL, IGNORE)
        error_mode = errors or GRACEFUL
        if error_mode.lower() not in error_modes:
            raise ValueError(
                'Possible values for errors argument are: %s' % ', '.join(error_modes))

        if callback is None:
            callback = self._default_resp_callback

        request = getattr(requests, method.lower())

        try:
            r = request(service_url, headers=headers, data=data, params=params)
            log.debug('* Request URL: %s' % r.url)
            log.debug('* Request method: %s' % method)
            log.debug('* Request query params: %s' % params)
            log.debug('* Request headers: %s' % headers)
            try:
                return callback(r, **params)
            except TypeError:
                raise MissingParameter
        except ConnectionError as ex:
            raise Exception

    def poll_session(self, poll_url, initial_delay=2, delay=1, tries=20, errors=STRICT, is_complete_callback=None, **params):
        """
        Poll the URL
        :param poll_url - URL to poll, should be returned by 'create_session' call
        :param initial_delay - specifies how many seconds to wait before the first poll
        :param delay - specifies how many seconds to wait between the polls
        :param tries - number of polls to perform
        :param errors - errors handling mode, see corresponding parameter in 'make_request' method
        :param params - additional query params for each poll request
        """
        time.sleep(initial_delay)
        poll_response = None

        if is_complete_callback == None:
            is_complete_callback = self._default_poll_callback

        for n in range(tries):
            poll_response = self.make_request(poll_url, headers=self._headers(),
                                              errors=errors, **params)

            if is_complete_callback(poll_response):
                return poll_response
            else:
                time.sleep(delay)

        if STRICT == errors:
            raise ExceededRetries(
                "Failed to poll within {0} tries.".format(tries))
        else:
            return poll_response

    def _default_poll_callback(self, poll_resp):
        """
        Checks the condition in poll response to determine if it is complete
        and no subsequent poll requests should be done.
        """
        if poll_resp.parsed is None:
            return False
        success_list = ['UpdatesComplete', True, 'COMPLETE']
        status = None
        if self.response_format == 'xml':
            status = poll_resp.parsed.find('./Status').text
        elif self.response_format == 'json':
            status = poll_resp.parsed.get(
                'Status', poll_resp.parsed.get('status'))
        if status is None:
            raise RuntimeError('Unable to get poll response status.')
        return status in success_list
