#!/usr/bin/env python
# encoding: utf-8
"""
munge_result.py

Created by Benjamin Fields on 2012-07-22.
Copyright (c) 2012 . All rights reserved.
"""

import sys
import getopt
import simplejson


help_message = '''
The help message goes here.
'''


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    with open(sys.argv[1]) as wh:
        good_res = simplejson.load(wh)
    with open(sys.argv[2]) as wh:
        fallback = wh.readlines()
    output = [None]*len(fallback)
    print 'fallback:', len(fallback)
    for thing in good_res:
        output[thing['order']] = thing['score']
    for idx in xrange(len(fallback)):
        if output[idx] == None:
            output[idx] = fallback[idx].strip()
    print 'output:',len(output)
    with open(sys.argv[3], 'w') as oh:
        oh.write('\n'.join([str(x) for x in output]))
        oh.write('\n')
        


if __name__ == "__main__":
    sys.exit(main())
