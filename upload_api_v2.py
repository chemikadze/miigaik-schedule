import logging
import os
import sys
import time


ROOT_PATH = os.path.dirname(__file__)
sys.path.append(ROOT_PATH)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gaenv'))

import settings
from sources import CURRENT_SOURCE
from rasp_vuzov_api import api_v2


def main():
    source = CURRENT_SOURCE()
    logging.info("Uploading version %s" % source.version)
    start = time.clock()
    data = api_v2.generate_data(source)
    api_v2.upload_data(data, settings.RASP_VUZOV_TOKEN, settings.RASP_VUZOV_ADMIN)
    logging.debug("Upload finished, took %s ms" % ((time.clock() - start) * 1000))
    print 'Uploaded version %s' % source.version


if __name__ == '__main__':
    try:
        logging.info("hello")
        main()
    except:
        logging.exception("Exception during update: ")
