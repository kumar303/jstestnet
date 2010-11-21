
from datetime import datetime, timedelta
import json

from django.shortcuts import render_to_response, get_object_or_404
from django.template import loader, RequestContext

from common.decorators import json_view
from work.models import Worker, Job, JobResult


@json_view
def query(request):
    worker = get_object_or_404(Worker, pk=request.POST.get('worker_id', 0))
    worker.last_heartbeat = datetime.now()
    worker.user_agent = request.POST['user_agent']
    worker.save()
    # Reap old workers:
    Worker.objects.filter(
            last_heartbeat__lt=datetime.now()-timedelta(minutes=5)).delete()
    # Delete old jobs:
    Job.objects.filter(created__lt=datetime.now()-timedelta(hours=2)).delete()
    recent = Job.objects.filter(finished=False).order_by('-created')
    if not recent.count():
        return {'desc': 'No jobs to run.'}
    job = recent[0]
    if JobResult.objects.filter(job=job, finished=False,
                                worker__user_agent=worker.user_agent).count():
        return {'desc': 'Job already running for this type of web browser.'}
    if JobResult.objects.filter(job=job, finished=True,
                                worker__user_agent=worker.user_agent).count():
        # This job per user agent is finished, others are in progress
        return {'desc': 'No jobs to run.'}
    res = JobResult(job=job, worker=worker)
    res.save()
    # TODO(kumar) check for other messages to send the worker,
    # like force reloading, etc
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
