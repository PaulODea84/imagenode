"""imagenode: capture, transform and transfer images to imagehub

Enables Raspberry Pi computers to capture images with the PiCamera, perform
image transformations and send the images to a central imagehub for further
processing. Can send other sensor data such as temperature data and GPIO data.
Works on other types of (non Raspberry Pi) computers with webcams.

Typically run as a service or background process. See README.rst for details.

Copyright (c) 2017 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import os
import sys
import signal
import logging
import logging.handlers
import traceback
from tools.utils import clean_shutdown_when_killed
from tools.imaging import Settings, ImageNode

def main():
    # set up controlled shutdown when Kill Process or SIGTERM received
    signal.signal(signal.SIGTERM, clean_shutdown_when_killed)
    log = start_logging()
    try:
        log.info('Starting imagenode.py')
        settings = Settings()  # get settings for node cameras, ROIs, GPIO
        node = ImageNode(settings)  # start ZMQ, cameras and other sensors
        # forever event loop
        while True:
            # read cameras and run detectors until there is something to send
            while not node.send_q:
                node.read_cameras()
            while len(node.send_q) > 0:  # send frames until send_q is empty
                text, image = node.send_q.popleft()
                try:                
                    hub_reply = node.send_frame(text, image)
                except Exception as ex:  # traceback will appear in log
                    log.exception('Unanticipated error with no Exception handler.')
                    print(ex)                    
                node.process_hub_reply(hub_reply)
    except KeyboardInterrupt:
        log.warning('Ctrl-C was pressed.')
    except SystemExit:
        log.warning('SIGTERM was received.')
    except Exception as ex:  # traceback will appear in log
        log.exception('Unanticipated error with no Exception handler.')
        print(ex)
    finally:
        if 'node' in locals():
            node.closeall(settings) # close cameras, GPIO, files
        log.info('Exiting imagenode.py')

def start_logging():
    log = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler('imagenode.log',
        maxBytes=15000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s ~ %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    return log

if __name__ == '__main__' :
    main()
