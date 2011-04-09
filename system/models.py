
import uuid

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

class Token(models.Model):
    token = models.TextField()
    test_suite = models.ForeignKey(TestSuite)
    active = models.BooleanField(default=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True, editable=False,
                                   null=True)
    last_modified = models.DateTimeField(auto_now=True, editable=False,
                                         null=True)

    @classmethod
    def is_valid(cls, token, test_suite):
        return cls.objects.filter(token=token, test_suite=test_suite,
                                  active=True).count()

    @classmethod
    def create(cls, test_suite):
        t = cls.objects.create(token=uuid.uuid4(), test_suite=test_suite,
                               active=True)
        return t.token
