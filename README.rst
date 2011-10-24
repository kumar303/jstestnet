
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

First, you need Python_ 2.6 or greater. Clone this repository with the
recursive flag and you'll get all necessary requirements in the vendor
submodule::

  git clone --recursive git://github.com/kumar303/jstestnet.git

There are a few Python modules to compile after that so create a
virtualenv_ and run::

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

Now you'll have a development server running at ``http://localhost:8000``.

JS TestNet is based on Playdoh_ and Django_. You can find tons of docs at
both of those project sites.

.. _Python: http://python.org/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _Playdoh: http://playdoh.readthedocs.org/

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

Supported Test Runners
======================

The existing adapter currently supports these JavaScript test runners:

- `Qunit`_
- `doctest.js`_

.. _`doctest.js`: http://ianb.github.com/doctestjs/

It's pretty simple to add a new adapter. Check out ``adapter/jstestnet.js``
in the source.

Adding a Web Browser
====================

To register a web browser to run the tests (called a worker) just open the
browser and go to this URL and leave the window open::

  http://your-jstestnet-server/work/

That's it!  No complicated start / stop commands are necessary.
The worker will be able to run tests for as long as you keep that window open
using Ajax polling to talk to the server.
In a CI environment you could just open this URL once in a virtual machine
and forget all about it.

In fact, you can open this URL on any web enabled device.  For example, you
could type this URL into your smart phone and
your phone would become a worker.

Setting Up Your Firewall
========================

To understand the networking needed to use jstestnet, here is a diagram of a
typical configuration. The counterintuitive surprise here is that only the
TestWorker (the web browser) needs to connect to the web server that serves
your HTML test suite. JsTestNet does *not* need to load your test suite.

.. image:: http://kumar303.github.com/jstestnet/jstestnet-network.png

- **JsTestNet**

  - The server running the Django app. This responds to requests from clients
    and workers.

- **Jenkins**

  - Your continuous integration server.  This will typically execute tests
    that invoke a client that talks to JsTestNet.  In this configuration it
    *also* runs a web server that serves the HTML Qunit suite at
    ``http://<jenkins>:9878/qunit``

- **TestWorker**

  - This is a web browser that loads the worker page from JsTestNet *once*.
    After that it polls the server with Ajax and fetches the Qunit test suite
    in an iframe.


Client Protocol
===============

A client is the controller for running tests.  It communicates via HTTP with
the server to start tests in remote web browsers and fetch results.

**POST /start_tests/**

Request this URL to start tests in some browsers. POST parameters:

**browsers**
  A comma separated list of browser specs to run tests against. See the
  browser spec format documented below.
**name**
  The registered name of the test suite. This is what you set up in the
  administration site.
**token**
  A security token (obtained from the administration site) that authorizes
  the client to start tests.

The response is a JSON object with the following structure::

  {'error': true || false,
   'message': 'informative message',
   'test_run_id': <numeric ID of test run>}

**GET /test/<test_run_id>/result**

Request this URL to check on the status of the tests you started.
The response is a JSON object with the following structure::

  {'finished': true || false,  // true if all tests are finished running
   'results': [{'worker_user_agent': <user agent string>,
                'browser': <parsed browser spec>,  // e.g. firefox/3.6.12, gecko/1.9.2.12,
                'module': 'Name of test module',
                'test': 'Name of test',
                'result': true || false,  // true if the test passed
                'stacktrace: 'traceback to code',  // if supported
                'message': 'some assertion...'}, ...]

Client Implementations
======================

- `JsTestNetLib`_

  - Python client that makes all the HTTP requests necessary to start
    tests and receive results from all browsers. It also implements a Nose
    (test runner) plugin for convenience.

Browser specs
=============

A browser spec is how the client specifies which browsers should run the
tests. In its simplest form it looks like this::

  firefox,chrome

This spec will run tests in **both** Firefox and Chrome at whatever version is
available. To specify a specific browser version, use the equal-tilde
operator::

  firefox=~7

This will match any version of Firefox 7, such as 7.0 or 7.1.  You can limit
Firefox to the 7.1 branch by specifying::

  firefox=~7.1

To run tests on many browsers, just list as many as you need::

  firefox=~7,firefox=~8,chrome=~11,chrome=~12

Browser specs are parsed from the parts of a user agent string that are
separated by a forward slash. For example, consider the Firefox mobile user
agent::

  Mozilla/5.0 (X11; U; Linux armv61; en-US; rv:1.9.1b2pre) Gecko/20081015 Fennec/1.0a1

You could select this worker with a browser spec of ``fennec=~1.0``.

There is a special name-colon syntax to filter browsers. It looks like this::

  firefox:latest

This will return the latest version of Firefox after doing a basic
alphanumeric sort on the version string.

There are a few exceptions:

- To access mobile safari and not desktop safari
  you can say ``mobile-safari=~528.16``
- Because the Gecko version is oddly specified as ``rv`` there is an alias.
  For example, in a user string containing
  ``rv:1.9.2.13 ... Gecko/20101203``
  you would specify this version of Gecko as ``gecko=~1.9.2.13``.

Worker Protocol
===============

Browser workers communicate with the server via HTTP to fetch test requests
and submit test results.

**GET /work/**

Request this URL in a browser to load all the JavaScript necessary to
become a worker.  Once loaded, the page will poll the server continuously.

**POST /work/query**

Request this URL to see if there are any tests to run. POST parameters:

**worker_id**
  Numeric ID that was assigned to the worker upon the first GET.

**user_agent**
  Full user agent string of the browser.

The response is a JSON object with the following structure::

  {'cmd': 'command name',  // e.g. run_test
   'args': [{'work_queue_id': <numeric ID>,
             ...}], // arguments specific to the command
   'desc': 'Description of command'}

**POST /work/submit_results**

Request this URL to submit the results of a test run. POST parameters:

**work_queue_id**
  Numeric ID assigned to the unit of work.

**results**
  JSON result object with the following structure:

::

  {'failures': 0,
   'total': 1,  // total tests run
   'tests': [{'test': 'Name of test',
              'module': 'Name of test module',
              'result': true || false,  // true if the test passed
              'message': 'some assertion...'}]}

The response is a JSON object with the following structure::

  {'desc': 'Test result received'}

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
Once you've installed everything just run the tests like this::

  $ python manage.py test

.. _github: https://github.com/kumar303/jstestnet

To-Do
=====

- Handle unexpected errors in the worker better.
- Port polling Ajax in worker to something simpler like socket.io

.. _`JsTestNetLib`: https://github.com/kumar303/jstestnetlib
