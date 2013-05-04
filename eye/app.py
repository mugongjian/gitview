# -*- coding: utf-8 -*-
from tornado import web
from tornado import ioloop
import views

def main():
    urls = (
        (r"/commit", views.Commit),
        (r"/merge", views.Merge),
        (r"/(?P<pk>\d+)/", views.ProjectView),
        (r"/branch/(?P<pk>\d+)/edit", views.Edit),
        (r"/", views.HomeView),
        )
    web.Application(
        urls,
        debug=True,
        autoescape=None,
        static_path="/home/jpg/Code/gitview/eye/static").listen(8002)
    ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
