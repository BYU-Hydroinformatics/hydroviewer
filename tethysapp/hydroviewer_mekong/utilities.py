import requests
import json
import datetime as dt
import time
from itertools import izip

def get_ts_pairs(content):

    data = content.split('dateTimeUTC="')
    data.pop(0)

    ts_pairs = []
    for elem in data:
        date = time.mktime(
            dt.datetime.strptime(elem.split('"  methodCode="1"  sourceCode="1"  qualityControlLevelCode="1" >')[0],
                                 '%Y-%m-%dT%H:%M:%S').timetuple())
        value = float(
            elem.split('  methodCode="1"  sourceCode="1"  qualityControlLevelCode="1" >')[1].split('</value>')[0])

        ts_pairs.append([date * 1e3, value])

    return ts_pairs

def get_ts_pairs_range(content,content2):

    data = content.split('dateTimeUTC="')
    data.pop(0)

    data2 = content2.split('dateTimeUTC="')
    data2.pop(0)

    ts_pairs_range = []
    for elem,elem2 in izip(data,data2):
        date = time.mktime(
            dt.datetime.strptime(elem.split('"  methodCode="1"  sourceCode="1"  qualityControlLevelCode="1" >')[0],
                                 '%Y-%m-%dT%H:%M:%S').timetuple())
        lower_value = float(
            elem.split('  methodCode="1"  sourceCode="1"  qualityControlLevelCode="1" >')[1].split('</value>')[0])

        upper_value = float(
            elem2.split('  methodCode="1"  sourceCode="1"  qualityControlLevelCode="1" >')[1].split('</value>')[0])

        ts_pairs_range.append([date * 1e3, lower_value,upper_value])

    return ts_pairs_range