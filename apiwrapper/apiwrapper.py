#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: ardydedase
# @Date:   2015-08-30 11:19:30
# @Last Modified by:   ardydedase
# @Last Modified time: 2015-09-24 19:36:51

import time
import requests
import logging
import sys

from requests.exceptions import ConnectionError

try:
    import lxml.etree as etree
except ImportError:
    import xml.etree.ElementTree as etree


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


class ExceededRetries(Exception):

    """Is thrown when allowed number of polls were
     performed but response is not complete yet."""
    pass


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

    def __init__(self, response_format='json'):
        self.response_format = response_format

    def _default_resp_callback(self, resp):
        if not resp or not resp.content:
            raise EmptyResponse('Response has no content.')

        try:
            parsed_resp = self._parse_resp(resp, self.response_format)
        except (ValueError, SyntaxError):
            raise ValueError('Invalid %s in response: %s...' %
                             (self.response_format.upper(),
                              resp.content[:100]))

        return parsed_resp

    def make_request(self, url, method='get', headers=None, data=None,
                     callback=None, errors=STRICT, verify=False, timeout=None, **params):
        """
        Reusable method for performing requests.
        :param url - URL to request
        :param method - request method, default is 'get'
        :param headers - request headers
        :param data - post data
        :param callback - callback to be applied to response,
                          default callback will parse response as json object.
        :param errors - specifies communication errors handling mode, possible
                        values are:
                         * strict (default) - throw an error as soon as one
                            occurred
                         * graceful - ignore certain errors, e.g. EmptyResponse
                         * ignore - ignore all errors and return a result in
                                    any case.
                                    NOTE that it DOES NOT mean that no
                                    exceptions can be
                                    raised from this method, it mostly ignores
                                    communication
                                    related errors.
                         * None or empty string equals to default
        :param verify - whether or not to verify SSL cert, default to False
        :param timeout - the timeout of the request in second, default to None
        :param params - additional query parameters for request
        """
        error_modes = (STRICT, GRACEFUL, IGNORE)
        error_mode = errors or GRACEFUL
        if error_mode.lower() not in error_modes:
            raise ValueError(
                'Possible values for errors argument are: %s'
                % ','.join(error_modes))

        if callback is None:
            callback = self._default_resp_callback

        request = getattr(requests, method.lower())
        log.debug('* Request URL: %s' % url)
        log.debug('* Request method: %s' % method)
        log.debug('* Request query params: %s' % params)
        log.debug('* Request headers: %s' % headers)
        log.debug('* Request timeout: %s' % timeout)

        r = request(
            url, headers=headers, data=data, verify=verify, timeout=timeout, params=params)

        log.debug('* r.url: %s' % r.url)

        try:
            r.raise_for_status()
            return callback(r)
        except Exception as e:
            return self._with_error_handling(r, e,
                                             error_mode, self.response_format)

    def _headers(self):
        return {'Accept': 'application/%s' % self.response_format}

    @staticmethod
    def _parse_resp(resp, response_format):
        resp.parsed = etree.fromstring(
            resp.content) if response_format == 'xml' else resp.json()
        return resp

    @staticmethod
    def _with_error_handling(resp, error, mode, response_format):
        """
        Static method for error handling.

        :param resp - API response
        :param error - Error thrown
        :param mode - Error mode
        :param response_format - XML or json
        """
        def safe_parse(r):
            try:
                return APIWrapper._parse_resp(r, response_format)
            except (ValueError, SyntaxError) as ex:
                log.error(ex)
                r.parsed = None
                return r

        if isinstance(error, requests.HTTPError):
            if resp.status_code == 400:
                # It means that request parameters were rejected by the server,
                # so we need to enrich standard error message
                # with 'ValidationErrors'
                # from the response
                resp = safe_parse(resp)
                if resp.parsed is not None:
                    parsed_resp = resp.parsed
                    messages = []
                    if response_format == 'xml' and\
                            parsed_resp.find('./ValidationErrors') is not None:
                        messages = [e.find('./Message').text
                                    for e in parsed_resp.findall('./ValidationErrors/ValidationErrorDto')]
                    elif response_format == 'json' and 'ValidationErrors' in parsed_resp:
                        messages = [e['Message']
                                    for e in parsed_resp['ValidationErrors']]
                    error = requests.HTTPError(
                        '%s: %s' % (error, '\n\t'.join(messages)), response=resp)
            elif resp.status_code == 429:
                error = requests.HTTPError('%sToo many requests in the last minute.' % error,
                                           response=resp)

        if STRICT == mode:
            raise error
        elif GRACEFUL == mode:
            if isinstance(error, EmptyResponse):
                # Empty response is returned by the API occasionally,
                # in this case it makes sense to ignore it and retry.
                log.warning(error)
                resp.parsed = None
                return resp

            elif isinstance(error, requests.HTTPError):
                # Ignoring 'Too many requests' error,
                # since subsequent retries will come after a delay.
                if resp.status_code == 429:    # Too many requests
                    log.warning(error)
                    return safe_parse(resp)
                else:
                    raise error
            else:
                raise error
        else:
            # ignore everything, just log it and return whatever response we
            # have
            log.error(error)
            return safe_parse(resp)

    def poll(self, url, initial_delay=2, delay=1, tries=20, errors=STRICT, is_complete_callback=None, **params):
        """
        Poll the URL
        :param url - URL to poll, should be returned by 'create_session' call
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
            poll_response = self.make_request(url, headers=self._headers(),
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
