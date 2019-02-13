from django.conf import settings
import logging


def get_logger(name):
    new_logger = logging.getLogger()

    # # if we get accounting.utils we just want accounting for searching
    # name_head = name.split('.')[0]
    #
    # # do we have a logger defined for this?
    # if name_head in settings.LOGGING['loggers']:
    #     new_logger = logging.getLogger(name)
    #
    # # no?  then stick it to the root logger
    # else:
    # new_logger.warning(name + " logger requested.  No logger defined for: " + name_head)

    new_logger = logging.getLogger('root.' + name)
    handler = logging.StreamHandler()
    #formatter = logging.Formatter('%(asctime)s || %(name)s || %(levelname)s || %(message)s')
    formatter = logging.Formatter('%(name)s || %(levelname)s || %(message)s')
    handler.setFormatter(formatter)
    new_logger.addHandler(handler)

    if settings.LOG_LEVEL == 'debug':
        new_logger.setLevel(logging.DEBUG)
    elif settings.LOG_LEVEL == 'info':
        new_logger.setLevel(logging.INFO)
    elif settings.LOG_LEVEL == 'warn':
        new_logger.setLevel(logging.WARN)
    elif settings.LOG_LEVEL == 'error':
        new_logger.setLevel(logging.ERROR)
    else:
        raise ValueError('Unrecognized LOG_LEVEL: {}'.format(settings.LOG_LEVEL))

    return new_logger

class Results(object):
    def __init__(self):
        self.results = {}

    def increment(self, key, amount=1):
        if key in self.results:
            self.results[key] += amount
        else:
            self.results[key] = amount

    def report(self, show_total=False):
        total = 0
        for k, v in self.results.items():
            print ('{}: {}'.format(k, v))
            total += v
        if show_total:
            print('')
            print ('Total: {}'.format(total))
