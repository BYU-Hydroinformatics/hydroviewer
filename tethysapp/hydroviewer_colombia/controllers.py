from tethys_sdk.gizmos import *
from django.shortcuts import render
from tethys_sdk.gizmos import PlotlyView
from tethys_sdk.base import TethysAppBase
from tethys_sdk.workspaces import app_workspace
from tethys_sdk.permissions import has_permission
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required

import io
import os
import json
import requests
import geoglows
import numpy as np
import pandas as pd
import datetime as dt
import hydrostats.data
import plotly.graph_objs as go
from csv import writer as csv_writer
from requests.auth import HTTPBasicAuth

from .app import Hydroviewer as app
from .helpers import *

base_name = __package__.split('.')[-1]


def set_custom_setting(defaultModelName, defaultWSName):
    from tethys_apps.models import TethysApp
    db_app = TethysApp.objects.get(package=app.package)
    custom_settings = db_app.custom_settings

    db_setting = db_app.custom_settings.get(name='default_model_type')
    db_setting.value = defaultModelName
    db_setting.save()

    db_setting = db_app.custom_settings.get(name='default_watershed_name')
    db_setting.value = defaultWSName
    db_setting.save()


def home(request):
    # Check if we have a default model. If we do, then redirect the user to the default model's page
    default_model = app.get_custom_setting('default_model_type')
    if default_model:
        model_func = switch_model(default_model)
        if model_func is not 'invalid':
            return globals()[model_func](request)
        else:
            return home_standard(request)
    else:
        return home_standard(request)


def home_standard(request):
    model_input = SelectInput(display_text='',
                              name='model',
                              multiple=False,
                              options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf')],
                              initial=['Select Model'],
                              original=True)

    zoom_info = TextInput(display_text='',
                          initial=json.dumps(app.get_custom_setting('zoom_info')),
                          name='zoom_info',
                          disabled=True)

    context = {
        "base_name": base_name,
        "model_input": model_input,
        "zoom_info": zoom_info
    }

    return render(request, '{0}/home.html'.format(base_name), context)

def get_popup_response(request):
    """
    get station attributes
    """

    simulated_data_path_file = os.path.join(app.get_app_workspace().path, 'simulated_data.json')
    f = open(simulated_data_path_file, 'w')
    f.close()

    stats_data_path_file = os.path.join(app.get_app_workspace().path, 'stats_data.json')
    f2 = open(stats_data_path_file, 'w')
    f2.close()

    ensemble_data_path_file = os.path.join(app.get_app_workspace().path, 'ensemble_data.json')
    f3 = open(ensemble_data_path_file, 'w')
    f3.close()

    return_obj = {}

    print("finished get_popup_response")

    return JsonResponse({})

