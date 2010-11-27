
from django import forms as djangoforms

from nose.tools import eq_

def no_form_errors(response):
    if response.context is None:
        return
    # if all went well the request probably redirected, 
    # otherwise, there will be form objects with errors:
    forms = []
    for ctx in response.context:
        for cdict in ctx:
            for v in cdict.values():
                if isinstance(v, djangoforms.BaseForm):
                    forms.append(v)
    for form in forms:
        eq_(form.errors.as_text(), "")
