from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from django.http import JsonResponse

import plotly.graph_objs as go
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

def get_historic_data(request):
    get_data = request.GET
    print "i got called"
    watershed = get_data['watershed']
    subbasin = get_data['subbasin']
    comid = get_data['comid']

    res = requests.get('https://tethys.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/?watershed_name=' + watershed +
                       '&subbasin_name=' + subbasin + '&reach_id=' + comid,
                       headers={'Authorization': 'Token 72b145121add58bcc5843044d9f1006d9140b84b'})

    return JsonResponse({
        "return_periods": eval(res.content)
    })

def get_ecmwf_hydrograph_plot(request):
    """
    Retrieves 52 ECMWF ensembles analysis with min., max., avg., std. dev.
    as a plotly hydrograph plot.
    """
    # retrieve statistics
    forecast_statistics, watershed_name, subbasin_name, river_id, units = \
        get_ecmwf_forecast_statistics(request)

    # ensure lower std dev values limited by the min
    std_dev_lower_df = \
        forecast_statistics['std_dev_range_lower']
    std_dev_lower_df[std_dev_lower_df < forecast_statistics['min']] =\
        forecast_statistics['min']

    # ----------------------------------------------
    # Chart Section
    # ----------------------------------------------
    datetime_start = forecast_statistics['mean'].index[0]
    datetime_end = forecast_statistics['mean'].index[-1]

    avg_series = go.Scatter(
        name='Mean',
        x=forecast_statistics['mean'].index,
        y=forecast_statistics['mean'].values,
        line=dict(
            color='blue',
        )
    )

    max_series = go.Scatter(
        name='Max',
        x=forecast_statistics['max'].index,
        y=forecast_statistics['max'].values,
        fill='tonexty',
        mode='lines',
        line=dict(
            color='rgb(152, 251, 152)',
            width=0,
        )
    )

    min_series = go.Scatter(
        name='Min',
        x=forecast_statistics['min'].index,
        y=forecast_statistics['min'].values,
        fill=None,
        mode='lines',
        line=dict(
            color='rgb(152, 251, 152)',
        )
    )

    std_dev_lower_series = go.Scatter(
        name='Std. Dev. Lower',
        x=std_dev_lower_df.index,
        y=std_dev_lower_df.values,
        fill='tonexty',
        mode='lines',
        line=dict(
            color='rgb(152, 251, 152)',
            width=0,
        )
    )

    std_dev_upper_series = go.Scatter(
        name='Std. Dev. Upper',
        x=forecast_statistics['std_dev_range_upper'].index,
        y=forecast_statistics['std_dev_range_upper'].values,
        fill='tonexty',
        mode='lines',
        line=dict(
            width=0,
            color='rgb(34, 139, 34)',
        )
    )

    plot_series = [min_series,
                   std_dev_lower_series,
                   std_dev_upper_series,
                   max_series,
                   avg_series]

    if 'high_res' in forecast_statistics:
        plot_series.append(go.Scatter(
            name='HRES',
            x=forecast_statistics['high_res'].index,
            y=forecast_statistics['high_res'].values,
            line=dict(
                color='black',
            )
        ))

    try:
        return_shapes, return_annotations = \
            get_return_period_ploty_info(
                request, datetime_start, datetime_end,
                forecast_statistics['max'].max())
    except NotFoundError:
        return_annotations = []
        return_shapes = []

    layout = go.Layout(
        title="Forecast<br><sub>{0} ({1}): {2}</sub>".format(
            watershed_name, subbasin_name, river_id),
        xaxis=dict(
            title='Date',
        ),
        yaxis=dict(
            title='Streamflow ({}<sup>3</sup>/s)'
                  .format(get_units_title(units))
        ),
        shapes=return_shapes,
        annotations=return_annotations
    )

    chart_obj = PlotlyView(
        go.Figure(data=plot_series,
                  layout=layout)
    )

    context = {
        'gizmo_object': chart_obj,
    }

    return render(request,
                  'streamflow_prediction_tool/gizmo_ajax.html',
                  context)