def ecmwf(request):
    # Can Set Default permissions : Only allowed for admin users
    can_update_default = has_permission(request, 'update_default')

    if (can_update_default):
        defaultUpdateButton = Button(
            display_text='Save',
            name='update_button',
            style='success',
            attributes={
                'data-toggle': 'tooltip',
                'data-placement': 'bottom',
                'title': 'Save as Default Options for WS'
            })
    else:
        defaultUpdateButton = False

    # Check if we need to hide the WS options dropdown.
    hiddenAttr = ""
    if app.get_custom_setting('show_dropdown') and app.get_custom_setting(
            'default_model_type') and app.get_custom_setting('default_watershed_name'):
        hiddenAttr = "hidden"

    init_model_val = request.GET.get('model', False) or app.get_custom_setting('default_model_type') or 'Select Model'
    init_ws_val = app.get_custom_setting('default_watershed_name') or 'Select Watershed'

    model_input = SelectInput(display_text='',
                              name='model',
                              multiple=False,
                              options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf'),],
                              initial=[init_model_val],
                              classes=hiddenAttr,
                              original=True)

    geoserver_engine = app.get_spatial_dataset_service(
        name='main_geoserver', as_engine=True)

    geos_username = geoserver_engine.username
    geos_password = geoserver_engine.password
    my_geoserver = geoserver_engine.endpoint.replace('rest', '')

    watershed_list = [['Select Watershed', '']]  # + watershed_list

    res2 = requests.get(my_geoserver + '/rest/workspaces/' + app.get_custom_setting('workspace') +
                        '/featuretypes.json', auth=HTTPBasicAuth(geos_username, geos_password), verify=False)

    for i in range(len(json.loads(res2.content)['featureTypes']['featureType'])):
        raw_feature = json.loads(res2.content)['featureTypes']['featureType'][i]['name']
        if 'drainage_line' in raw_feature and any(
                n in raw_feature for n in app.get_custom_setting('keywords').replace(' ', '').split(',')):
            feat_name = raw_feature.split('-')[0].replace('_', ' ').title() + ' (' + \
                        raw_feature.split('-')[1].replace('_', ' ').title() + ')'
            if feat_name not in str(watershed_list):
                watershed_list.append([feat_name, feat_name])

    # Add the default WS if present and not already in the list
    if init_ws_val and init_ws_val not in str(watershed_list):
        watershed_list.append([init_ws_val, init_ws_val])

    watershed_select = SelectInput(display_text='',
                                   name='watershed',
                                   options=watershed_list,
                                   initial=[init_ws_val],
                                   original=True,
                                   classes=hiddenAttr,
                                   attributes={'onchange': "javascript:view_watershed();" + hiddenAttr}
                                   )

    zoom_info = TextInput(display_text='',
                          initial=json.dumps(app.get_custom_setting('zoom_info')),
                          name='zoom_info',
                          disabled=True)

    # Retrieve a geoserver engine and geoserver credentials.
    geoserver_engine = app.get_spatial_dataset_service(
        name='main_geoserver', as_engine=True)

    my_geoserver = geoserver_engine.endpoint.replace('rest', '')

    geoserver_base_url = my_geoserver
    geoserver_workspace = app.get_custom_setting('workspace')
    region = app.get_custom_setting('region')
    geoserver_endpoint = TextInput(display_text='',
                                   initial=json.dumps([geoserver_base_url, geoserver_workspace, region]),
                                   name='geoserver_endpoint',
                                   disabled=True)

    today = dt.datetime.now()
    year = str(today.year)
    month = str(today.strftime("%m"))
    day = str(today.strftime("%d"))
    date = day + '/' + month + '/' + year
    lastyear = int(year) - 1
    date2 = day + '/' + month + '/' + str(lastyear)

    startdateobs = DatePicker(name='startdateobs',
                              display_text='Start Date',
                              autoclose=True,
                              format='dd/mm/yyyy',
                              start_date='01/01/1950',
                              start_view='month',
                              today_button=True,
                              initial=date2,
                              classes='datepicker')

    enddateobs = DatePicker(name='enddateobs',
                            display_text='End Date',
                            autoclose=True,
                            format='dd/mm/yyyy',
                            start_date='01/01/1950',
                            start_view='month',
                            today_button=True,
                            initial=date,
                            classes='datepicker')

    res = requests.get('https://geoglows.ecmwf.int/api/AvailableDates/?region=central_america-geoglows', verify=False)
    data = res.json()
    dates_array = (data.get('available_dates'))

    dates = []

    for date in dates_array:
        if len(date) == 10:
            date_mod = date + '000'
            date_f = dt.datetime.strptime(date_mod, '%Y%m%d.%H%M').strftime('%Y-%m-%d %H:%M')
        else:
            date_f = dt.datetime.strptime(date, '%Y%m%d.%H%M').strftime('%Y-%m-%d')
            date = date[:-3]
        dates.append([date_f, date])
        dates = sorted(dates)

    dates.append(['Select Date', dates[-1][1]])
    # print(dates)
    dates.reverse()

    # Date Picker Options
    date_picker = DatePicker(name='datesSelect',
                             display_text='Date',
                             autoclose=True,
                             format='yyyy-mm-dd',
                             start_date=dates[-1][0],
                             end_date=dates[1][0],
                             start_view='month',
                             today_button=True,
                             initial='')

    #Select Region
    region_index = json.load(open(os.path.join(os.path.dirname(__file__), 'public', 'geojson', 'index.json')))
    regions = SelectInput(
        display_text='Zoom to a Region:',
        name='regions',
        multiple=False,
        #original=True,
        options=[(region_index[opt]['name'], opt) for opt in region_index],
        initial='',
        select2_options={'placeholder': 'Select a Region', 'allowClear': False}
    )

    # Select Basins
    basin_index = json.load(open(os.path.join(os.path.dirname(__file__), 'public', 'geojson2', 'index2.json')))
    basins = SelectInput(
        display_text='Zoom to a Basin:',
        name='basins',
        multiple=False,
        # original=True,
        options=[(basin_index[opt]['name'], opt) for opt in basin_index],
        initial='',
        select2_options={'placeholder': 'Select a Basin', 'allowClear': False}
    )

    # Select SubBasins
    subbasin_index = json.load(open(os.path.join(os.path.dirname(__file__), 'public', 'geojson3', 'index3.json')))
    subbasins = SelectInput(
        display_text='Zoom to a Subbasin:',
        name='subbasins',
        multiple=False,
        # original=True,
        options=[(subbasin_index[opt]['name'], opt) for opt in subbasin_index],
        initial='',
        select2_options={'placeholder': 'Select a Subbasin', 'allowClear': False}
    )

    context = {
        "base_name": base_name,
        "model_input": model_input,
        "watershed_select": watershed_select,
        "zoom_info": zoom_info,
        "geoserver_endpoint": geoserver_endpoint,
        "defaultUpdateButton": defaultUpdateButton,
        "startdateobs": startdateobs,
        "enddateobs": enddateobs,
        "date_picker": date_picker,
        "regions": regions,
        "basins": basins,
        "subbasins": subbasins,
    }

    return render(request, '{0}/ecmwf.html'.format(base_name), context)


