from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from django.http import JsonResponse

from utilities import *
import requests
import json
import datetime as dt
import time
import netCDF4 as nc
import numpy as np


def home(request):
    """
    Controller for the app home page.
    """
    model_input = SelectInput(display_text='',
                              name='model',
                              multiple=False,
                              options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf')],
                              initial=['Select Model'],
                              original=True)

    res = requests.get('https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetWatersheds/',
                       headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

    watershed_list_raw = json.loads(res.content)
    watershed_list = [value for value in watershed_list_raw if "Nepal" in value[0] or "Asia" in value[0]]
    watershed_list.append(['Select Watershed', ''])

    watershed_select = SelectInput(display_text='',
                                   name='watershed',
                                   options=watershed_list,
                                   initial=['Select Watershed'],
                                   original=True,
                                   attributes = {'onchange':"javascript:view_watershed();"
                                                }
                                   )

    context = {
        "model_input":model_input,
        "watershed_select":watershed_select
    }

    return render(request, 'hydroviewer_nepal/home.html', context)


def get_warning_points(request):
    get_data = request.GET
    try:
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']

        dates_res = requests.get(
            'https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetAvailableDates/?watershed_name=' + watershed +
            '&subbasin_name=' + subbasin, headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

        folder = eval(dates_res.content)[-1]

        res20 = requests.get(
            'https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetWarningPoints/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin + '&return_period=20&forecast_folder='+folder,
            headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

        res10 = requests.get(
            'https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetWarningPoints/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin + '&return_period=10&forecast_folder=' + folder,
            headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

        res2 = requests.get(
            'https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetWarningPoints/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin + '&return_period=2&forecast_folder=' + folder,
            headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

        # warning = {}
        # warning["20"] = res20.content
        # warning["10"] = res10.content
        # warning["2"]= res2.content
        # for lat in json.loads(res20.content)["warning_points"]:
        #     print lat
        return JsonResponse({
            "success": "Data analysis complete!",
            "warning20":json.loads(res20.content)["warning_points"],
            "warning10":json.loads(res10.content)["warning_points"],
            "warning2":json.loads(res2.content)["warning_points"]
        })
    except Exception as e:
        print str(e)
        return JsonResponse({'error': 'No data found for the selected reach.'})



def ecmwf_get_time_series(request):
    get_data = request.GET

    try:
        model = get_data['model']
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['comid']
        if get_data['startdate'] != '':
            startdate = get_data['startdate']
        else:
            startdate = 'most_recent'

        if model == 'ecmwf-rapid':
            res = requests.get('https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetWaterML/?watershed_name=' +
                               watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&start_folder=' +
                               startdate + '&stat_type=mean', headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

            res2 = requests.get(
                'https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid,
                headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

            res3 = requests.get(
                'https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetWaterML/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&start_folder=' +
                startdate + '&stat_type=outer_range_lower',
                headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

            res4 = requests.get(
                'https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetWaterML/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&start_folder=' +
                startdate + '&stat_type=outer_range_upper',
                headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

            res5 = requests.get(
                'https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetWaterML/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&start_folder=' +
                startdate + '&stat_type=std_dev_range_lower',
                headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

            res6 = requests.get(
                'https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetWaterML/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&start_folder=' +
                startdate + '&stat_type=std_dev_range_upper',
                headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

            ts_pairs = get_ts_pairs(res.content)
            ts_pairs2 = get_ts_pairs(res2.content)
            ts_pairs3 = get_ts_pairs_range(res3.content,res4.content)
            ts_pairs4 = get_ts_pairs_range(res5.content,res6.content)

            ts_pairs_data = {}
            ts_pairs_data['watershed'] = watershed
            ts_pairs_data['subbasin'] = subbasin
            ts_pairs_data['id'] = comid
            ts_pairs_data['ts_pairs'] = ts_pairs
            ts_pairs_data['ts_pairs2'] = ts_pairs2
            ts_pairs_data['ts_pairs3'] = ts_pairs3
            ts_pairs_data['ts_pairs4'] = ts_pairs4


            return JsonResponse({
                "success": "Data analysis complete!",
                "ts_pairs_data": json.dumps(ts_pairs_data)
            })

    except Exception as e:
        print str(e)
        return JsonResponse({'error': 'No data found for the selected reach.'})

def get_available_dates(request):
    get_data = request.GET

    watershed = get_data['watershed']
    subbasin = get_data['subbasin']
    comid = get_data['comid']
    res = requests.get('https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetAvailableDates/?watershed_name=' + watershed +
                       '&subbasin_name=' + subbasin, headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

    dates = []
    for date in eval(res.content):
        if len(date) == 10:
            date_mod = date + '000'
            date_f = dt.datetime.strptime(date_mod , '%Y%m%d.%H%M').strftime('%Y-%m-%d %H:%M')
        else:
            date_f = dt.datetime.strptime(date, '%Y%m%d.%H%M').strftime('%Y-%m-%d %H:%M')
        dates.append([date_f,date,watershed,subbasin,comid])

    dates.append(['Select Date', dates[-1][1]])
    dates.reverse()

    return JsonResponse({
        "success": "Data analysis complete!",
        "available_dates": json.dumps(dates)
    })


def get_return_periods(request):
    get_data = request.GET

    watershed = get_data['watershed']
    subbasin = get_data['subbasin']
    comid = get_data['comid']

    res = requests.get('https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetReturnPeriods/?watershed_name=' + watershed +
                       '&subbasin_name=' + subbasin + '&reach_id=' + comid,
                       headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

    return JsonResponse({
        "return_periods": eval(res.content)
    })