import logging

from django.db import models

from common.stdlib import json
from jstestnet.system.models import TestSuite
from jstestnet.system.useragent import parse_useragent


log = logging.getLogger('jstestnet')


class Worker(models.Model):
    user_agent = models.CharField(max_length=255)
    last_heartbeat = models.DateTimeField(null=True)
    is_alive = models.BooleanField(default=True)
    ip_address = models.CharField(max_length=200, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def get_engine(self, name):
        for e in self.engines.all():
            if e.engine == name:
                return e
        raise LookupError(
                "Worker %r does not have an engine called %r" % (self,
                                                                 name))

    def parse_user_agent(self, user_agent):
        if self.user_agent:
            # Already parsed, nothing to do
            return
        self.user_agent = user_agent
        for engine, version in parse_useragent(user_agent):
            WorkerEngine.from_parsed_ua(self, engine, version)

    def restart(self):
        q = WorkQueue(
            worker=self,
            cmd='restart',
            description='Server said restart. Goodbye!',
            cmd_args=json.dumps([]),
        )
        q.save()

    def run_test(self, test):
        q = WorkQueue(
            worker=self,
            cmd='run_test',
            description='Running test suite.',
            cmd_args=json.dumps([{
                'test_run_id': test.id,
                'url': test.url,
                'name': test.test_suite.name
            }]),
        )
        q.save()
        tq = TestRunQueue(test_run=test, work_queue=q)
        tq.save()

    def start_debugging(self):
        q = WorkQueue(
            worker=self,
            cmd='start_debugging',
            description='Server wants to start the debugger',
            cmd_args=json.dumps([]),
        )
        q.save()

    @property
    def browser(self):
        engines = sorted(["%s/%s" % (e.engine, e.version)
                          for e in self.engines.all()])
        return ", ".join(engines)


class WorkerEngine(models.Model):
    worker = models.ForeignKey(Worker, related_name='engines')
    engine = models.CharField(max_length=50, db_index=True)
    version = models.CharField(max_length=10)

    @classmethod
    def from_parsed_ua(cls, worker, engine, version):
        if len(engine) > 50:
            log.info('Engine from user agent too long %r (truncated)' % engine)
            engine = engine[:50]
        if len(version) > 10:
            log.info('Version from user agent too long %r (truncated)' % version)
            version = version[:10]
        return cls.objects.create(worker=worker, engine=engine,
                                  version=version)


class TestRun(models.Model):
    test_suite = models.ForeignKey(TestSuite)
    url = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def is_finished(self):
        # TODO(Kumar) maybe do something here if a worker
        # has died while running the test (i.e. it will never finish)
        q = TestRunQueue.objects.filter(test_run=self,
                                        work_queue__finished=False)
        return q.count() == 0


class WorkQueue(models.Model):
    worker = models.ForeignKey(Worker)
    # The cmds should match those in media/js/system/work.js
    cmd = models.CharField(max_length=25,
                           choices=((f,f) for f in
                                    ['run_test','reload','change_rate']))
    cmd_args = models.TextField()
    description = models.CharField(max_length=255)
    work_received = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    results = models.TextField(null=True)
    results_received = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)


class TestRunQueue(models.Model):
    test_run = models.ForeignKey(TestRun)
    work_queue = models.ForeignKey(WorkQueue)
