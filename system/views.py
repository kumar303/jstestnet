
import json

from django.db import transaction
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext

from common.decorators import json_view
from system.models import TestSuite
from work.models import Worker, WorkQueue, Job, JobResult


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
    return render_to_response('system/index.html', dict(
                workers=Worker.objects.filter(is_alive=True),
                test_suites=TestSuite.objects.all().order_by('name')
            ),
            context_instance=RequestContext(request))
