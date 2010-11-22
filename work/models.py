
from django.db import models

from system.models import TestSuite

class Worker(models.Model):
    user_agent = models.CharField(max_length=255)
    last_heartbeat = models.DateTimeField(null=True)
    is_alive = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

class Job(models.Model):
    test_suite = models.ForeignKey(TestSuite)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    finished = models.BooleanField(default=False)

class WorkQueue(models.Model):
    job = models.ForeignKey(Job)
    worker = models.ForeignKey(Worker)
    created = models.DateTimeField(auto_now_add=True)
    received = models.BooleanField(default=False)

class JobResult(models.Model):
    job = models.ForeignKey(Job)
    worker = models.ForeignKey(Worker)
    finished = models.BooleanField(default=False)
    retrieved = models.BooleanField(default=False)
    results = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
