#!/usr/bin/env python
# encoding: utf-8
"""
drift.py

pull in two prediciton files, compute the RMSE for each prediction, then print some details

run as drift.py file1 file2

"""

import sys
import getopt
import csv
import numpy as np

help_message = '''
The help message goes here.
'''


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    file1predicts = []
    drift = []
    with open(file1) as fh:
        filecsv = csv.reader(fh)
        for (rating,) in filecsv:
            file1predicts.append(rating)
    with open(file2) as fh:
        filecsv = csv.reader(fh)
        for idx, (rating,) in enumerate(filecsv):
            try:
                drift.append(((float(file1predicts[idx])-float(rating))**2)**0.5)
            except KeyError:
                print 'file one lacks the rating of ', track, 'by', user
    
    print 'max', max(drift)
    print 'min', min(drift)
    print 'mean', sum(drift)/float(len(drift))
    print 'changed', len(drift) - drift.count(0.0)
    
    
    

if __name__ == "__main__":
    sys.exit(main())
