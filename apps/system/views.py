import json
import logging
import random
import traceback

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext
from django.views.decorators.csrf import csrf_view_exempt

from gevent import Greenlet
import jingo
from redis import Redis

from common.decorators import json_view, post_required
from common.stdlib import json
from system.models import TestSuite, Token
from system.forms import TestSuiteForm
from work.models import Worker, WorkQueue, TestRun, TestRunQueue
import work.views


log = logging.getLogger()


class InvalidToken(Exception):
    """An invalid or expired token sent to start_tests."""


@staff_member_required
def test_suites(request, test_suite_id=None, form=None):
    test_suites = TestSuite.objects.all().order_by('slug')
    test_suite = get_object_or_404(
                    TestSuite, pk=test_suite_id) if test_suite_id else None
    if not form:
        form = TestSuiteForm(instance=test_suite)

    data = dict(test_suites=test_suites, form=form, test_suite=test_suite)
    return jingo.render(request, 'system/admin/index.html', data)


@staff_member_required
def create_edit_test_suite(request, test_suite_id=None):
    test_suite = get_object_or_404(
                    TestSuite, pk=test_suite_id) if test_suite_id else None
    if request.POST:
        attr = request.POST.copy()
        form = TestSuiteForm(attr, instance=test_suite)
        if form.is_valid():
            form.save()
            return http.HttpResponseRedirect(reverse('system.test_suites'))
        else:
            return test_suites(form=form)
    else:
        return http.HttpResponseBadRequest()


@staff_member_required
def delete_test_suite(request, pk):
    ts = get_object_or_404(TestSuite, pk=pk)
    ts.delete()
    return http.HttpResponseRedirect(reverse('system.test_suites'))


@staff_member_required
def generate_token(request):
    ts = get_object_or_404(TestSuite, pk=request.POST['test_suite_id'])
    Token.create(ts)
    return http.HttpResponseRedirect(reverse('system.test_suites'))


@json_view
def test_result(request, test_run_id):
    test_run = get_object_or_404(TestRun, pk=test_run_id)
    # Group assertions by module/test
    tests = {}
    for tq in TestRunQueue.objects.filter(test_run=test_run,
                                          work_queue__finished=True):
        for test in json.loads(tq.work_queue.results)['tests']:
            k = (str(test['module']), str(test['test']))
            tests.setdefault(k, [])
            r = {
                'worker_id': tq.work_queue.worker.id,
                'worker_user_agent': tq.work_queue.worker.user_agent,
                'browser': tq.work_queue.worker.browser
            }
            r.update(test)
            tests[k].append(r)

    all_results = []
    for module, test in sorted(tests.keys()):
        all_results.append({
            'module': module,
            'test': test,
            'assertions': tests[(module, test)]
        })

    return {'finished': test_run.is_finished(), 'results': all_results}


class NoWorkers(Exception):
    """No workers are available for the request."""


def select_engine_workers(all_workers, name):
    engines = {}
    for worker in all_workers:
        engine = worker.get_engine(name)
        k = (name, engine.version)
        engines.setdefault(k, [])
        engines[k].append(worker)
    for version, pool in engines.items():
        # We only need on worker per engine/version.
        # TODO(Kumar) implement a better round-robin here, maybe one
        # that excludes busy workers:
        yield random.choice(pool)


def get_workers(qs, browser_spec):
    workers = []
    for spec in browser_spec.lower().split(','):
        spec = spec.strip()
        if '=~' in spec:
            name, version = spec.split('=~')
        else:
            name = spec
            version = '*'
        matches = []
        if version == '*':
            matches = list(qs.all().filter(engines__engine=name))
        else:
            matches = list(qs.all().filter(
                            engines__engine=name,
                            engines__version__istartswith=version))
        if len(matches) == 0:
            raise NoWorkers("No workers for %r are connected" % spec)
        # Make a pool of workers per identical engine/version
        # and only select one worker per version.
        for w in select_engine_workers(matches, name):
            workers.append(w)
    return workers


