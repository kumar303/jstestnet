
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from nose.tools import eq_, raises

from common.testutils import no_form_errors
from system.models import TestSuite
from system.views import get_workers, NoWorkers
from work.models import TestRun, TestRunQueue, WorkQueue, Worker
from common.stdlib import json


def create_ts():
    return TestSuite.objects.create(name='Zamboni', slug='zamboni',
                                    url='http://server/qunit1.html')


def create_worker(user_agent=None):
    if not user_agent:
        user_agent = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
                      'en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12')
    worker = Worker()
    worker.save()
    worker.parse_user_agent(user_agent)
    worker.save()
    return worker


class TestSystem(TestCase):

    def query(self, worker):
        r = self.client.post(reverse('work.query'),
                             dict(worker_id=worker.id,
                                  user_agent=worker.user_agent))
        eq_(r.status_code, 200)
        return json.loads(r.content)

    def test_status_page(self):
        r = self.client.get(reverse('system.status'))
        eq_(r.status_code, 200)

    def test_start_tests_with_no_workers(self):
        ts = create_ts()
        r = self.client.get(reverse('system.start_tests', args=['zamboni']),
                            data={'browsers': 'firefox'})
        eq_(r.status_code, 500)
        data = json.loads(r.content)
        eq_(data['error'], True)
        eq_(data['message'], "No workers for u'firefox' are connected")

    def test_start_specific_worker(self):
        ts = create_ts()
        fx_worker = create_worker(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; '
                               'rv:2.0b10) Gecko/20100101 Firefox/4.0b10')
        ch_worker = create_worker(
                    user_agent='Mozilla/5.0 (Windows; U; Windows NT 5.2; '
                               'en-US) AppleWebKit/534.17 (KHTML, like Gecko)'
                               ' Chrome/11.0.652.0 Safari/534.17')
        r = self.client.get(reverse('system.start_tests', args=['zamboni']),
                            data={'browsers': 'firefox=~*'})
        eq_(r.status_code, 200)
        data = json.loads(r.content)

        data = self.query(ch_worker)
        eq_(data, {u'desc': u'No commands from server.'})
        data = self.query(fx_worker)
        eq_(data['cmd'], 'run_test')

    def test_get_job_result(self):
        ts = create_ts()
        worker = create_worker()

        r = self.client.get(reverse('system.start_tests', args=['zamboni']),
                            data={'browsers': 'firefox'})
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        test_run_id = data['test_run_id']

        r = self.client.get(reverse('system.test_result', args=[test_run_id]))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['finished'], False)
        eq_(data['results'], [])

        data = self.query(worker)
        queue_id = data['work_queue_id']

        results = {
            'failures': 0,
            'total': 1,
            'tests': [
                {'module':'Bar', 'test':'foo',
                 'message':'1 equals 2', 'result':False},
                {'module':'Bar', 'test':'foo',
                 'message':'ok', 'result':True},
                {'module':'Zebo', 'test':'zee',
                 'message':'ok', 'result':True},
            ]
        }
        r = self.client.post(reverse('work.submit_results'),
                             dict(work_queue_id=queue_id,
                                  results=json.dumps(results)))
        eq_(r.status_code, 200)

        r = self.client.get(reverse('system.test_result', args=[test_run_id]))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['finished'], True)

        tests = sorted(data['results'])
        eq_(tests[0]['module'], 'Bar')
        eq_(tests[0]['test'], 'foo')
        eq_(tests[0]['assertions'], [
            {'module':'Bar', 'test':'foo', 'worker_id': worker.id,
             'worker_user_agent': worker.user_agent,
             'browser': 'firefox/3.6.12, gecko/1.9.2.12',
             'message':'1 equals 2', 'result':False},
            {'module':'Bar', 'test':'foo', 'worker_id': worker.id,
             'worker_user_agent': worker.user_agent,
             'browser': 'firefox/3.6.12, gecko/1.9.2.12',
             'message':'ok', 'result':True},
        ])
        eq_(tests[1]['module'], 'Zebo')
        eq_(tests[1]['test'], 'zee')
        eq_(tests[1]['assertions'], [
            {'module':'Zebo', 'test':'zee', 'worker_id': worker.id,
             'worker_user_agent': worker.user_agent,
             'browser': 'firefox/3.6.12, gecko/1.9.2.12',
             'message':'ok', 'result':True},
        ])

    def test_restart_workers(self):
        worker = Worker(user_agent='Mozilla/5.0 (Macintosh; U; etc...')
        worker.save()
        r = self.client.get(reverse('system.restart_workers'))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['workers_restarted'], 1)
        r = self.client.post(reverse('work.query'),
                             dict(worker_id=worker.id,
                                  user_agent=worker.user_agent))
        eq_(r.status_code, 200)
        data = json.loads(r.content)
        eq_(data['cmd'], 'restart')
        eq_(data['args'], [])
        eq_(data['desc'], 'Server said restart. Goodbye!')


class TestFilterByEngine(TestCase):

    def setUp(self):
        for ua in [
            # Firefox:
            ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; '
             'rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13'),
            ('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b7pre) '
             'Gecko/20100925 Firefox/4.0b7pre'),
            # Chrome:
            ('Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) '
             'AppleWebKit/534.17 (KHTML, like Gecko) Chrome/11.0.652.0 '
             'Safari/534.17'),
            # Two MSIE browsers with identical versions:
            'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US)',
            'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US)']:
            create_worker(ua)

    def filter(self, spec=None):
        engines = []
        for worker in get_workers(Worker.objects.all(), spec):
            for e in worker.engines.all():
                engines.append((e.engine, e.version))
        return sorted(engines)

    def test_firefox_version(self):
        eq_(self.filter('firefox=~3.6'),
            [(u'firefox', u'3.6.13'), (u'gecko', u'1.9.2.13')])
        eq_(self.filter('firefox=~3'),
            [(u'firefox', u'3.6.13'), (u'gecko', u'1.9.2.13')])

    def test_firefox_all(self):
        eq_(self.filter('firefox'),
            [(u'firefox', u'3.6.13'), (u'firefox', u'4.0b7pre'),
             (u'gecko', u'1.9.2.13'), (u'gecko', u'2.0b7pre')])
        eq_(self.filter('firefox=~*'),
            [(u'firefox', u'3.6.13'), (u'firefox', u'4.0b7pre'),
             (u'gecko', u'1.9.2.13'), (u'gecko', u'2.0b7pre')])
        eq_(self.filter('firefox=~3,firefox=~4'),
            [(u'firefox', u'3.6.13'), (u'firefox', u'4.0b7pre'),
             (u'gecko', u'1.9.2.13'), (u'gecko', u'2.0b7pre')])

    @raises(NoWorkers)
    def test_firefox_none(self):
        self.filter('firefox=~1.5')

    def test_chrome_and_firefox_happy_together(self):
        eq_(self.filter('chrome,firefox'),
            [(u'applewebkit', u'534.17'), (u'chrome', u'11.0.652.0'),
             (u'firefox', u'3.6.13'), (u'firefox', u'4.0b7pre'),
             (u'gecko', u'1.9.2.13'), (u'gecko', u'2.0b7pre'),
             (u'safari', u'534.17')])
        eq_(self.filter('firefox=~4.0,chrome'),
            [(u'applewebkit', u'534.17'), (u'chrome', u'11.0.652.0'),
             (u'firefox', u'4.0b7pre'), (u'gecko', u'2.0b7pre'),
             (u'safari', u'534.17')])

    def test_one_msie_worker(self):
        eq_(self.filter('msie=~9'),
            [(u'msie', u'9.0')])


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
