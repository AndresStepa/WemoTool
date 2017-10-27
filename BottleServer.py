from threading import Thread

from bottle import ServerAdapter


class BottleServer(ServerAdapter):
    server = None
    bottleApp = None

    def __init__(self,bottleApp,sourceIp,sourcePort):
        super(BottleServer, self).__init__(host=sourceIp, port=sourcePort)
        self.bottleApp = bottleApp
        t = Thread(target=bottleApp.run, kwargs={'server': self, 'quiet': True})
        t.setDaemon(True)
        t.start()

    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        self.server = make_server(self.host, self.port, handler, **self.options)
        self.server.serve_forever()

    def stop(self):
        # self.server.server_close() <--- alternative but causes bad fd exception
        self.server.shutdown()