@json_view
@post_required
@transaction.commit_on_success()
@csrf_view_exempt
def start_tests(request):
    ts = get_object_or_404(TestSuite, slug=request.POST.get('name', None))
    url = request.POST.get('url') or ts.default_url
    token_is_valid = False
    if request.POST.get('token', None):
        if Token.is_valid(request.POST['token'], ts):
            token_is_valid = True
    if not token_is_valid:
        raise InvalidToken('Invalid or expired token sent to start_tests. '
                           'Contact an administrator.')

    work.views.collect_garbage()
    # TODO(kumar) don't start a test suite if it's already running.
    test = TestRun(test_suite=ts, url=url)
    test.save()
    workers = []
    qs = Worker.objects.filter(is_alive=True)
    browsers = request.POST.get('browsers', None)
    if not browsers:
        raise ValueError("No browsers were specified in GET request")
    for worker in get_workers(qs, browsers):
        # TODO(kumar) add options to ignore workers for
        # unwanted browsers perhaps?
        worker.run_test(test)
        workers.append(worker)
    return {'test_run_id': test.id,
            'workers': [{'worker_id': w.id, 'user_agent': w.user_agent}
                         for w in workers]}


@json_view
@transaction.commit_on_success()
def restart_workers(request):
    work.views.collect_garbage()
    count = 0
    for worker in Worker.objects.filter(is_alive=True):
        worker.restart()
        count += 1
    return {'workers_restarted': count}


def status(request):
    work.views.collect_garbage()

    data = dict(workers=(Worker.objects.filter(is_alive=True)
                         .exclude(last_heartbeat=None)),
                test_suites=TestSuite.objects.all().order_by('name'))
    return jingo.render(request, 'system/index.html', data)


@staff_member_required
def start_remote_debugger(request, worker_id):
    work.views.collect_garbage()
    worker = get_object_or_404(Worker, id=worker_id)
    worker.start_debugging()
    # TODO check is_alive?
    # Cannot be a POST since user might need to login first (login redirect)
    return http.HttpResponseRedirect(reverse('system.debug_in_worker',
                                     args=[worker_id]))


@staff_member_required
def debug_in_worker(request, worker_id):
    work.views.collect_garbage()
    worker = get_object_or_404(Worker, id=worker_id)
    # TODO check is_alive?
    return jingo.render(request, 'system/admin/debug_in_worker.html',
                        {'worker_id': worker_id})


def redis_client():
    return Redis(settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_DB,
                 socket_timeout=0.5)


def socketio(request):
    """socket.io communication layer currently used for debugging
    JavaScript remotely on a worker.
    """
    io = request.environ['socketio']
    redis_sub = redis_client().pubsub()

    def sender(io):
        while io.connected():
            redis_sub.subscribe('channel')  # TODO(Kumar) pass in worker ID
            for message in redis_sub.listen():
                if message['type'] == 'message':
                    msg = json.loads(message['data'])
                    print 'SENDING MESSAGE: %s' % msg
                    io.send(msg)

    greenlet = Greenlet.spawn(sender, io)

    # Listen to incoming messages from client.
    try:
        while io.connected():
            message = io.recv()
            if message:
                msg = message[0]
                print 'GOT MESSAGE: %s' % msg
                action = msg.get('action')
                if action == 'start_debug':
                    redis_client().publish('channel',
                                           json.dumps({'action': 'worker_connected',
                                                       'worker_id': msg['worker_id']}))
                elif action in ('eval', 'result'):
                    # pass these results through as is
                    redis_client().publish('channel', json.dumps(msg))
                else:
                    print 'Ignoring message: %s' % msg
    except Exception, exc:
        log.exception('RECEIVE EXCEPTION')
        raise

    # Disconnected...
    redis_client().publish('channel', 'disconnected')
    greenlet.throw(Greenlet.GreenletExit)

    return HttpResponse()
