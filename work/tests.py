
from datetime import datetime
import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from nose.tools import eq_

from system.models import TestSuite
from work.models import Worker, Job, JobResult

class TestWork(TestCase):

    def test_start_work(self):
        r = self.client.get(reverse('work'))
        eq_(r.status_code, 200)
        assert r.context['worker_id']
        worker = Worker.objects.get(pk=r.context['worker_id'])
        eq_(worker.created.timetuple()[0:3],
            datetime.now().timetuple()[0:3])
        eq_(worker.last_heartbeat, None)

    def test_submit_results(self):
        worker = Worker()
        worker.save()
        ts = TestSuite(name='Zamboni', slug='zamboni',
                       url='http://server/qunit1.html')
        ts.save()
        job = Job(test_suite=ts)
        job.save()
        res = JobResult(job=job, worker=worker)
        res.save()
        results = {
            'failures': 0,
            'total': 1,
            'tests': [{'test':'foo','message':'1 equals 2'}]
        }
        r = self.client.post(reverse('work.submit_results'),
                             dict(job_result_id=res.id,
                                  results=json.dumps(results)))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['desc'], 'Test result received')

        res = JobResult.objects.get(job=job, worker=worker)
        eq_(res.finished, True)
        eq_(res.results, json.dumps(results))

    def test_submit_error_results(self):
        worker = Worker()
        worker.save()
        ts = TestSuite(name='Zamboni', slug='zamboni',
                       url='http://server/qunit1.html')
        ts.save()
        job = Job(test_suite=ts)
        job.save()
        res = JobResult(job=job, worker=worker)
        res.save()
        results = {
            'job_error': True,
            'job_error_msg': 'Timed out waiting for test results'
        }
        r = self.client.post(reverse('work.submit_results'),
                             dict(job_result_id=res.id,
                                  results=json.dumps(results)))
        eq_(r.status_code, 200)

        res = JobResult.objects.get(job=job, worker=worker)
        eq_(res.finished, True)
        eq_(res.results, json.dumps(results))

    def test_query(self):
        user_agent = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
                      'en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12')
        worker = Worker()
        worker.save()
        ts = TestSuite(name='Zamboni', slug='zamboni',
                       url='http://server/qunit1.html')
        ts.save()

        # No work to fetch.
        r = self.client.post(reverse('work.query'),
                             dict(worker_id=worker.id, user_agent=user_agent))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['desc'], 'No jobs to run.')

        # Simulate Hudson requesting a job:
        r = self.client.get(reverse('system.start_tests', args=[ts.slug]))
        eq_(r.status_code, 200)

        # Do work
        r = self.client.post(reverse('work.query'),
                             dict(worker_id=worker.id, user_agent=user_agent))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        if 'cmd' not in data:
            assert False, "Unexpected: %r" % data
        res = JobResult.objects.get(pk=data['args'][0]['job_result_id'])
        eq_(data['args'][0]['url'], ts.url)
        eq_(data['args'][0]['name'], ts.name)
        eq_(res.worker.id, worker.id)
        eq_(res.finished, False)
        eq_(data['cmd'], 'run_test')
        eq_(res.worker.last_heartbeat.timetuple()[0:3],
            datetime.now().timetuple()[0:3])
        eq_(res.worker.user_agent, user_agent)

        res.finished = True
        res.save()

        # Cannot fetch more work.
        r = self.client.post(reverse('work.query'),
                             dict(worker_id=worker.id, user_agent=user_agent))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['desc'], 'No jobs to run.')
