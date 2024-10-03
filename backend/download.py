import urllib.request
import logging
import urllib
import threading
from queue import Queue

logger = logging.getLogger(__name__)

import yt_dlp
import requests

from . import config

class DownloadThread(threading.Thread):
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue
        self.daemon = True
        self.filename = ''
        self.ydl_opts = {
            #'format': format_selector,
            'progress_hooks': [self.my_hook],
            'paths': {
                'temp': config.TEMP_DIR,
                'home': config.CACHE_DIR,
            },
            'outtmpl': '%(id)l.%(ext)s'
        }

    def my_hook(self, d):
        filename = d.get('tmpfilename', None)
        if filename is not None:
            self.filename = str(filename).split('\\')[-1]
        filename = d.get('filename', None)
        if filename is not None:
            self.filename = str(filename).split('\\')[-1]
            
    def run(self):
        while True:
            (dqueue, dtype, durl, dpath) = self.queue.get()
            logger.info(f"Downloading: {(dqueue, dtype, durl, dpath)}")
            try:
                if dtype == 0:
                    logger.info("Stopping")
                    return
                elif dtype == 1:
                    urllib.request.urlretrieve(durl, dpath)
                elif dtype == 2:
                    self.ydl_opts['outtmpl'] = dpath
                    ydl = yt_dlp.YoutubeDL(self.ydl_opts)
                    ydl.download([durl])
                else:
                    logger.error("Unkown dtype")
                dqueue.put(True)
            except:
                logger.exception(f"Failed to download: {durl}")
                dqueue.put(False)
            del dqueue

