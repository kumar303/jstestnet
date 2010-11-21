
from datetime import datetime
import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from nose.tools import eq_

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
