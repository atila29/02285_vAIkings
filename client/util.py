import sys

def log(msg, tag = None):
    if tag is None:
        tag = 'debug'
    print('[{}] {}'.format(tag, msg), file=sys.stderr, flush=True)