@app_workspace
def get_warning_points(request, app_workspace):
    get_data = request.GET
    colombia_id_path = os.path.join(app_workspace.path, 'colombia_reachids.csv')
    reach_pds = pd.read_csv(colombia_id_path)
    reach_ids_list = reach_pds['COMID'].tolist()
    return_obj = {}
    # print("REACH_PDS")
    # print(reach_ids_list)
    if get_data['model'] == 'ECMWF-RAPID':
        try:
            watershed = get_data['watershed']
            subbasin = get_data['subbasin']

            res = requests.get(app.get_custom_setting(
                'api_source') + '/api/ForecastWarnings/?region=' + watershed + '-' + 'geoglows' + '&return_format=csv',
                               verify=False).content

            res_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
            cols = ['date_exceeds_return_period_2', 'date_exceeds_return_period_5', 'date_exceeds_return_period_10',
                    'date_exceeds_return_period_25', 'date_exceeds_return_period_50', 'date_exceeds_return_period_100']

            res_df["rp_all"] = res_df[cols].apply(lambda x: ','.join(x.replace(np.nan, '0')), axis=1)

            test_list = res_df["rp_all"].tolist()

            final_new_rp = []
            for term in test_list:
                new_rp = []
                terms = term.split(',')
                for te in terms:
                    if te is not '0':
                        # print('yeah')
                        new_rp.append(1)
                    else:
                        new_rp.append(0)
                final_new_rp.append(new_rp)

            res_df['rp_all2'] = final_new_rp

            res_df = res_df.reset_index()
            res_df = res_df[res_df['comid'].isin(reach_ids_list)]

            d = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(),
                 'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist()}
            df_final = pd.DataFrame(data=d)

            df_final[['rp_2', 'rp_5', 'rp_10', 'rp_25', 'rp_50', 'rp_100']] = pd.DataFrame(res_df.rp_all2.tolist(),
                                                                                           index=df_final.index)
            d2 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(),
                  'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_2']}
            d5 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(),
                  'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_5']}
            d10 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(),
                   'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_10']}
            d25 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(),
                   'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_25']}
            d50 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(),
                   'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(), 'rp': df_final['rp_50']}
            d100 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(),
                    'lat': res_df['stream_lat'].tolist(), 'lon': res_df['stream_lon'].tolist(),
                    'rp': df_final['rp_100']}

            df_final_2 = pd.DataFrame(data=d2)
            df_final_2 = df_final_2[df_final_2['rp'] > 0]
            df_final_5 = pd.DataFrame(data=d5)
            df_final_5 = df_final_5[df_final_5['rp'] > 0]
            df_final_10 = pd.DataFrame(data=d10)
            df_final_10 = df_final_10[df_final_10['rp'] > 0]
            df_final_25 = pd.DataFrame(data=d25)
            df_final_25 = df_final_25[df_final_25['rp'] > 0]
            df_final_50 = pd.DataFrame(data=d50)
            df_final_50 = df_final_50[df_final_50['rp'] > 0]
            df_final_100 = pd.DataFrame(data=d100)
            df_final_100 = df_final_100[df_final_100['rp'] > 0]

            return_obj['success'] = "Data analysis complete!"
            return_obj['warning2'] = create_rp(df_final_2)
            return_obj['warning5'] = create_rp(df_final_5)
            return_obj['warning10'] = create_rp(df_final_10)
            return_obj['warning25'] = create_rp(df_final_25)
            return_obj['warning50'] = create_rp(df_final_50)
            return_obj['warning100'] = create_rp(df_final_100)

            return JsonResponse(return_obj)
        except Exception as e:
            print(str(e))
            return JsonResponse({'error': 'No data found for the selected reach.'})
    else:
        pass


def create_rp(df_):
    war = {}

    list_coordinates = []
    for lat, lon in zip(df_['lat'].tolist(), df_['lon'].tolist()):
        list_coordinates.append([lat, lon])

    return list_coordinates


