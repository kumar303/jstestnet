
from datetime import datetime, timedelta
import json

from django.db import transaction
from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext

from common.decorators import json_view
from work.models import Worker, WorkQueue, Job, JobResult


@json_view
@transaction.commit_on_success()
def query(request):
    worker = get_object_or_404(Worker, pk=request.POST.get('worker_id', 0))
    worker.last_heartbeat = datetime.now()
    worker.user_agent = request.POST['user_agent']
    worker.save()
    # Reap old workers:
    Worker.objects.filter(
            last_heartbeat__lt=datetime.now()-timedelta(minutes=5)).delete()
    # Clear out the work queue:
    WorkQueue.objects.filter(received=True).delete()
    # Delete old jobs:
    Job.objects.filter(created__lt=datetime.now()-timedelta(hours=2)).delete()
    # Look for work, FIFO:
    queue = (WorkQueue.objects
                      .filter(worker=worker, received=False)
                      .order_by('created'))
    if not queue.count():
        return {'desc': 'No jobs to run.'}
    # TODO(kumar) check for other messages to send the worker,
    # like force reloading, etc
    q = queue[0]
    q.received = True
    q.save()
    job = q.job
    res = JobResult(job=job, worker=worker)
    res.save()
    return {
        'cmd':'run_test',
        'desc': 'Here is a job to run.',
        'args': [{'job_result_id': res.id,
                  'url': job.test_suite.url,
                  'name': job.test_suite.name}]
    }


@json_view
def submit_results(request):
    res = get_object_or_404(JobResult,
                            pk=request.POST.get('job_result_id', 0))
    res.results = request.POST['results']
    res.finished = True
    res.save()
    return {
        'desc': 'Test result received'
    }


def work(request):
    worker = Worker()
    worker.save()
    return render_to_response('work/work.html',
            {'worker_id': worker.id},
            context_instance=RequestContext(request))
