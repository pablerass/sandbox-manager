#!/usr/bin/env python3
"""
Launches a REST API service to manage the sandbox.

**Changelog**

* 02/03/2016 - Pablo - First script version.
"""
import json
import sys
import tornado.ioloop
import tornado.web
import tornado.wsgi

import sandbox_manager.proxy


LISTEN_PORT = 8888


# Handlers
class ApiHandler(tornado.web.RequestHandler):
    """Empty handler."""

    def get(self):
        """Generate an empty response."""
        pass


class SandboxHandler(tornado.web.RequestHandler):
    """Sandbox handler."""

    def get(self):
        """Generate response in JSON with all sandboxes."""
        json.dump(sandbox_manager.proxy.list_instances(), self)


HANDLERS = [
    (r"/", ApiHandler),
    (r"/sandboxes", SandboxHandler),
    # (r"/instance/(?P<sandbox>.*)", SandboxHandler)
]


def application():
    """Application."""
    return tornado.web.Application(HANDLERS)


def wsgi_application():
    """WSGI application."""
    return tornado.wsgi.WSGIApplication(HANDLERS)


def main(argv=None):
    """Main function."""
    app = application()
    app.listen(LISTEN_PORT)
    tornado.ioloop.IOLoop.current().start()


if (__name__ == "__main__"):
    sys.exit(main(sys.argv))