def ecmwf_get_time_series(request):
    get_data = request.GET
    try:
        # model = get_data['model']
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['comid']
        units = 'metric'

        '''Getting Forecast Stats'''
        if get_data['startdate'] != '':
            startdate = get_data['startdate']
        else:
            startdate = 'most_recent'

        if get_data['startdate'] != '':
            startdate = get_data['startdate']
            res = requests.get(app.get_custom_setting('api_source') + '/api/ForecastStats/?reach_id=' + comid + '&date=' + startdate + '&return_format=csv', verify=False).content
        else:
            res = requests.get(app.get_custom_setting('api_source') + '/api/ForecastStats/?reach_id=' + comid + '&return_format=csv',verify=False).content

        '''Stats'''
        stats_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
        stats_df.index = pd.to_datetime(stats_df.index)
        stats_df[stats_df < 0] = 0
        stats_df.index = stats_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
        stats_df.index = pd.to_datetime(stats_df.index)

        stats_data_file_path = os.path.join(app.get_app_workspace().path, 'stats_data.json')
        stats_df.index.name = 'Datetime'
        stats_df.to_json(stats_data_file_path)

        hydroviewer_figure = geoglows.plots.forecast_stats(stats=stats_df, titles={'Reach ID': comid})

        x_vals = (stats_df.index[0], stats_df.index[len(stats_df.index) - 1], stats_df.index[len(stats_df.index) - 1],
                  stats_df.index[0])
        max_visible = max(stats_df.max())

        '''Getting Forecast Records'''
        res = requests.get(app.get_custom_setting('api_source') + '/api/ForecastRecords/?reach_id=' + comid + '&return_format=csv', verify=False).content

        records_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
        records_df.index = pd.to_datetime(records_df.index)
        records_df[records_df < 0] = 0
        records_df.index = records_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
        records_df.index = pd.to_datetime(records_df.index)

        records_df = records_df.loc[records_df.index >= pd.to_datetime(stats_df.index[0] - dt.timedelta(days=8))]
        records_df = records_df.loc[records_df.index <= pd.to_datetime(stats_df.index[0] + dt.timedelta(days=2))]

        if len(records_df.index) > 0:
            hydroviewer_figure.add_trace(go.Scatter(
                name='1st days forecasts',
                x=records_df.index,
                y=records_df.iloc[:, 0].values,
                line=dict(
                    color='#FFA15A',
                )
            ))

            x_vals = (
            records_df.index[0], stats_df.index[len(stats_df.index) - 1], stats_df.index[len(stats_df.index) - 1],
            records_df.index[0])
            max_visible = max(max(records_df.max()), max_visible)

        '''Getting Return Periods'''
        res = requests.get(
            app.get_custom_setting('api_source') + '/api/ReturnPeriods/?reach_id=' + comid + '&return_format=csv',
            verify=False).content
        rperiods_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)

        r2 = int(rperiods_df.iloc[0]['return_period_2'])

        colors = {
            '2 Year': 'rgba(254, 240, 1, .4)',
            '5 Year': 'rgba(253, 154, 1, .4)',
            '10 Year': 'rgba(255, 56, 5, .4)',
            '20 Year': 'rgba(128, 0, 246, .4)',
            '25 Year': 'rgba(255, 0, 0, .4)',
            '50 Year': 'rgba(128, 0, 106, .4)',
            '100 Year': 'rgba(128, 0, 246, .4)',
        }

        if max_visible > r2:
            visible = True
            hydroviewer_figure.for_each_trace(
                lambda trace: trace.update(visible=True) if trace.name == "Maximum & Minimum Flow" else (), )
        else:
            visible = 'legendonly'
            hydroviewer_figure.for_each_trace(
                lambda trace: trace.update(visible=True) if trace.name == "Maximum & Minimum Flow" else (), )

        def template(name, y, color, fill='toself'):
            return go.Scatter(
                name=name,
                x=x_vals,
                y=y,
                legendgroup='returnperiods',
                fill=fill,
                visible=visible,
                line=dict(color=color, width=0))

        r5 = int(rperiods_df.iloc[0]['return_period_5'])
        r10 = int(rperiods_df.iloc[0]['return_period_10'])
        r25 = int(rperiods_df.iloc[0]['return_period_25'])
        r50 = int(rperiods_df.iloc[0]['return_period_50'])
        r100 = int(rperiods_df.iloc[0]['return_period_100'])

        hydroviewer_figure.add_trace(
            template('Return Periods', (r100 * 0.05, r100 * 0.05, r100 * 0.05, r100 * 0.05), 'rgba(0,0,0,0)',
                     fill='none'))
        hydroviewer_figure.add_trace(template(f'2 Year: {r2}', (r2, r2, r5, r5), colors['2 Year']))
        hydroviewer_figure.add_trace(template(f'5 Year: {r5}', (r5, r5, r10, r10), colors['5 Year']))
        hydroviewer_figure.add_trace(template(f'10 Year: {r10}', (r10, r10, r25, r25), colors['10 Year']))
        hydroviewer_figure.add_trace(template(f'25 Year: {r25}', (r25, r25, r50, r50), colors['25 Year']))
        hydroviewer_figure.add_trace(template(f'50 Year: {r50}', (r50, r50, r100, r100), colors['50 Year']))
        hydroviewer_figure.add_trace(template(f'100 Year: {r100}', (
        r100, r100, max(r100 + r100 * 0.05, max_visible), max(r100 + r100 * 0.05, max_visible)), colors['100 Year']))

        hydroviewer_figure['layout']['xaxis'].update(autorange=True)

        chart_obj = PlotlyView(hydroviewer_figure)

        context = {
            'gizmo_object': chart_obj,
        }

        return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'No data found for the selected reach.'})

def get_time_series(request):
    return ecmwf_get_time_series(request)

def get_available_dates(request):
    get_data = request.GET

    watershed = get_data['watershed']
    subbasin = get_data['subbasin']
    comid = get_data['comid']
    res = requests.get(
        app.get_custom_setting('api_source') + '/api/AvailableDates/?region=' + watershed + '-' + subbasin,
        verify=False)

    data = res.json()

    dates_array = (data.get('available_dates'))

    # print(dates_array)

    dates = []

    for date in dates_array:
        if len(date) == 10:
            date_mod = date + '000'
            date_f = dt.datetime.strptime(date_mod, '%Y%m%d.%H%M').strftime('%Y-%m-%d %H:%M')
        else:
            date_f = dt.datetime.strptime(date, '%Y%m%d.%H%M').strftime('%Y-%m-%d')
            date = date[:-3]
        dates.append([date_f, date, watershed, subbasin, comid])

    dates.append(['Select Date', dates[-1][1]])
    # print(dates)
    dates.reverse()
    # print(dates)

    return JsonResponse({
        "success": "Data analysis complete!",
        "available_dates": json.dumps(dates)
    })

