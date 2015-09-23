========
Usage
========

Basic Usage
~~~~~~~~~~~

To use API Wrapper in a project::

    from apiwrapper import APIWrapper

Use it as a helper::

    my_api = APIWrapper()
    url = 'https://api.github.com/users/ardydedase/repos'
    resp = my_api.make_request(url, method='get', headers=None, data=None, callback=None).parsed
    print(resp)

Use it as a parent class::
    
    class GithubAPI(APIWrapper):
        def get_repos(self, username):
            """
            Uses 'make_request' method              
            """
            url = "https://api.github.com/users/{username}/repos".format(username=username)
            return self.make_request(url, method='get', headers=None, data=None, callback=None).parsed

Polling
~~~~~~~

APIWrapper's built-in polling method makes it convenient to declare polling methods and calls. Its flexibility allows a number of options including switching between JSON and XML response types.

In this `poll` method example, let's use Skyscanner's API.

Let's start by importing `APIWrapper` class and all the error modes 
available in the apiwrapper package::
    
    from apiwrapper import (
        APIWrapper,
        STRICT,
        GRACEFUL,
        IGNORE)

Next will be to declare the `Flights` class that will inherit 
our `APIWrapper` parent class. 
The parent APIWrapper class is initizialized with `response_format='json'`.
The `api_key` is a private property so we don't have to pass 
it as an argument every time we call `make_request`::

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

Wrap the `make_request` method from `APIWrapper` and inject the `apikey` only if it is not available in the request url::

    def make_request(self, url, method='get', headers=None,
                     data=None, callback=None, errors=STRICT,
                     verify=False, **params):
        """
        Call the `make_request` method from apiwrapper.
        So we can inject the apikey when it is not available.
        """
        if 'apikey' not in url.lower():
            params.update({
                'apiKey': self.api_key
            })
        return super(Flights, self).make_request(url, method, headers,
                                                 data, callback, errors,
                                                 verify, **params)

The `create_session` method prepares the API's polling session and returns the polling url `poll_url`. This method uses the `make_request` method declared above. It also makes use of the  `_headers()` method from `APIWrapper`::

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

This boolean method `is_poll_complete_callback` will be passed as a callback parameter in the `APIWrapper.poll` method call. 
`is_poll_complete_callback` will receive the `poll` response from `poll` method as a parameter.
This method will then use the `poll_resp` value to check whether the polling is complete or not and returns a boolean::

    def _is_poll_complete_callback(self, poll_resp):
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

And lastly, the `get_result` method polls the API using the URL that was returned from `create_session`. 
Notice that we are passing `_is_poll_complete_callback` as an argument to the `is_poll_complete_callback` parameter in the `poll` method. After the poll is complete, the `get_result` method will return the flight search result::

    def get_result(self, errors=STRICT, **params):
        """
        Get all results, no filtering,
        etc. by creating and polling the session.
        """
        service_url = self.create_session(**params)
        return self.poll(service_url, errors=errors, is_poll_complete_callback=self._is_poll_complete_callback)


Now that the `Flights` class is ready. The `get_result` method can be called as follows:
    
.. code:: python

        from datetime import datetime, timedelta

        datetime_format = '%Y-%m-%d'
        outbound_datetime = datetime.now() + timedelta(days=7)
        inbound_datetime = outbound_datetime + timedelta(days=3)
        outbound_date = outbound_datetime.strftime(datetime_format)
        inbound_date = inbound_datetime.strftime(datetime_format)

        flights_service = Flights(<skyscanner_api_key>)
        result = flights_service.get_result(
            errors=GRACEFUL,
            country='UK',
            currency='GBP',
            locale='en-GB',
            originplace='SIN-sky',
            destinationplace='KUL-sky',
            outbounddate=outbound_date,
            inbounddate=inbound_date,
            adults=1).parsed

Response callbacks
~~~~~~~~~~~~~~~~~~

`callback` parameter in `make_request` method. It passes the `Response` object as an argument::

    class GithubAPI(APIWrapper):
        def _my_callback(self, resp):
            """
            'resp' is a Response object returned from `requests` library
            """
            return resp.json()

                
        def get_repos(self, username):
            """
            Uses 'make_request' method
            """
            url = "https://api.github.com/users/{username}/repos".format(username=username)
            return self.make_request(url, method='get', headers=None, data=None, callback=self._my_callback)
            