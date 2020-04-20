import sys

log_filter = ["test"]

def log(msg, tag = None, ignoreFilter = True):
    if tag is None:
        tag = 'log'
    if tag in log_filter or ignoreFilter:
        print('[{}] {}'.format(tag, msg), file=sys.stderr, flush=True)