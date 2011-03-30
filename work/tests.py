
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.test import TestCase
from nose.tools import eq_, raises

from system.models import TestSuite
from work.models import Worker, WorkerEngine, TestRun, WorkQueue
from work.views import collect_garbage
from common.stdlib import json
from system.useragent import parse_useragent

class TestWork(TestCase):

    def test_start_work(self):
        r = self.client.get(reverse('work'))
        eq_(r.status_code, 200)
        assert r.context['worker_id']
        worker = Worker.objects.get(pk=r.context['worker_id'])
        eq_(worker.created.timetuple()[0:3],
            datetime.now().timetuple()[0:3])
        eq_(worker.last_heartbeat, None)

    def test_work(self):
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
        eq_(data['desc'], 'No commands from server.')

        # Simulate Hudson requesting a job:
        r = self.client.get(reverse('system.start_tests', args=[ts.slug]),
                            data={'browsers': 'firefox'})
        eq_(r.status_code, 200)

        # Do work
        r = self.client.post(reverse('work.query'),
                             dict(worker_id=worker.id, user_agent=user_agent))
        eq_(r.status_code, 200)
        data = json.loads(r.content)

        eq_(data['cmd'], 'run_test')
        eq_(data['args'][0]['url'], ts.url)
        eq_(data['args'][0]['name'], ts.name)
        work_queue_id = data['args'][0]['work_queue_id']

        queue = WorkQueue.objects.get(pk=work_queue_id)
        eq_(queue.worker.id, worker.id)
        eq_(queue.finished, False)
        eq_(queue.results, None)
        eq_(queue.results_received, False)
        eq_(queue.worker.last_heartbeat.timetuple()[0:3],
            datetime.now().timetuple()[0:3])
        eq_(queue.worker.user_agent, user_agent)
        eq_(sorted([(e.engine, e.version) for e in
                    queue.worker.engines.all()]),
            sorted(parse_useragent(user_agent)))

        results = {
            'failures': 0,
            'total': 1,
            'tests': [{'test': 'foo',
                       'message': '1 equals 2',
                       'module': 'some module',
                       'result': True}]
        }
        r = self.client.post(reverse('work.submit_results'),
                             dict(work_queue_id=queue.id,
                                  results=json.dumps(results)))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['desc'], 'Test result received')

        # Refresh from db...
        queue = WorkQueue.objects.get(pk=queue.id)
        eq_(queue.finished, True)
        eq_(queue.results, json.dumps(results))
        eq_(queue.results_received, False)

        # Cannot fetch more work.
        r = self.client.post(reverse('work.query'),
                             dict(worker_id=worker.id, user_agent=user_agent))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['desc'], 'No commands from server.')

    def test_garbage_collection(self):
        w = Worker.objects.create()
        w.parse_user_agent('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
                           'en-US; rv:1.9.2.12) Gecko/20101026 '
                           'Firefox/3.6.12')
        w.last_heartbeat = datetime.now() - timedelta(seconds=31)
        w.save()
        w.restart()
        collect_garbage()
        eq_([o.id for o in Worker.objects.all()], [])
        eq_([o.engine for o in WorkerEngine.objects.all()], [])
        eq_([o.id for o in WorkQueue.objects.all()], [])

    def test_zombie_worker_gets_told_to_restart(self):
        user_agent = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
                      'en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12')
        # post an unknown worker ID
        r = self.client.post(reverse('work.query'),
                             dict(worker_id=666, user_agent=user_agent))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['cmd'], 'restart')

    def test_invalid_input_gets_told_to_restart(self):
        user_agent = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
                      'en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12')
        r = self.client.post(reverse('work.query'),
                             dict(worker_id='some kind of garbage',
                                  user_agent=user_agent))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['cmd'], 'restart')


class TestWorkResults(TestCase):

    def setUp(self):
        user_agent = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
                      'en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12')
        worker = Worker.objects.create()
        worker.parse_user_agent(user_agent)
        worker.save()
        ts = TestSuite(name='Zamboni', slug='zamboni',
                       url='http://server/qunit1.html')
        ts.save()
        r = self.client.get(reverse('system.start_tests', args=['zamboni']),
                            data={'browsers': 'firefox'})
        eq_(r.status_code, 200)
        r = self.client.post(reverse('work.query'),
                             dict(worker_id=worker.id, user_agent=user_agent))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        self.work_queue_id = data['work_queue_id']

    def test_submit_error_results(self):
        results = {
            'test_run_error': True,
            'test_run_error_msg': 'Timed out waiting for test results'
        }
        r = self.client.post(reverse('work.submit_results'),
                             dict(work_queue_id=self.work_queue_id,
                                  results=json.dumps(results)))
        eq_(r.status_code, 200)

        q = WorkQueue.objects.get(pk=self.work_queue_id)
        eq_(q.finished, True)
        d = json.loads(q.results)
        eq_(d['tests'][0], {'module': '__jstestnet__',
                            'test': 'test_run_error',
                            'result': False,
                            'message': results['test_run_error_msg']})

    def test_submit_incomplete_results(self):
        results = {
            'failures': 0,
            'total': 1,
            # mostly empty test result:
            'tests': [{'result': True}]
        }
        r = self.client.post(reverse('work.submit_results'),
                             dict(work_queue_id=self.work_queue_id,
                                  results=json.dumps(results)))
        eq_(r.status_code, 200)

        q = WorkQueue.objects.get(pk=self.work_queue_id)
        eq_(q.finished, True)
        eq_(json.loads(q.results)['tests'],
            [{'result': True,
              'module': "<'module' was empty>",
              'test': "<'test' was empty>",
              'message': "<'message' was empty>"}])

    def test_missing_results(self):
        results = {
            'failures': 0,
            'total': 1,
            # totally empty
            'tests': [{}]
        }
        r = self.client.post(reverse('work.submit_results'),
                             dict(work_queue_id=self.work_queue_id,
                                  results=json.dumps(results)))
        eq_(r.status_code, 500)
        d = json.loads(r.content)
        eq_(d['error'], True)
        assert 'missing key result' in d['message'], (
                                            'Unexpected: %s' % d['message'])
