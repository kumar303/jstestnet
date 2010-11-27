
from django.forms import ModelForm

from system.models import TestSuite

class TestSuiteForm(ModelForm):
    class Meta:
        model = TestSuite
