
import json

from django import http
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext

from system.models import TestSuite
from system.forms import TestSuiteForm
from common.decorators import json_view
import work.views
from work.models import Worker, WorkQueue, Job, JobResult


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
def job_result(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    results = []
    for res in JobResult.objects.filter(job=job, finished=True):
        results.append({
            'worker_id': res.worker.id,
            'user_agent': res.worker.user_agent,
            'results': json.loads(res.results)
        })
    return {'finished': job.finished, 'results': results}


@json_view
@transaction.commit_on_success()
def start_tests(request, name):
    ts = get_object_or_404(TestSuite, slug=name)
    # TODO(kumar) don't start a test suite if it's already running.
    job = Job(test_suite=ts)
    job.save()
    workers = []
    for worker in Worker.objects.filter(is_alive=True):
        # TODO(kumar) add options to ignore workers for
        # unwanted browsers perhaps?
        WorkQueue(worker=worker, job=job).save()
        workers.append(worker)
    return {'job_id': job.id,
            'workers': [{'worker_id': w.id, 'user_agent': w.user_agent}
                         for w in workers]}


def status(request):
    work.views.collect_garbage()
    return render_to_response('system/index.html', dict(
                workers=Worker.objects.filter(is_alive=True),
                test_suites=TestSuite.objects.all().order_by('name')
            ),
            context_instance=RequestContext(request))
