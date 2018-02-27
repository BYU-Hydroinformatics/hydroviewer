from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from django.http import HttpResponse, JsonResponse

import requests
import json
import numpy as np
from csv import writer as csv_writer
import scipy.stats as sp
import datetime as dt

import plotly.graph_objs as go
from tethys_sdk.gizmos import PlotlyView

def home(request):
    """
    Controller for the app home page.
    """
    # model_input = SelectInput(display_text='',
    #                           name='model',
    #                           multiple=False,
    #                           options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf')],
    #                           initial=['Select Model'],
    #                           original=True)

    res = requests.get('https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetWatersheds/',
                       headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

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
        # "model_input": model_input,
        "watershed_select": watershed_select
    }

    return render(request, 'hydroviewer_nepal/home.html', context)


def get_warning_points(request):
    get_data = request.GET
    try:
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']

        # dates_res = requests.get(
        #     'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetAvailableDates/?watershed_name=' + watershed +
        #     '&subbasin_name=' + subbasin, headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})
        #
        # folder = eval(dates_res.content)[-1]

        res20 = requests.get(
            'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetWarningPoints/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin + '&return_period=20',
            headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

        res10 = requests.get(
            'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetWarningPoints/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin + '&return_period=10',
            headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

        res2 = requests.get(
            'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetWarningPoints/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin + '&return_period=2',
            headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

        return JsonResponse({
            "success": "Data analysis complete!",
            "warning20":json.loads(res20.content)["features"],
            "warning10":json.loads(res10.content)["features"],
            "warning2":json.loads(res2.content)["features"]
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
        units = 'metric'

        if model == 'ecmwf-rapid':
            mean_res = requests.get(
                'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetForecast/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&forecast_folder=' +
                startdate + '&stat_type=mean&return_format=csv',
                headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

            hres_res = requests.get(
                'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetForecast/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&forecast_folder=' +
                startdate + '&stat_type=high_res&return_format=csv',
                headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

            min_res = requests.get(
                'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetForecast/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&forecast_folder=' +
                startdate + '&stat_type=min&return_format=csv',
                headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

            max_res = requests.get(
                'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetForecast/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&forecast_folder=' +
                startdate + '&stat_type=max&return_format=csv',
                headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

            std_dev_lower_res = requests.get(
                'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetForecast/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&forecast_folder=' +
                startdate + '&stat_type=std_dev_range_lower&return_format=csv',
                headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

            std_dev_upper_res = requests.get(
                'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetForecast/?watershed_name=' +
                watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&forecast_folder=' +
                startdate + '&stat_type=std_dev_range_upper&return_format=csv',
                headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

            mean_pairs = mean_res.content.splitlines()
            hres_pairs = hres_res.content.splitlines()
            min_pairs = min_res.content.splitlines()
            max_pairs = max_res.content.splitlines()
            std_dev_lower_pairs = std_dev_lower_res.content.splitlines()
            std_dev_upper_pairs = std_dev_upper_res.content.splitlines()

            mean_pairs.pop(0)
            hres_pairs.pop(0)
            min_pairs.pop(0)
            max_pairs.pop(0)
            std_dev_lower_pairs.pop(0)
            std_dev_upper_pairs.pop(0)

            dates = []
            # hres_dates = []

            mean_values = []
            hres_values = []
            min_values = []
            max_values = []
            std_dev_lower_values = []
            std_dev_upper_values = []

            stats_list = zip(mean_pairs, hres_pairs, min_pairs, max_pairs, std_dev_lower_pairs, std_dev_upper_pairs)
            for mean_pair, hres_pair, min_pair, max_pair, std_dev_lower_pair, std_dev_upper_pair in stats_list:
                dates.append(dt.datetime.strptime(mean_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
                # hres_dates.append(dt.datetime.strptime(hres_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))

                mean_values.append(float(mean_pair.split(',')[1]))
                hres_values.append(float(hres_pair.split(',')[1]))
                min_values.append(float(min_pair.split(',')[1]))
                max_values.append(float(max_pair.split(',')[1]))
                std_dev_lower_values.append(float(std_dev_lower_pair.split(',')[1]))
                std_dev_upper_values.append(float(std_dev_upper_pair.split(',')[1]))


            # ----------------------------------------------
            # Chart Section
            # ----------------------------------------------

            datetime_start = dates[0]
            datetime_end = dates[-1]

            avg_series = go.Scatter(
                name='Mean',
                x=dates,
                y=mean_values,
                line=dict(
                    color='blue',
                )
            )

            max_series = go.Scatter(
                name='Max',
                x=dates,
                y=max_values,
                fill='tonexty',
                mode='lines',
                line=dict(
                    color='rgb(152, 251, 152)',
                    width=0,
                )
            )

            min_series = go.Scatter(
                name='Min',
                x=dates,
                y=min_values,
                fill=None,
                mode='lines',
                line=dict(
                    color='rgb(152, 251, 152)',
                )
            )

            std_dev_lower_series = go.Scatter(
                name='Std. Dev. Lower',
                x=dates,
                y=std_dev_lower_values,
                fill='tonexty',
                mode='lines',
                line=dict(
                    color='rgb(152, 251, 152)',
                    width=0,
                )
            )

            std_dev_upper_series = go.Scatter(
                name='Std. Dev. Upper',
                x=dates,
                y=std_dev_upper_values,
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

            if hres_pairs:
                plot_series.append(go.Scatter(
                    name='HRES',
                    x=dates,
                    y=hres_values,
                    line=dict(
                        color='black',
                    )
                ))

            try:
                return_shapes, return_annotations = get_return_period_ploty_info(request, datetime_start, datetime_end)
            except:
                return_annotations = []
                return_shapes = []


            layout = go.Layout(
                title="Forecast<br><sub>{0} ({1}): {2}</sub>".format(
                    watershed, subbasin, comid),
                xaxis=dict(
                    title='Date',
                ),
                yaxis=dict(
                    title='Streamflow ({}<sup>3</sup>/s)'.format(get_units_title(units)),
                    range=[0, max(max_values) + max(max_values)/5]
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

            return render(request, 'hydroviewer_nepal/gizmo_ajax.html', context)


    except Exception as e:
        print str(e)
        return JsonResponse({'error': 'No data found for the selected reach.'})


def get_available_dates(request):
    get_data = request.GET

    watershed = get_data['watershed']
    subbasin = get_data['subbasin']
    comid = get_data['comid']
    res = requests.get(
            'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetAvailableDates/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin,
            headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

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

    res = requests.get(
            'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetReturnPeriods/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid,
            headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

    return eval(res.content)


def get_historic_data(request):
    """""
    Returns ERA Interim hydrograph
    """""

    get_data = request.GET

    try:
        # model = get_data['model']
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['comid']
        units = 'metric'

        era_res = requests.get(
            'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&return_format=csv',
            headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

        era_pairs = era_res.content.splitlines()
        era_pairs.pop(0)

        era_dates = []
        era_values = []

        for era_pair in era_pairs:
            era_dates.append(dt.datetime.strptime(era_pair.split(',')[0], '%Y-%m-%d %H:%M:%S'))
            era_values.append(float(era_pair.split(',')[1]))

        # ----------------------------------------------
        # Chart Section
        # --------------------------------------
        era_series = go.Scatter(
            name='ERA Interim',
            x=era_dates,
            y=era_values,
        )

        return_shapes, return_annotations = get_return_period_ploty_info(request, era_dates[0], era_dates[-1])

        layout = go.Layout(
            title="Historical Streamflow<br><sub>{0} ({1}): {2}</sub>".format(
                watershed, subbasin, comid),
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

        return render(request,'hydroviewer_nepal/gizmo_ajax.html', context)

    except Exception as e:
        print str(e)
        return JsonResponse({'error': 'No historic data found for the selected reach.'})


def get_flow_duration_curve(request):
    get_data = request.GET

    try:
        # model = get_data['model']
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['comid']
        units = 'metric'

        era_res = requests.get(
            'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&return_format=csv',
            headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

        era_pairs = era_res.content.splitlines()
        era_pairs.pop(0)

        era_values = []

        for era_pair in era_pairs:
            era_values.append(float(era_pair.split(',')[1]))

        sorted_daily_avg = np.sort(era_values)[::-1]

        # ranks data from smallest to largest
        ranks = len(sorted_daily_avg) - sp.rankdata(sorted_daily_avg,
                                                    method='average')

        # calculate probability of each rank
        prob = [100*(ranks[i] / (len(sorted_daily_avg) + 1))
                for i in range(len(sorted_daily_avg))]

        flow_duration_sc = go.Scatter(
            x=prob,
            y=sorted_daily_avg,
        )

        layout = go.Layout(title="Flow-Duration Curve<br><sub>{0} ({1}): {2}</sub>"
                                 .format(watershed, subbasin, comid),
                           xaxis=dict(
                               title='Exceedance Probability (%)',),
                           yaxis=dict(
                               title='Streamflow ({}<sup>3</sup>/s)'
                                     .format(get_units_title(units)),
                               type='log',
                               autorange=True),
                           showlegend=False)

        chart_obj = PlotlyView(
            go.Figure(data=[flow_duration_sc],
                      layout=layout)
        )

        context = {
            'gizmo_object': chart_obj,
        }

        return render(request,'hydroviewer_nepal/gizmo_ajax.html', context)

    except Exception as e:
        print str(e)
        return JsonResponse({'error': 'No historic data found for calculating flow duration curve.'})


def get_return_period_ploty_info(request, datetime_start, datetime_end,
                                 band_alt_max=-9999):
    """
    Get shapes and annotations for plotly plot
    """

    # Return Period Section
    return_period_data = get_return_periods(request)
    return_max = float(return_period_data["max"])
    return_20 = float(return_period_data["twenty"])
    return_10 = float(return_period_data["ten"])
    return_2 = float(return_period_data["two"])

    # plotly info section
    shapes = [
         # return 20 band
         dict(
             type='rect',
             xref='x',
             yref='y',
             x0=datetime_start,
             y0=return_20,
             x1=datetime_end,
             y1=max(return_max, band_alt_max),
             line=dict(width=0),
             fillcolor='rgba(128, 0, 128, 0.4)',
         ),
         # return 10 band
         dict(
             type='rect',
             xref='x',
             yref='y',
             x0=datetime_start,
             y0=return_10,
             x1=datetime_end,
             y1=return_20,
             line=dict(width=0),
             fillcolor='rgba(255, 0, 0, 0.4)',
         ),
         # return 2 band
         dict(
             type='rect',
             xref='x',
             yref='y',
             x0=datetime_start,
             y0=return_2,
             x1=datetime_end,
             y1=return_10,
             line=dict(width=0),
             fillcolor='rgba(255, 255, 0, 0.4)',
         ),
    ]
    annotations = [
        # return max
        dict(
            x=datetime_end,
            y=return_max,
            xref='x',
            yref='y',
            text='Max. ({:.1f})'.format(return_max),
            showarrow=False,
            xanchor='left',
        ),
        # return 20 band
        dict(
            x=datetime_end,
            y=return_20,
            xref='x',
            yref='y',
            text='20-yr ({:.1f})'.format(return_20),
            showarrow=False,
            xanchor='left',
        ),
        # return 10 band
        dict(
            x=datetime_end,
            y=return_10,
            xref='x',
            yref='y',
            text='10-yr ({:.1f})'.format(return_10),
            showarrow=False,
            xanchor='left',
        ),
        # return 2 band
        dict(
            x=datetime_end,
            y=return_2,
            xref='x',
            yref='y',
            text='2-yr ({:.1f})'.format(return_2),
            showarrow=False,
            xanchor='left',
        ),
    ]

    return shapes, annotations


def get_historic_data_csv(request):
    """""
    Returns ERA Interim data as csv
    """""

    get_data = request.GET

    try:
        # model = get_data['model']
        watershed = get_data['watershed_name']
        subbasin = get_data['subbasin_name']
        comid = get_data['reach_id']
        units = get_data['units']

        era_res = requests.get(
            'https://tethys-staging.byu.edu/apps/streamflow-prediction-tool/api/GetHistoricData/?watershed_name=' +
            watershed + '&subbasin_name=' + subbasin + '&reach_id=' + comid + '&return_format=csv',
            headers={'Authorization': 'Token 0b1310ea009af7de0315213adf21ea765e57b03a'})

        qout_data = era_res.content.splitlines()
        qout_data.pop(0)
        print qout_data, '*******'

        # prepare to write response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=historic_streamflow_{0}_{1}_{2}.csv'.format(watershed, subbasin, comid)

        writer = csv_writer(response)

        writer.writerow(['datetime', 'streamflow ({}3/s)'.format(get_units_title(units))])

        for row_data in qout_data:
            writer.writerow(row_data.split(','))

        return response

    except Exception as e:
        print str(e)
        return JsonResponse({'error': 'No historic data found.'})


# def get_daily_seasonal_streamflow_chart(request):
#     """
#     Returns daily seasonal streamflow chart for unique river ID
#     """
#     units = request.GET.get('units')
#     seasonal_data_file, river_id, watershed_name, subbasin_name =\
#         validate_historical_data(request.GET,
#                                  "seasonal_average*.nc",
#                                  "Seasonal Average")
#
#     with rivid_exception_handler('Seasonal Average', river_id):
#         with xarray.open_dataset(seasonal_data_file) as seasonal_nc:
#             seasonal_data = seasonal_nc.sel(rivid=river_id)
#             base_date = datetime.datetime(2017, 1, 1)
#             day_of_year = \
#                 [base_date + datetime.timedelta(days=ii)
#                  for ii in range(seasonal_data.dims['day_of_year'])]
#             season_avg = seasonal_data.average_flow.values
#             season_std = seasonal_data.std_dev_flow.values
#
#             season_avg[season_avg < 0] = 0
#
#             avg_plus_std = season_avg + season_std
#             avg_min_std = season_avg - season_std
#
#             avg_plus_std[avg_plus_std < 0] = 0
#             avg_min_std[avg_min_std < 0] = 0
#
#     if units == 'english':
#         # convert from m3/s to ft3/s
#         season_avg *= M3_TO_FT3
#         avg_plus_std *= M3_TO_FT3
#         avg_min_std *= M3_TO_FT3
#
#     # generate chart
#     avg_scatter = go.Scatter(
#         name='Average',
#         x=day_of_year,
#         y=season_avg,
#         line=dict(
#             color='#0066ff'
#         )
#     )
#
#     std_plus_scatter = go.Scatter(
#         name='Std. Dev. Upper',
#         x=day_of_year,
#         y=avg_plus_std,
#         fill=None,
#         mode='lines',
#         line=dict(
#             color='#98fb98'
#         )
#     )
#
#     std_min_scatter = go.Scatter(
#         name='Std. Dev. Lower',
#         x=day_of_year,
#         y=avg_min_std,
#         fill='tonexty',
#         mode='lines',
#         line=dict(
#             color='#98fb98',
#         )
#     )
#
#     layout = go.Layout(
#         title="Daily Seasonal Streamflow<br>"
#               "<sub>{0} ({1}): {2}</sub>"
#               .format(watershed_name, subbasin_name, river_id),
#         xaxis=dict(
#             title='Day of Year',
#             tickformat="%b"),
#         yaxis=dict(
#             title='Streamflow ({}<sup>3</sup>/s)'
#                   .format(get_units_title(units)))
#     )
#
#     chart_obj = PlotlyView(
#         go.Figure(data=[std_plus_scatter,
#                         std_min_scatter,
#                         avg_scatter],
#                   layout=layout)
#     )
#
#     context = {
#         'gizmo_object': chart_obj,
#     }
#
#     return render(request,
#                   'streamflow_prediction_tool/gizmo_ajax.html',
#                   context)


def get_units_title(unit_type):
    """
    Get the title for units
    """
    units_title = "m"
    if unit_type == 'english':
        units_title = "ft"
    return units_title
