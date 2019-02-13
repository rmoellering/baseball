
from datetime import datetime, timedelta
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

log = get_logger(__name__)

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

def get_human_time_diff(start, end):
    """
    calculate the difference between 2 time stamps
    show a maximum of 2 units of resolution,

    start: start time, format 2018-11-30 01:06:29
    end:   end time, must be >= start

    return: string, e.g. 1 week, 3 secs
    """

    # 2018-11-30 01:06:29
    start_time = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')

    diff = (end_time - start_time)

    units = (
        (timedelta(weeks=1), 'wk'),
        (timedelta(days=1), 'day'),
        (timedelta(hours=1), 'hr'),
        (timedelta(minutes=1), 'min'),
        (timedelta(seconds=1), 'sec')
    )

    duration = None
    for tpl in units:

        td = tpl[0]     # timedelta of current unit
        unit = tpl[1]

        cnt = 0
        # TODO: make this efficient
        while diff >= td:
            cnt += 1
            diff -= td

        if cnt:
            new_duration = '{} {}'.format(cnt, unit)
            if cnt > 1:
                new_duration += 's'

            if duration:
                return('{}, {}'.format(duration, new_duration))
            else:
                duration = new_duration

    return duration
