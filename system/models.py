
from django.db import models

class TestSuite(models.Model):
    """URL to a QUnit test suite.

    e.g. http://some-server/qunit/all-tests.html
    """
    name = models.CharField(max_length=150)
    slug = models.CharField(max_length=100)
    url = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False,
                                   null=True)
    last_modified = models.DateTimeField(auto_now=True, editable=False,
                                         null=True)
