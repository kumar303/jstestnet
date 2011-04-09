import random

from django import http
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext

from common.stdlib import json
from system.models import TestSuite, Token
from system.forms import TestSuiteForm
from common.decorators import json_view, post_required
import work.views
from work.models import Worker, WorkQueue, TestRun, TestRunQueue


class InvalidToken(Exception):
    """An invalid or expired token sent to start_tests."""


@staff_member_required
def test_suites(request, test_suite_id=None, form=None):
    test_suites = TestSuite.objects.all().order_by('slug')
    test_suite = get_object_or_404(
                    TestSuite, pk=test_suite_id) if test_suite_id else None
    if not form:
        form = TestSuiteForm(instance=test_suite)
    return render_to_response('system/admin.html', dict(
                test_suites=test_suites,
                form=form,
                test_suite=test_suite
            ),
            context_instance=RequestContext(request))


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
def start_tests(request):
    ts = get_object_or_404(TestSuite, slug=request.POST.get('name', None))
    token_is_valid = False
    if request.POST.get('token', None):
        if Token.is_valid(request.POST['token'], ts):
            token_is_valid = True
    if not token_is_valid:
        raise InvalidToken('Invalid or expired token sent to start_tests. '
                           'Contact an administrator.')

    work.views.collect_garbage()
    # TODO(kumar) don't start a test suite if it's already running.
    test = TestRun(test_suite=ts)
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
    return render_to_response('system/index.html', dict(
                workers=(Worker.objects.filter(is_alive=True)
                         .exclude(last_heartbeat=None)),
                test_suites=TestSuite.objects.all().order_by('name')
            ),
            context_instance=RequestContext(request))
