import sys

def log(msg, tag = None):
    if tag is None:
        tag = 'log'
    print('[{}] {}'.format(tag, msg), file=sys.stderr, flush=True)