#!/usr/bin/python

import sys
import math
import yaml

def conv_recur(d):
    ret = {}
    for key, val in d.iteritems():
        if key == 'indices':
            ret['joints'] = val
        elif key == 'values':
            ret['q'] = [q*math.pi/180 for q in val]
        elif key == 'name':
            if val is None:
                val = ''
            ret[key] = val
        elif type(val) == dict:
            ret[key] = conv_recur(val)
        elif type(val) == list:
            ret[key] = [conv_recur(v) for v in val]
        else:
            ret[key] = val
    return ret

d = yaml.load(open(sys.argv[1]))
nd = conv_recur(d)
print yaml.dump(nd, indent = 3, width=10000).replace('-  ', ' - ')