def get_historical_hydrograph(request):
    """""
    Returns ERA Interim hydrograph
    """""
    units = request.GET.get('units')
    historical_data_file, river_id, watershed_name, subbasin_name =\
        validate_historical_data(request.GET)

    with rivid_exception_handler('ERA Interim', river_id):
        with xarray.open_dataset(historical_data_file) as qout_nc:
            # get information from dataset
            qout_data = qout_nc.sel(rivid=river_id).Qout
            qout_values = qout_data.values
            qout_time = qout_data.time.values

    if units == 'english':
        # convert m3/s to ft3/s
        qout_values *= M3_TO_FT3

    # ----------------------------------------------
    # Chart Section
    # ----------------------------------------------
    qout_time = pd.to_datetime(qout_time)
    era_series = go.Scatter(
        name='ERA Interim',
        x=qout_time,
        y=qout_values,
    )

    return_shapes, return_annotations = \
        get_return_period_ploty_info(request, qout_time[0], qout_time[-1])

    layout = go.Layout(
        title="Historical Streamflow<br><sub>{0} ({1}): {2}</sub>".format(
            watershed_name, subbasin_name, river_id),
        xaxis=dict(
            title='Date',
        ),
        yaxis=dict(
            title='Streamflow ({}<sup>3</sup>/s)'
                  .format(get_units_title(units))
        ),
        shapes=return_shapes,
        annotations=return_annotations
    )

    chart_obj = PlotlyView(
        go.Figure(data=[era_series],
                  layout=layout)
    )

    context = {
        'gizmo_object': chart_obj,
    }

    return render(request,
                  'streamflow_prediction_tool/gizmo_ajax.html',
                  context)
def get_daily_seasonal_streamflow_chart(request):
    """
    Returns daily seasonal streamflow chart for unique river ID
    """
    units = request.GET.get('units')
    seasonal_data_file, river_id, watershed_name, subbasin_name =\
        validate_historical_data(request.GET,
                                 "seasonal_average*.nc",
                                 "Seasonal Average")

    with rivid_exception_handler('Seasonal Average', river_id):
        with xarray.open_dataset(seasonal_data_file) as seasonal_nc:
            seasonal_data = seasonal_nc.sel(rivid=river_id)
            base_date = datetime.datetime(2017, 1, 1)
            day_of_year = \
                [base_date + datetime.timedelta(days=ii)
                 for ii in range(seasonal_data.dims['day_of_year'])]
            season_avg = seasonal_data.average_flow.values
            season_std = seasonal_data.std_dev_flow.values

            season_avg[season_avg < 0] = 0

            avg_plus_std = season_avg + season_std
            avg_min_std = season_avg - season_std

            avg_plus_std[avg_plus_std < 0] = 0
            avg_min_std[avg_min_std < 0] = 0

    if units == 'english':
        # convert from m3/s to ft3/s
        season_avg *= M3_TO_FT3
        avg_plus_std *= M3_TO_FT3
        avg_min_std *= M3_TO_FT3

    # generate chart
    avg_scatter = go.Scatter(
        name='Average',
        x=day_of_year,
        y=season_avg,
        line=dict(
            color='#0066ff'
        )
    )

    std_plus_scatter = go.Scatter(
        name='Std. Dev. Upper',
        x=day_of_year,
        y=avg_plus_std,
        fill=None,
        mode='lines',
        line=dict(
            color='#98fb98'
        )
    )

    std_min_scatter = go.Scatter(
        name='Std. Dev. Lower',
        x=day_of_year,
        y=avg_min_std,
        fill='tonexty',
        mode='lines',
        line=dict(
            color='#98fb98',
        )
    )

    layout = go.Layout(
        title="Daily Seasonal Streamflow<br>"
              "<sub>{0} ({1}): {2}</sub>"
              .format(watershed_name, subbasin_name, river_id),
        xaxis=dict(
            title='Day of Year',
            tickformat="%b"),
        yaxis=dict(
            title='Streamflow ({}<sup>3</sup>/s)'
                  .format(get_units_title(units)))
    )

    chart_obj = PlotlyView(
        go.Figure(data=[std_plus_scatter,
                        std_min_scatter,
                        avg_scatter],
                  layout=layout)
    )

    context = {
        'gizmo_object': chart_obj,
    }

    return render(request,
                  'streamflow_prediction_tool/gizmo_ajax.html',
                  context)