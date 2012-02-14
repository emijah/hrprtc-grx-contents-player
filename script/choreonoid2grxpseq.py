#!/usr/bin/python

import sys
import math
import yaml

def conv_recur(d):
    ret = {}
    for key, val in d.iteritems():
        if key == 'refs':
            for i in range(0, len(val)-1):
                val[i]['refer']['transition-time'] = val[i+1]['time'] - val[i]['time']
            val[-1]['refer']['transition-time'] = 2.0
        if key == 'joints':
            ret['indices'] = val
        elif key == 'q':
            ret['values'] = [q*180/math.pi for q in val]
        elif key in ('ikLinks'):
            pass
        elif key in ('translation', 'rotation'):
            ret[key] = val
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
print yaml.dump(nd, indent = 3, width=10000).replace('-  ', ' - ').replace('      ', '     ')