def get_historic_data(request):
    """""
    Returns ERA 5 hydrograph
    """""

    get_data = request.GET

    try:
        # model = get_data['model']
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['comid']
        units = 'metric'

        '''Historical Simulation'''
        era_res = requests.get(app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv',verify=False).content

        simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
        simulated_df[simulated_df < 0] = 0
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
        simulated_df.index = pd.to_datetime(simulated_df.index)

        simulated_data_file_path = os.path.join(app.get_app_workspace().path, 'simulated_data.json')
        simulated_df.reset_index(level=0, inplace=True)
        simulated_df['datetime'] = simulated_df['datetime'].dt.strftime('%Y-%m-%d')
        simulated_df.set_index('datetime', inplace=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.index.name = 'Datetime'
        simulated_df.to_json(simulated_data_file_path)

        '''Getting Return Periods'''
        res = requests.get(
            app.get_custom_setting('api_source') + '/api/ReturnPeriods/?reach_id=' + comid + '&return_format=csv',
            verify=False).content
        rperiods_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)

        hydroviewer_figure = geoglows.plots.historic_simulation(simulated_df, rperiods_df, titles={'Reach ID': comid})

        chart_obj = PlotlyView(hydroviewer_figure)

        context = {
            'gizmo_object': chart_obj,
        }

        return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'No historic data found for the selected reach.'})


def get_flow_duration_curve(request):
    get_data = request.GET

    try:
        # model = get_data['model']
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['comid']
        units = 'metric'

        simulated_data_file_path = os.path.join(app.get_app_workspace().path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        hydroviewer_figure = geoglows.plots.flow_duration_curve(simulated_df, titles={'Reach ID': comid})

        chart_obj = PlotlyView(hydroviewer_figure)

        context = {
            'gizmo_object': chart_obj,
        }

        return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'No historic data found for calculating flow duration curve.'})


def get_historic_data_csv(request):
    """""
    Returns ERA 5 data as csv
    """""

    get_data = request.GET

    try:
        # model = get_data['model']
        watershed = get_data['watershed_name']
        subbasin = get_data['subbasin_name']
        comid = get_data['reach_id']

        simulated_data_file_path = os.path.join(app.get_app_workspace().path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=historic_streamflow_{0}_{1}_{2}.csv'.format(watershed, subbasin, comid)

        simulated_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

        return response

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'No historic data found.'})


def get_forecast_data_csv(request):
    """""
    Returns Forecast data as csv
    """""

    get_data = request.GET

    try:
        # model = get_data['model']
        watershed = get_data['watershed_name']
        subbasin = get_data['subbasin_name']
        comid = get_data['reach_id']

        if get_data['startdate'] != '':
            startdate = get_data['startdate']
        else:
            startdate = 'most_recent'

        '''Getting Forecast Stats'''
        stats_data_file_path = os.path.join(app.get_app_workspace().path, 'stats_data.json')
        stats_df = pd.read_json(stats_data_file_path, convert_dates=True)
        stats_df.index = pd.to_datetime(stats_df.index)
        stats_df.sort_index(inplace=True, ascending=True)

        init_time = stats_df.index[0]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=streamflow_forecast_{0}_{1}_{2}_{3}.csv'.format(
            watershed, subbasin, comid, init_time)

        stats_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

        return response

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'No forecast data found.'})

def get_forecast_ens_data_csv(request):
    """""
    Returns Forecast data as csv
    """""

    get_data = request.GET

    try:
        # model = get_data['model']
        watershed = get_data['watershed_name']
        subbasin = get_data['subbasin_name']
        comid = get_data['reach_id']

        '''Getting Forecast Stats'''
        ensemble_data_file_path = os.path.join(app.get_app_workspace().path, 'ensemble_data.json')
        ensemble_df = pd.read_json(ensemble_data_file_path, convert_dates=True)
        ensemble_df.index = pd.to_datetime(ensemble_df.index)
        ensemble_df.sort_index(inplace=True, ascending=True)

        init_time = ensemble_df.index[0]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=streamflow_forecast_ens_{0}_{1}_{2}_{3}.csv'.format(watershed, subbasin, comid, init_time)

        ensemble_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

        return response

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'No forecast data found.'})

def get_daily_seasonal_streamflow(request):
    """
     Returns daily seasonal streamflow chart for unique river ID
     """
    get_data = request.GET

    try:
        # model = get_data['model']
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['comid']
        units = 'metric'

        simulated_data_file_path = os.path.join(app.get_app_workspace().path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        dayavg_df = hydrostats.data.daily_average(simulated_df, rolling=True)

        hydroviewer_figure = geoglows.plots.daily_averages(dayavg_df, titles={'Reach ID': comid})

        chart_obj = PlotlyView(hydroviewer_figure)

        context = {
            'gizmo_object': chart_obj,
        }

        return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'No historic data found for calculating daily seasonality.'})


