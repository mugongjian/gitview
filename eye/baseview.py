# -*- coding: utf-8 -*-
from tornado.web import RequestHandler

class BaseView(RequestHandler):

    def mod_body(self):
        return ""

    def make(self):
        return self.render(
            "templates/base.html",
            body=self.mod_body())

