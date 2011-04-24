import logging

import tornado
import tornadio
import tornadio.server

import settings_local as settings

log = logging.getLogger()


class Worker(tornadio.SocketConnection):
    connections = {}

    def on_open(self, request, *args, **kwargs):
        resource = kwargs['resource']
        self.worker_id = int(kwargs['extra'])
        self.connections[self.worker_id] = self
        if self.worker_id in Admin.connections:
            self.tell_admin()
        log.info('%s: %r joined' % (resource, self.worker_id))

    def on_message(self, message):
        Admin.connections[self.worker_id].send(message)

    def tell_admin(self):
        Admin.connections[self.worker_id].send({'action': 'worker_connected'})


class Admin(tornadio.SocketConnection):
    connections = {}

    def on_open(self, request, *args, **kwargs):
        resource = kwargs['resource']
        self.worker_id = int(kwargs['extra'])
        self.connections[self.worker_id] = self
        if self.worker_id in Worker.connections:
            Worker.connections[self.worker_id].tell_admin()
        log.info('%s: %r requested' % (resource, self.worker_id))

    def on_message(self, message):
        Worker.connections[self.worker_id].send(message)


protocols = ['xhr-polling']

WorkerRouter = tornadio.get_router(Worker,
                                   {'enabled_protocols': protocols},
                                   resource='worker',
                                   # worker ID
                                   extra_re=r'\d+',
                                   extra_sep='/')

AdminRouter = tornadio.get_router(Admin,
                                  {'enabled_protocols': protocols},
                                  resource='admin',
                                  # worker ID
                                  extra_re=r'\d+',
                                  extra_sep='/')


application = tornado.web.Application(
    [WorkerRouter.route(), AdminRouter.route()],
    socket_io_port = 8889)


if __name__ == '__main__':
    log.setLevel(logging.INFO)
    application.listen(8888)
    tornadio.server.SocketServer(application)
    # tornado.ioloop.IOLoop.instance().start()