def get_monthly_seasonal_streamflow(request):
    """
     Returns daily seasonal streamflow chart for unique river ID
     """
    get_data = request.GET

    try:
        # model = get_data['model']
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['comid']
        units = 'metric'

        simulated_data_file_path = os.path.join(app.get_app_workspace().path, 'simulated_data.json')
        simulated_df = pd.read_json(simulated_data_file_path, convert_dates=True)
        simulated_df.index = pd.to_datetime(simulated_df.index)
        simulated_df.sort_index(inplace=True, ascending=True)

        monavg_df = hydrostats.data.monthly_average(simulated_df)

        hydroviewer_figure = geoglows.plots.monthly_averages(monavg_df, titles={'Reach ID': comid})

        chart_obj = PlotlyView(hydroviewer_figure)

        context = {
            'gizmo_object': chart_obj,
        }

        return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'No historic data found for calculating monthly seasonality.'})


def setDefault(request):
    get_data = request.GET
    set_custom_setting(get_data.get('ws_name'), get_data.get('model_name'))
    return JsonResponse({'success': True})


def get_units_title(unit_type):
    """
    Get the title for units
    """
    units_title = "m"
    if unit_type == 'english':
        units_title = "ft"
    return units_title


def forecastpercent(request):
    get_data = request.GET
    try:
        # model = get_data['model']
        watershed = get_data['watershed']
        subbasin = get_data['subbasin']
        comid = get_data['comid']
        units = 'metric'

        '''Forecast'''
        if get_data['startdate'] != '':
            startdate = get_data['startdate']
        else:
            startdate = 'most_recent'

        '''Getting Forecast Stats'''
        if get_data['startdate'] != '':
            startdate = get_data['startdate']
            ens = requests.get(app.get_custom_setting('api_source') + '/api/ForecastEnsembles/?reach_id=' + comid + '&date=' + startdate + '&ensemble=all&return_format=csv', verify=False).content
        else:
            ens = requests.get(app.get_custom_setting('api_source') + '/api/ForecastEnsembles/?reach_id=' + comid + '&ensemble=all&return_format=csv', verify=False).content

        '''Getting Forecast Stats'''
        stats_data_file_path = os.path.join(app.get_app_workspace().path, 'stats_data.json')
        stats_df = pd.read_json(stats_data_file_path, convert_dates=True)
        stats_df.index = pd.to_datetime(stats_df.index)
        stats_df.sort_index(inplace=True, ascending=True)

        '''Getting Forecast Ensemble'''
        ensemble_df = pd.read_csv(io.StringIO(ens.decode('utf-8')), index_col=0)
        ensemble_df.index = pd.to_datetime(ensemble_df.index)
        ensemble_df[ensemble_df < 0] = 0
        ensemble_df.index = ensemble_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
        ensemble_df.index = pd.to_datetime(ensemble_df.index)

        ensemble_data_file_path = os.path.join(app.get_app_workspace().path, 'ensemble_data.json')
        ensemble_df.index.name = 'Datetime'
        ensemble_df.to_json(ensemble_data_file_path)

        '''Getting Return Periods'''
        res = requests.get(app.get_custom_setting('api_source') + '/api/ReturnPeriods/?reach_id=' + comid + '&return_format=csv', verify=False).content
        rperiods_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)

        table = geoglows.plots.probabilities_table(stats_df, ensemble_df, rperiods_df)

        return HttpResponse(table)

    except Exception:
        return JsonResponse({'error': 'No data found for the selected station.'})


def get_discharge_data(request):
    """
    Get data from fews stations
    """
    get_data = request.GET

    try:

        codEstacion = get_data['stationcode']
        # YYYY/MM/DD

        url = 'http://fews.ideam.gov.co/colombia/jsonQ/00' + codEstacion + 'Qobs.json'

        f = requests.get(url, verify=False)
        data = f.json()

        observedDischarge = (data.get('obs'))
        sensorDischarge = (data.get('sen'))

        observedDischarge = (observedDischarge.get('data'))
        sensorDischarge = (sensorDischarge.get('data'))

        datesObservedDischarge = [row[0] for row in observedDischarge]
        observedDischarge = [row[1] for row in observedDischarge]

        datesSensorDischarge = [row[0] for row in sensorDischarge]
        sensorDischarge = [row[1] for row in sensorDischarge]

        dates = []
        discharge = []

        for i in range(0, len(datesObservedDischarge) - 1):
            year = int(datesObservedDischarge[i][0:4])
            month = int(datesObservedDischarge[i][5:7])
            day = int(datesObservedDischarge[i][8:10])
            hh = int(datesObservedDischarge[i][11:13])
            mm = int(datesObservedDischarge[i][14:16])
            dates.append(dt.datetime(year, month, day, hh, mm))
            discharge.append(observedDischarge[i])

        datesObservedDischarge = dates
        observedDischarge = discharge

        dates = []
        discharge = []

        for i in range(0, len(datesSensorDischarge) - 1):
            year = int(datesSensorDischarge[i][0:4])
            month = int(datesSensorDischarge[i][5:7])
            day = int(datesSensorDischarge[i][8:10])
            hh = int(datesSensorDischarge[i][11:13])
            mm = int(datesSensorDischarge[i][14:16])
            dates.append(dt.datetime(year, month, day, hh, mm))
            discharge.append(sensorDischarge[i])

        datesSensorDischarge = dates
        sensorDischarge = discharge

        observed_Q = go.Scatter(
            x=datesObservedDischarge,
            y=observedDischarge,
            name='Observed'
        )

        sensor_Q = go.Scatter(
            x=datesSensorDischarge,
            y=sensorDischarge,
            name='Sensor'
        )

        layout = go.Layout(title='Observed Discharge',
                           xaxis=dict(
                               title='Dates', ),
                           yaxis=dict(
                               title='Discharge (m<sup>3</sup>/s)',
                               autorange=True),
                           showlegend=True)

        chart_obj = PlotlyView(
            go.Figure(data=[observed_Q, sensor_Q],
                      layout=layout)
        )

        context = {
            'gizmo_object': chart_obj,
        }

        return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'No  data found for the station.'})


