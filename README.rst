=================================
API Wrapper
=================================

.. image:: https://api.travis-ci.org/ardydedase/apiwrapper.svg
        :target: https://travis-ci.org/ardydedase/apiwrapper

.. image:: https://img.shields.io/pypi/v/apiwrapper.svg
        :target: https://pypi.python.org/pypi/apiwrapper

.. image:: https://readthedocs.org/projects/apiwrapper/badge/?version=latest
        :target: https://readthedocs.org/projects/apiwrapper/?badge=latest
        :alt: Documentation Status

Simple API Wrapper

* Free software: BSD license
* Documentation: https://apiwrapper.readthedocs.org.

Overview
--------

Recently noticed a pattern and repeated pieces of code in Python API wrappers for simple requests and polling. A separate Python package will minimize code duplication and encourage de-coupling of logic from the API request functions.

Installation
------------

At the command line::

    $ easy_install apiwrapper

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv apiwrapper
    $ pip install apiwrapper

Getting started with a simple request
-------------------------------------

.. code:: python
    
    # as a helper class
    from apiwrapper import APIWrapper

    my_api = APIWrapper()
    url = 'https://api.github.com/users/ardydedase/repos'
    resp = my_api.make_request(url=url)
    print(resp)

    # as a parent class
    class GithubAPI(APIWrapper):
        def get_repos(self, username):
            """
            Uses `make_request` method              
            """
            url = "https://api.github.com/users/{username}/repos".format(username=username)
            return self.make_request(url, method='get', headers=None, data=None, callback=None)

More features including polling
-------------------------------

Read the docs: https://apiwrapper.readthedocs.org/en/latest/usage.html

Or use `apiwrapper/apiwrapper.py` as a reference. Implementation is straightforward.
