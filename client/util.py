import sys
"""
"BDI", "CNET", "BIDDING", "CONFLICT RESOLUTION", "NEXT_TO_AGENT", "RETREAT"
"""

log_filter=["BIDDING", "CNET", "BDI", "RETREAT", "SAS"]
def log(msg, tag = None, ignoreFilter = True):
    if tag is None:
        tag = 'log'
    if tag in log_filter or ignoreFilter:
        print('[{}] {}'.format(tag, msg), file=sys.stderr, flush=True)