def get_observed_discharge_csv(request):
    """
    Get data from fews stations
    """

    get_data = request.GET

    try:
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        url = 'http://fews.ideam.gov.co/colombia/jsonQ/00' + codEstacion + 'Qobs.json'

        f = requests.get(url, verify=False)
        data = f.json()

        observedDischarge = (data.get('obs'))
        observedDischarge = (observedDischarge.get('data'))

        datesObservedDischarge = [row[0] for row in observedDischarge]
        observedDischarge = [row[1] for row in observedDischarge]

        dates = []
        discharge = []

        for i in range(0, len(datesObservedDischarge) - 1):
            year = int(datesObservedDischarge[i][0:4])
            month = int(datesObservedDischarge[i][5:7])
            day = int(datesObservedDischarge[i][8:10])
            hh = int(datesObservedDischarge[i][11:13])
            mm = int(datesObservedDischarge[i][14:16])
            dates.append(dt.datetime(year, month, day, hh, mm))
            discharge.append(observedDischarge[i])

        datesObservedDischarge = dates
        observedDischarge = discharge

        pairs = [list(a) for a in zip(datesObservedDischarge, observedDischarge)]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=observed_discharge_{0}_{1}.csv'.format(
            codEstacion, nomEstacion)

        writer = csv_writer(response)
        writer.writerow(['datetime', 'flow (m3/s)'])

        for row_data in pairs:
            writer.writerow(row_data)

        return response

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'An unknown error occurred while retrieving the Discharge Data.'})


def get_sensor_discharge_csv(request):
    """
      Get data from fews stations
      """

    get_data = request.GET

    try:
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        url = 'http://fews.ideam.gov.co/colombia/jsonQ/00' + codEstacion + 'Qobs.json'

        f = requests.get(url, verify=False)
        data = f.json()

        sensorDischarge = (data.get('sen'))
        sensorDischarge = (sensorDischarge.get('data'))
        datesSensorDischarge = [row[0] for row in sensorDischarge]
        sensorDischarge = [row[1] for row in sensorDischarge]

        dates = []
        discharge = []

        for i in range(0, len(datesSensorDischarge) - 1):
            year = int(datesSensorDischarge[i][0:4])
            month = int(datesSensorDischarge[i][5:7])
            day = int(datesSensorDischarge[i][8:10])
            hh = int(datesSensorDischarge[i][11:13])
            mm = int(datesSensorDischarge[i][14:16])
            dates.append(dt.datetime(year, month, day, hh, mm))
            discharge.append(sensorDischarge[i])

        datesSensorDischarge = dates
        sensorDischarge = discharge

        pairs = [list(a) for a in zip(datesSensorDischarge, sensorDischarge)]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=sensor_discharge_{0}_{1}.csv'.format(
            codEstacion, nomEstacion)

        writer = csv_writer(response)
        writer.writerow(['datetime', 'flow (m3/s)'])

        for row_data in pairs:
            writer.writerow(row_data)

        return response

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'An unknown error occurred while retrieving the Discharge Data.'})


