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
    app = web.Application(urls, **config.APP)
    app.listen(config.APP_PORT)
    ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
