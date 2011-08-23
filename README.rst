
==========
JS TestNet
==========

JS TestNet is a Django_ web service that coordinates the execution of
JavaScript tests across web browsers.  It was designed to run pure JavaScript
tests with Qunit_ in a CI environment like Jenkins_ and to get test feedback
from real web browsers.  It is probably flexible enough for other JavaScript
test runners too.

.. _Django: http://www.djangoproject.com/
.. _Qunit: http://docs.jquery.com/Qunit
.. _Jenkins: http://jenkins-ci.org/

.. contents::
      :local:

How Does It Work?
=================

JS TestNet lets you turn any web browser into a JavaScript test runner. You
control everything through a client (like `JsTestNetLib`_); the client talks
to the server and it doesn't have to run on the same machine as any web
browser.

Here is a screenshot of Firefox and Chrome simultaneously running a
QUnit based test suite. You can see a script running in a terminal to kick off
the tests and collect results.

.. image:: http://kumar303.github.com/jstestnet/jstestnet-screenshot.png

This screenshot was taken with a local development install of the JS Test Net
server. In a real world situation you'd probably run each web browser in a
headless virtual machine and you'd start the tests using the shell as part of
your Continuous Integration system.

Install
=======

First, you need Python_ 2.6 or greater.  Clone this repository, create a
virtualenv_, then cd into the project and run::

  pip install -r requirements.txt
  pip install -r requirements/compiled.txt

Make your own settings_local.py::

  cp settings_local.py-example settings_local.py

Set up a MySQL user and database::

  create user jstestnet_dev@localhost identified by 'test';
  create database jstestnet_dev;
  grant all on jstestnet_dev.* to jstestnet_dev;

Then enter the credentials in settings_local.py::

  DATABASES['default']['NAME'] = 'jstestnet_dev'
  DATABASES['default']['USER'] = 'jstestnet_dev'
  DATABASES['default']['PASSWORD'] = 'test'

Also in settings_local.py, uncomment the ``HMAC_KEYS`` setting and enter some
unique value.

Create the database::

  ./manage.py syncdb

During the process, you will be prompted to create a superuser. You should do
so, or run the ``createsuperuser`` management command later.

::

  ./manage.py createsuperuser

Start the server and open the front page to see the system status.

::

  ./manage.py runserver

.. _Python: http://python.org/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv

Adding a Test Suite
===================

A test suite is a URL to an HTML page that runs tests in a web browser when
loaded.  The front page of the JS TestNet app links to a form where an
administrator can add a test suite into the system.

You will have to make one modification to your test suite.  It must include
the jstestnet.js script (found in the adapter folder) to communicate with the
worker.  Be sure it loads after Qunit or whatever supported test runner you
are using.

::

  <html>
  <head>
    <title>Your QUnit Test Suite</title>
    <script type="text/javascript" src="/js/jquery.js"></script>
    <script type="text/javascript" src="/js/qunit/testrunner.js"></script>
    <script type="text/javascript" src="/js/jstestnet.js"></script>
  </head>
  <body>
  ...
  </body>
  </html>

This enables your test suite to send results back to JS TestNet via
`window.postMessage`_.

You will also need to be sure your web server is **not** sending a response
header like this::

  X-Frame-Options: DENY

.. _window.postMessage: https://developer.mozilla.org/en/dom/window.postmessage

Adding a Web Browser
====================

To register a web browser to run the tests (called a worker) just open the
browser and go to this URL and leave the window open::

  http://127.0.0.1:8000/work/

That's it!  No complicated start / stop commands are necessary.
The worker will be able to run tests for as long as you keep that window open
using Ajax polling to talk to the server.
In a CI environment you could just open this URL once in a virtual machine
and forget all about it.

In fact, you can open this URL on any web enabled device.  For example, you
could type this URL into your smart phone and
your phone would become a worker.

Running Tests
=============

To start your test suite on all web browsers, just request this URL from curl
or a custom script (more on that later)::

  http://127.0.0.1:8000/start_tests/foo

That will return a JSON response of who is working on your tests.  You can
check for results at::

  http://127.0.0.1:8000/job/{id}/result

Python Client
=============

Check out `JsTestNetLib`_! This makes all the HTTP requests necessary to start
tests and receive results from all browsers. It also implements a Nose (test
runner) plugin for convenience.

Server Protocol
===============

It's somewhat in flux at the moment so your best bet is to read the
`JsTestNetLib`_ source.

Credits
=======

This simple pub/sub model was inspired by jsTestDriver_, which is a great tool
for running very fast unit tests.  JS TestNet set out with a different goal:
run any kind of JavaScript tests, especially middle-tier integration tests
that do not lock down your implementation as much as unit tests.  You may want
to mock out jQuery's $.ajax method and perform asynchronous Ajax calls -- go
for it!

JS TestNet's worker implementation was forked from TestSwarm_, which is a
similar tool.  JS TestNet is different in that it supports direct execution of
tests suitable for CI.  Big thanks to John Resig for figuring out a lot of the
cross domain stuff and implementing retry timeouts, error handling, etc :)
Also, JS TestNet is dumber than TestSwarm in that it requires an adapter.

.. _jsTestDriver: http://code.google.com/p/js-test-driver/
.. _TestSwarm: https://github.com/jeresig/testswarm

Developers
==========

Hi!  Feel free to submit bugs, patches and pull requests on github_.
To run the test suite first install `tox`_ then run it from the project dir::

  $ cd jstestnet
  $ tox

.. _tox: http://codespeak.net/tox/
.. _github: https://github.com/kumar303/jstestnet

To-Do
=====

- Handle unexpected errors in the worker
- Add some kind of secure test execution to prevent DoS.  Probably a simple
  token based thing.

.. _`JsTestNetLib`: https://github.com/kumar303/jstestnetlib
