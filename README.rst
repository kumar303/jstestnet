
==========
JS TestNet
==========

JS TestNet is a Django_ web service that coordinates the execution of JavaScript tests across web browsers.  It was designed to run pure JavaScript tests with Qunit_ in a CI environment like Hudson_ and to get test feedback from real web browsers.  It is probably flexible enough for other JavaScript test runners too.

.. _Django: http://www.djangoproject.com/
.. _Qunit: http://docs.jquery.com/Qunit
.. _Hudson: http://hudson-ci.org/

.. contents::
      :local:

Install
=======

First, you need Python_ 2.6 or greater.  Clone this repository, create a virtualenv_, install pip_, then cd into the project and run::

  pip install -r requirements.txt

Make your own settings_local.py::

  cp settings_local.py-example settings_local.py

Set up a MySQL User and enter the credentials in settings_local.py::

  DATABASES['default']['NAME'] = 'jstestnet_dev'
  DATABASES['default']['USER'] = 'jstestnet_dev'
  DATABASES['default']['PASSWORD'] = 'test'

Create the database::

  ./manage.py syncdb

Start the server and open the front page to see the system status.

::

  ./manage.py runserver

.. _Python: http://python.org/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
.. _pip: http://pip.openplans.org/

Adding a Test Suite
===================

A test suite is a URL to an HTML page that runs tests in a web browser when loaded.  Make it accessible to JS TestNet like this in a mysql shell::

  insert into system_testsuite
    (name, slug, url)
    values
    ('Foo Test Suite','foo','http://my-dev-server/qunit/all.html');

You will have to make one modification to your test suite.  It must include the jstestnet.js script, found in the adapter folder.  Be sure it loads after Qunit or whatever supported test runner you are using.

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

This is important because it enables your test suite to send results back to JS TestNet via `window.postMessage`_.

You will also need to be sure your web server is **not** sending a response header like this::

  X-Frame-Options: DENY

.. _window.postMessage: https://developer.mozilla.org/en/dom/window.postmessage

Adding a Web Browser
====================

To register a web browser to run the tests (called a worker) just open the browser and go to this URL and leave the window open::

  http://127.0.0.1:8000/work/

The worker will be able to run tests for as long as you keep that window open.  In a CI environment you probably want to open this once in a virtual machine and forget all about it.

You can open this URL on any web enabled device and it will automatically join the work pool.  For example, you could type this URL into your smart phone and your phone would become a worker.

Running Tests
=============

To start your test suite on all web browsers, just request this URL from curl or a custom script (more on that later)::

  http://127.0.0.1:8000/start_tests/foo

That will return a JSON response of who is working on your tests.

Credits
=======

This simple pub/sub model was inspired by jsTestDriver_, which is a great tool for running very fast unit tests.  JS TestNet set out with a different goal: run any kind of JavaScript tests, especially middle-tier integration tests that do not lock down your implementation as much as unit tests.  You may want to mock out jQuery's $.ajax method and perform asynchronous Ajax calls -- go for it!

JS TestNet's client side implementation was forked from TestSwarm_ which is also a similar tool.  JS TestNet is different in that it supports direct execution of tests suitable for CI.  Big thanks to John Resig for figuring out a lot of the cross domain stuff and retry timeouts, etc :)

.. _jsTestDriver: http://code.google.com/p/js-test-driver/
.. _TestSwarm: https://github.com/jeresig/testswarm

Developers
==========

Hi!  Feel free to submit bugs, patches and pull requests on github_.  Here is the command to run the test suite::

  ./manage.py test

.. _github: https://github.com/kumar303/jstestnet
