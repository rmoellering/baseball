
import logging
import threading

def get_logger(name, log_level='debug'):
    new_logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    #formatter = logging.Formatter('%(asctime)s || %(name)s || %(levelname)s || %(message)s')
    formatter = logging.Formatter('%(name)s || %(levelname)s || %(message)s')
    handler.setFormatter(formatter)
    new_logger.addHandler(handler)

    if log_level == 'debug':
        new_logger.setLevel(logging.DEBUG)
    elif log_level == 'info':
        new_logger.setLevel(logging.INFO)
    elif log_level == 'warn':
        new_logger.setLevel(logging.WARN)
    elif log_level == 'error':
        new_logger.setLevel(logging.ERROR)
    else:
        raise ValueError('Unrecognized log_level: {}'.format(log_level))

    return new_logger

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