def get_waterlevel_data(request):
    """
    Get data from telemetric stations
    """
    get_data = request.GET

    try:

        codEstacion = get_data['stationcode']
        # YYYY/MM/DD

        url = 'http://fews.ideam.gov.co/colombia/jsonH/00' + codEstacion + 'Hobs.json'

        f = requests.get(url, verify=False)
        data = f.json()

        observedWaterLevel = (data.get('obs'))
        sensorWaterLevel = (data.get('sen'))

        observedWaterLevel = (observedWaterLevel.get('data'))
        sensorWaterLevel = (sensorWaterLevel.get('data'))

        datesObservedWaterLevel = [row[0] for row in observedWaterLevel]
        observedWaterLevel = [row[1] for row in observedWaterLevel]

        datesSensorWaterLevel = [row[0] for row in sensorWaterLevel]
        sensorWaterLevel = [row[1] for row in sensorWaterLevel]

        dates = []
        waterLevel = []

        for i in range(0, len(datesObservedWaterLevel) - 1):
            year = int(datesObservedWaterLevel[i][0:4])
            month = int(datesObservedWaterLevel[i][5:7])
            day = int(datesObservedWaterLevel[i][8:10])
            hh = int(datesObservedWaterLevel[i][11:13])
            mm = int(datesObservedWaterLevel[i][14:16])
            dates.append(dt.datetime(year, month, day, hh, mm))
            waterLevel.append(observedWaterLevel[i])

        datesObservedWaterLevel = dates
        observedWaterLevel = waterLevel

        dates = []
        waterLevel = []

        for i in range(0, len(datesSensorWaterLevel) - 1):
            year = int(datesSensorWaterLevel[i][0:4])
            month = int(datesSensorWaterLevel[i][5:7])
            day = int(datesSensorWaterLevel[i][8:10])
            hh = int(datesSensorWaterLevel[i][11:13])
            mm = int(datesSensorWaterLevel[i][14:16])
            dates.append(dt.datetime(year, month, day, hh, mm))
            waterLevel.append(sensorWaterLevel[i])

        datesSensorWaterLevel = dates
        sensorWaterLevel = waterLevel

        observed_WL = go.Scatter(
            x=datesObservedWaterLevel,
            y=observedWaterLevel,
            name='Observed'
        )

        sensor_WL = go.Scatter(
            x=datesSensorWaterLevel,
            y=sensorWaterLevel,
            name='Sensor'
        )

        layout = go.Layout(title='Observed Water Level',
                           xaxis=dict(
                               title='Dates', ),
                           yaxis=dict(
                               title='Water Level (m)',
                               autorange=True),
                           showlegend=True)

        chart_obj = PlotlyView(
            go.Figure(data=[observed_WL, sensor_WL],
                      layout=layout)
        )

        context = {
            'gizmo_object': chart_obj,
        }

        return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'No  data found for the station.'})


def get_observed_waterlevel_csv(request):
    """
    Get data from fews stations
    """

    get_data = request.GET

    try:
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        url = 'http://fews.ideam.gov.co/colombia/jsonH/00' + codEstacion + 'Hobs.json'

        f = requests.get(url, verify=False)
        data = f.json()

        observedWaterLevel = (data.get('obs'))
        observedWaterLevel = (observedWaterLevel.get('data'))

        datesObservedWaterLevel = [row[0] for row in observedWaterLevel]
        observedWaterLevel = [row[1] for row in observedWaterLevel]

        dates = []
        waterLevel = []

        for i in range(0, len(datesObservedWaterLevel) - 1):
            year = int(datesObservedWaterLevel[i][0:4])
            month = int(datesObservedWaterLevel[i][5:7])
            day = int(datesObservedWaterLevel[i][8:10])
            hh = int(datesObservedWaterLevel[i][11:13])
            mm = int(datesObservedWaterLevel[i][14:16])
            dates.append(dt.datetime(year, month, day, hh, mm))
            waterLevel.append(observedWaterLevel[i])

        datesObservedWaterLevel = dates
        observedWaterLevel = waterLevel

        pairs = [list(a) for a in zip(datesObservedWaterLevel, observedWaterLevel)]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=observed_water_level_{0}_{1}.csv'.format(
            codEstacion, nomEstacion)

        writer = csv_writer(response)
        writer.writerow(['datetime', 'water level (m)'])

        for row_data in pairs:
            writer.writerow(row_data)

        return response

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'An unknown error occurred while retrieving the Water Level Data.'})


def get_sensor_waterlevel_csv(request):
    """
      Get data from fews stations
      """

    get_data = request.GET

    try:
        codEstacion = get_data['stationcode']
        nomEstacion = get_data['stationname']

        url = 'http://fews.ideam.gov.co/colombia/jsonH/00' + codEstacion + 'Hobs.json'

        f = requests.get(url, verify=False)
        data = f.json()

        sensorWaterLevel = (data.get('sen'))
        sensorWaterLevel = (sensorWaterLevel.get('data'))

        datesSensorWaterLevel = [row[0] for row in sensorWaterLevel]
        sensorWaterLevel = [row[1] for row in sensorWaterLevel]

        dates = []
        waterLevel = []

        for i in range(0, len(datesSensorWaterLevel) - 1):
            year = int(datesSensorWaterLevel[i][0:4])
            month = int(datesSensorWaterLevel[i][5:7])
            day = int(datesSensorWaterLevel[i][8:10])
            hh = int(datesSensorWaterLevel[i][11:13])
            mm = int(datesSensorWaterLevel[i][14:16])
            dates.append(dt.datetime(year, month, day, hh, mm))
            waterLevel.append(sensorWaterLevel[i])

        datesSensorWaterLevel = dates
        sensorWaterLevel = waterLevel

        pairs = [list(a) for a in zip(datesSensorWaterLevel, sensorWaterLevel)]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=sensor_water_level_{0}_{1}.csv'.format(
            codEstacion, nomEstacion)

        writer = csv_writer(response)
        writer.writerow(['datetime', 'water level (m)'])

        for row_data in pairs:
            writer.writerow(row_data)

        return response

    except Exception as e:
        print(str(e))
        return JsonResponse({'error': 'An unknown error occurred while retrieving the Water Level Data.'})
