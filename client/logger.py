import sys
"""
"BDI", "CNET", "BIDDING", "CONFLICT RESOLUTION", "NEXT_TO_AGENT", "RETREAT", "SAS", "MAP", "CAVES"
"""

log_filter=["RETREAT"]
def log(msg, tag = None, ignoreFilter = True):
    if tag is None:
        tag = 'log'
    if tag in log_filter or ignoreFilter:
        print('[{}] {}'.format(tag, msg), file=sys.stderr, flush=True)
