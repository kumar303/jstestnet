
from datetime import datetime
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from nose.tools import eq_

from common.testutils import no_form_errors
from system.models import TestSuite
from work.models import Job, JobResult, Worker

class TestSystem(TestCase):

    def test_status_page(self):
        r = self.client.get(reverse('system.status'))
        eq_(r.status_code, 200)

    def test_start_tests(self):
        TestSuite(name='Zamboni', slug='zamboni',
                  url='http://server/qunit1.html').save()
        r = self.client.get(reverse('system.start_tests', args=['zamboni']))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        q = Job.objects.all()
        eq_(q.count(), 1)
        job = q[0]
        eq_(job.test_suite.slug, 'zamboni')
        eq_(job.created.timetuple()[0:3], datetime.now().timetuple()[0:3])
        eq_(job.finished, False)
        eq_(data['job_id'], job.id)

    def test_get_job_result(self):
        ts = TestSuite(name='Zamboni', slug='zamboni',
                       url='http://server/qunit1.html')
        ts.save()
        job = Job(test_suite=ts)
        job.save()
        r = self.client.get(reverse('system.job_result', args=[job.id]))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['finished'], False)
        eq_(data['results'], [])

        job.finished = True
        job.save()
        worker = Worker(user_agent='Mozilla/5.0 (Macintosh; U; etc...')
        worker.save()
        results = {
            'failures': 0,
            'total': 1,
            'tests': [{'test':'foo','message':'1 equals 2'}]
        }
        JobResult(job=job, worker=worker, finished=True,
                  results=json.dumps(results)).save()

        r = self.client.get(reverse('system.job_result', args=[job.id]))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['finished'], True)
        eq_(data['results'], [{
            'worker_id': worker.id,
            'user_agent': worker.user_agent,
            'results': results
        }])


class TestSystemAdmin(TestCase):

    def setUp(self):
        a = User(username='admin', is_staff=True)
        a.set_password('test')
        a.save()
        assert self.client.login(username='admin', password='test')

    def test_login_required(self):
        self.client.logout()

        def is_login_page(r):
            eq_(r.status_code, 200)
            assert 'Log in | Django site admin' in r.content, (
                                                    'Expected login form')

        r = self.client.get(reverse('system.test_suites'))
        is_login_page(r)
        r = self.client.get(reverse('system.create_edit_test_suite'))
        is_login_page(r)

    def test_create_test_suite(self):
        r = self.client.get(reverse('system.test_suites'))
        eq_(r.status_code, 200)
        assert 'form' in r.context[0]
        r = self.client.post(reverse('system.create_edit_test_suite'), {
            'name': 'Zamboni',
            'slug': 'zamboni',
            'url': 'http://127.0.0.1:8001/qunit/'
        })
        no_form_errors(r)
        self.assertRedirects(r, reverse('system.test_suites'))
        ts = TestSuite.objects.get(slug='zamboni')
        eq_(ts.name, 'Zamboni')
        eq_(ts.url, 'http://127.0.0.1:8001/qunit/')
        eq_(ts.created.timetuple()[0:3],
            datetime.now().timetuple()[0:3])
        eq_(ts.last_modified.timetuple()[0:3],
            datetime.now().timetuple()[0:3])

    def test_edit_test_suite(self):
        ts = TestSuite(name='Zamboni', slug='zamboni',
                       url='http://127.0.0.1:8001/qunit/')
        ts.save()
        orig_ts = ts
        r = self.client.post(reverse('system.create_edit_test_suite',
                                     args=[ts.id]), {
            'name': 'Zamboni2',
            'slug': 'zamboni2',
            'url': 'http://127.0.0.1:8001/qunit2/'
        })
        no_form_errors(r)
        self.assertRedirects(r, reverse('system.test_suites'))
        ts = TestSuite.objects.get(pk=orig_ts.id)
        eq_(ts.name, 'Zamboni2')
        eq_(ts.slug, 'zamboni2')
        eq_(ts.url, 'http://127.0.0.1:8001/qunit2/')
        eq_(ts.created.timetuple()[0:5],
            orig_ts.created.timetuple()[0:5])
        assert ts.last_modified != orig_ts.last_modified

    def test_delete_test_suite(self):
        ts = TestSuite(name='Zamboni', slug='zamboni',
                       url='http://127.0.0.1:8001/qunit/')
        ts.save()
        r = self.client.get(reverse('system.delete_test_suite',
                                     args=[ts.id]))
        self.assertRedirects(r, reverse('system.test_suites'))
        eq_(TestSuite.objects.filter(slug='zamboni').count(), 0)
