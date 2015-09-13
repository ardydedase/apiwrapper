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
    resp = my_api.make_request(url=url)
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

`poll` method

- TODO

`callback` parameter in `poll` method. Defines the conditions that determines if the polling is complete. Should return a boolean::

    class TestPoller(APIWrapper):
        def _my_poll_callback(self, poll_resp):
            """
            'poll_resp' is returned by `make_request`
            """
            if poll_resp.parsed is None:
                return False
            success_list = ['UpdatesComplete', True, 'COMPLETE']
            status = poll_resp.parsed.get(
                'Status', poll_resp.parsed.get('status'))
            if status is None:
                raise RuntimeError('Unable to get poll response status.')
            return status in success_list
            

Response callbacks
~~~~~~~~~~~~~~~~~~

`callback` parameter in `make_request` method::

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
    


