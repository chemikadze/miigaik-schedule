#!/usr/bin/env python

import logging
import os, sys

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext import db

ROOT_PATH = os.path.dirname(__file__)
sys.path.append(ROOT_PATH)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gaenv'))

from sources.gsql_datastore import *

GQL_MODELS = [GsqlGroupLesson,
              GsqlClassroomData,
              GsqlClassroomDescriptor,
              GsqlFacultyDescriptor,
              GsqlFreeClassroomsView,
              GsqlGroupData,
              GsqlGroupDescriptor,
              GsqlYearDescriptor,
              GsqlVersion]

def dropVersion(versionNum):
    for model in GQL_MODELS:
        while True:
            l = model.all().filter("version =", versionNum).fetch(100)
            if len(l):
                db.delete(l)
            else:
                break

def cleanupDatastore(logger):
    latest_versions = \
        GsqlVersion.all().filter('valid =', True).order('-version').fetch(5)
    latest_preserved = latest_versions[-1]
    logger("Five last versions are: %s" %
           map(lambda x: x.version, latest_versions))
    oldest = GsqlVersion.all().filter('valid =', True).order('version').get()
    logger("Oldest version is %s created at %s" %
           (oldest.version, oldest.create_time))
    if oldest.version < latest_preserved.version:
        logger("No need to store version %s" % oldest.version)
        logger("Removing old records...")
        dropVersion(oldest.version)
    else:
        logger("Have only five valid versions, no need to do cleanup.")


class MainHandler(webapp.RequestHandler):
    def get(self):
        self.post()

    def post(self):
        self.log("Starting cleanup...")
        cleanupDatastore(logger = self.log)
        self.log("Cleanup finished")

    def log(self, msg):
        logging.info(msg)
        self.response.out.write(msg + "<br/>")

def main():
    application = webapp.WSGIApplication([('/tasks/clean_oldest', MainHandler)],
        debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
