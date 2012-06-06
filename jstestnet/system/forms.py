
from django.forms import ModelForm

from jstestnet.system.models import TestSuite, Token

class TestSuiteForm(ModelForm):
    class Meta:
        model = TestSuite

    def __init__(self, data=None, instance=None, **kw):
        self.creating_test_suite = instance is None
        super(TestSuiteForm, self).__init__(data=data, instance=instance,
                                            **kw)

    def save(self, *args, **kw):
        ts = super(TestSuiteForm, self).save(*args, **kw)
        if self.creating_test_suite:
            Token.create(ts)
        return ts
