from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import *
from django.http import HttpResponse, JsonResponse
from tethys_sdk.permissions import has_permission
from tethys_sdk.base import TethysAppBase
from tethys_sdk.gizmos import PlotlyView
from tethys_sdk.workspaces import app_workspace
import os
import requests
from requests.auth import HTTPBasicAuth
import json
import urllib.request
import urllib.error
import urllib.parse
import numpy as np
import netCDF4 as nc

from osgeo import ogr
from osgeo import osr
from csv import writer as csv_writer
import csv
import scipy.stats as sp
import datetime as dt
import ast
import plotly.graph_objs as go
import io
import pandas as pd
import geoglows
import hydrostats.data

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
							  options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf'), ('LIS-RAPID', 'lis')],
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
							  options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf'),
									   ('LIS-RAPID', 'lis'), ('HIWAT-RAPID', 'hiwat')],
							  initial=[init_model_val],
							  classes=hiddenAttr,
							  original=True)

	# uncomment for displaying watersheds in the SPT
	# res = requests.get(app.get_custom_setting('api_source') + '/apps/streamflow-prediction-tool/api/GetWatersheds/',
	#                    headers={'Authorization': 'Token ' + app.get_custom_setting('spt_token')})
	#
	# watershed_list_raw = json.loads(res.content)
	#
	# app.get_custom_setting('keywords').lower().replace(' ', '').split(',')
	# watershed_list = [value for value in watershed_list_raw if
	#                   any(val in value[0].lower().replace(' ', '') for
	#                       val in app.get_custom_setting('keywords').lower().replace(' ', '').split(','))]

	# Retrieve a geoserver engine and geoserver credentials.
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

	context = {
		"base_name": base_name,
		"model_input": model_input,
		"watershed_select": watershed_select,
		"zoom_info": zoom_info,
		"geoserver_endpoint": geoserver_endpoint,
		"defaultUpdateButton": defaultUpdateButton,
		"startdateobs": startdateobs,
		"enddateobs": enddateobs
	}

	return render(request, '{0}/ecmwf.html'.format(base_name), context)


def lis(request):
	default_model = app.get_custom_setting('default_model_type')
	init_model_val = request.GET.get('model', False) or default_model or 'Select Model'
	init_ws_val = app.get_custom_setting('default_watershed_name') or 'Select Watershed'

	model_input = SelectInput(display_text='',
							  name='model',
							  multiple=False,
							  options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf'),
									   ('LIS-RAPID', 'lis'), ('HIWAT-RAPID', 'hiwat')],
							  initial=[init_model_val],
							  original=True)

	watershed_list = [['Select Watershed', '']]

	if app.get_custom_setting('lis_path'):
		res = os.listdir(app.get_custom_setting('lis_path'))

		for i in res:
			feat_name = i.split('-')[0].replace('_', ' ').title() + ' (' + \
						i.split('-')[1].replace('_', ' ').title() + ')'
			if feat_name not in str(watershed_list):
				watershed_list.append([feat_name, i])

	# Add the default WS if present and not already in the list
	# Not sure if this will work with LIS type. Need to test it out.
	if default_model == 'LIS-RAPID' and init_ws_val and init_ws_val not in str(watershed_list):
		watershed_list.append([init_ws_val, init_ws_val])

	watershed_select = SelectInput(display_text='',
								   name='watershed',
								   options=watershed_list,
								   initial=[init_ws_val],
								   original=True,
								   attributes={'onchange': "javascript:view_watershed();"}
								   )

	zoom_info = TextInput(display_text='',
						  initial=json.dumps(app.get_custom_setting('zoom_info')),
						  name='zoom_info',
						  disabled=True)
	context = {
		"base_name": base_name,
		"model_input": model_input,
		"watershed_select": watershed_select,
		"zoom_info": zoom_info
	}

	return render(request, '{0}/lis.html'.format(base_name), context)


def hiwat(request):
	default_model = app.get_custom_setting('default_model_type')
	init_model_val = request.GET.get('model', False) or default_model or 'Select Model'
	init_ws_val = app.get_custom_setting('default_watershed_name') or 'Select Watershed'

	model_input = SelectInput(display_text='',
							  name='model',
							  multiple=False,
							  options=[('Select Model', ''), ('ECMWF-RAPID', 'ecmwf'),
									   ('LIS-RAPID', 'lis'), ('HIWAT-RAPID', 'hiwat')],
							  initial=[init_model_val],
							  original=True)

	watershed_list = [['Select Watershed', '']]

	if app.get_custom_setting('lis_path'):
		res = os.listdir(app.get_custom_setting('hiwat_path'))

		for i in res:
			feat_name = i.split('-')[0].replace('_', ' ').title() + ' (' + \
						i.split('-')[1].replace('_', ' ').title() + ')'
			if feat_name not in str(watershed_list):
				watershed_list.append([feat_name, i])

	# Add the default WS if present and not already in the list
	# Not sure if this will work with LIS type. Need to test it out.
	if default_model == 'HIWAT-RAPID' and init_ws_val and init_ws_val not in str(watershed_list):
		watershed_list.append([init_ws_val, init_ws_val])

	watershed_select = SelectInput(display_text='',
								   name='watershed',
								   options=watershed_list,
								   initial=[init_ws_val],
								   original=True,
								   attributes={'onchange': "javascript:view_watershed();"}
								   )

	zoom_info = TextInput(display_text='',
						  initial=json.dumps(app.get_custom_setting('zoom_info')),
						  name='zoom_info',
						  disabled=True)
	context = {
		"base_name": base_name,
		"model_input": model_input,
		"watershed_select": watershed_select,
		"zoom_info": zoom_info
	}

	return render(request, '{0}/hiwat.html'.format(base_name), context)

@app_workspace
def get_warning_points(request,app_workspace):
	get_data = request.GET
	colombia_id_path = os.path.join(app_workspace.path,'colombia_reachids.csv')
	reach_pds = pd.read_csv(colombia_id_path)
	reach_ids_list = reach_pds['COMID'].tolist()
	# print("REACH_PDS")
	# print(reach_ids_list)
	if get_data['model'] == 'ECMWF-RAPID':
		try:
			watershed = get_data['watershed']
			subbasin = get_data['subbasin']

			res = requests.get(app.get_custom_setting('api_source') + '/api/ForecastWarnings/?region=' + watershed + '-' + 'geoglows'+ '&return_format=csv', verify = False).content
			print(app.get_custom_setting('api_source') + '/api/ForecastWarnings/?region=' + watershed + '-' + 'geoglows'+ '&return_format=csv')
			# print(res)
			# https://geoglows.ecmwf.int/api/ForecastWarnings/?region=south_america-geoglows&return_format=csv
			res_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
			cols = ['date_exceeds_return_period_2', 'date_exceeds_return_period_5', 'date_exceeds_return_period_10','date_exceeds_return_period_25', 'date_exceeds_return_period_50','date_exceeds_return_period_100']
			res_df["rp_all"] = res_df[cols].apply(lambda x: ','.join(x.replace(np.nan,'0')), axis=1)
			print(res_df)
			test_list = res_df["rp_all"].tolist()
			# print(test_list)
			final_new_rp = []
			for term in test_list:
				new_rp =[]
				terms = term.split(',')
				for te in terms:
					if te is not '0':
						# print('yeah')
						new_rp.append(1)
					else:
						new_rp.append(0)
				final_new_rp.append(new_rp)

			res_df['rp_all2'] = final_new_rp
			print("ANTES")
			print(res_df.head())
			res_df = res_df.reset_index()
			res_df = res_df[res_df['comid'].isin(reach_ids_list)]
			# res_df['rp_all'] = res_df['rp_all'].where(res_df['rp_all'] != '0', '1')
			# res_df = pd.read_csv(io.StringIO(res), index_col=0)
			d_2 = []
			d_5 = []
			d_10 = []
			d_50 = []
			d_100 = []

			d = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat':res_df['stream_lat'].tolist(),'lon':res_df['stream_lon'].tolist()}
			df_final = pd.DataFrame(data=d)
			# 'rep':res_df['rp_all2'].tolist()
			df_final[['rp_2','rp_5','rp_10','rp_25','rp_50','rp_100']] = pd.DataFrame(res_df.rp_all2.tolist(), index= df_final.index)
			d2 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat':res_df['stream_lat'].tolist(),'lon':res_df['stream_lon'].tolist(),'rp':df_final['rp_2']}
			d5 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat':res_df['stream_lat'].tolist(),'lon':res_df['stream_lon'].tolist(),'rp':df_final['rp_5']}
			d10 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat':res_df['stream_lat'].tolist(),'lon':res_df['stream_lon'].tolist(),'rp':df_final['rp_10']}
			d25 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat':res_df['stream_lat'].tolist(),'lon':res_df['stream_lon'].tolist(),'rp':df_final['rp_25']}
			d50 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat':res_df['stream_lat'].tolist(),'lon':res_df['stream_lon'].tolist(),'rp':df_final['rp_50']}
			d100 = {'comid': res_df['comid'].tolist(), 'stream_order': res_df['stream_order'].tolist(), 'lat':res_df['stream_lat'].tolist(),'lon':res_df['stream_lon'].tolist(),'rp':df_final['rp_100']}
			print("DESPUES")
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

			print(df_final_2)
			print(df_final_5)
			print(df_final_10)
			print(df_final_25)
			print(df_final_50)
			print(df_final_100)

			# res20 = requests.get(
			# 	app.get_custom_setting(
			# 		'api_source') + '/apps/streamflow-prediction-tool/api/GetWarningPoints/?watershed_name=' +
			# 	watershed + '&subbasin_name=' + subbasin + '&return_period=20',
			# 	headers={'Authorization': 'Token ' + app.get_custom_setting('spt_token')})
			#
			# res10 = requests.get(
			# 	app.get_custom_setting(
			# 		'api_source') + '/apps/streamflow-prediction-tool/api/GetWarningPoints/?watershed_name=' +
			# 	watershed + '&subbasin_name=' + subbasin + '&return_period=10',
			# 	headers={'Authorization': 'Token ' + app.get_custom_setting('spt_token')})
			#
			# res2 = requests.get(
			# 	app.get_custom_setting(
			# 		'api_source') + '/apps/streamflow-prediction-tool/api/GetWarningPoints/?watershed_name=' +
			# 	watershed + '&subbasin_name=' + subbasin + '&return_period=2',
			# 	headers={'Authorization': 'Token ' + app.get_custom_setting('spt_token')})

			return JsonResponse({
				"success": "Data analysis complete!",
				# "warning20": json.loads(res20.content)["features"],
				# "warning10": json.loads(res10.content)["features"],
				# "warning2": json.loads(res2.content)["features"]
			})
		except Exception as e:
			print(str(e))
			return JsonResponse({'error': 'No data found for the selected reach.'})
	else:
		pass


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
			res = requests.get(
				app.get_custom_setting('api_source') + '/api/ForecastStats/?reach_id=' + comid + '&date=' + startdate + '&return_format=csv',
				verify=False).content
		else:
			res = requests.get(
				app.get_custom_setting('api_source') + '/api/ForecastStats/?reach_id=' + comid + '&return_format=csv',
				verify=False).content


		stats_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
		stats_df.index = pd.to_datetime(stats_df.index)
		stats_df[stats_df < 0] = 0
		stats_df.index = stats_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
		stats_df.index = pd.to_datetime(stats_df.index)

		hydroviewer_figure = geoglows.plots.forecast_stats(stats=stats_df, titles={'Reach ID': comid})

		x_vals = (stats_df.index[0], stats_df.index[len(stats_df.index) - 1], stats_df.index[len(stats_df.index) - 1], stats_df.index[0])
		max_visible = max(stats_df.max())

		'''Getting Forecast Records'''
		res = requests.get(
			app.get_custom_setting('api_source') + '/api/ForecastRecords/?reach_id=' + comid + '&return_format=csv',
			verify=False).content

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

			x_vals = (records_df.index[0], stats_df.index[len(stats_df.index) - 1], stats_df.index[len(stats_df.index) - 1], records_df.index[0])
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

		hydroviewer_figure.add_trace(template('Return Periods', (r100 * 0.05, r100 * 0.05, r100 * 0.05, r100 * 0.05), 'rgba(0,0,0,0)', fill='none'))
		hydroviewer_figure.add_trace(template(f'2 Year: {r2}', (r2, r2, r5, r5), colors['2 Year']))
		hydroviewer_figure.add_trace(template(f'5 Year: {r5}', (r5, r5, r10, r10), colors['5 Year']))
		hydroviewer_figure.add_trace(template(f'10 Year: {r10}', (r10, r10, r25, r25), colors['10 Year']))
		hydroviewer_figure.add_trace(template(f'25 Year: {r25}', (r25, r25, r50, r50), colors['25 Year']))
		hydroviewer_figure.add_trace(template(f'50 Year: {r50}', (r50, r50, r100, r100), colors['50 Year']))
		hydroviewer_figure.add_trace(template(f'100 Year: {r100}', (r100, r100, max(r100 + r100 * 0.05, max_visible), max(r100 + r100 * 0.05, max_visible)), colors['100 Year']))

		hydroviewer_figure['layout']['xaxis'].update(autorange=True);

		chart_obj = PlotlyView(hydroviewer_figure)

		context = {
			'gizmo_object': chart_obj,
		}

		return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No data found for the selected reach.'})


def get_available_dates(request):
	get_data = request.GET

	watershed = get_data['watershed']
	subbasin = get_data['subbasin']
	comid = get_data['comid']
	res = requests.get(app.get_custom_setting('api_source') + '/api/AvailableDates/?region=' + watershed + '-' + subbasin, verify=False)

	data = res.json()

	dates_array = (data.get('available_dates'))

	#print(dates_array)

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
	#print(dates)
	dates.reverse()
	#print(dates)

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

		era_res = requests.get(app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv', verify=False).content

		simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
		simulated_df[simulated_df < 0] = 0
		simulated_df.index = pd.to_datetime(simulated_df.index)
		simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
		simulated_df.index = pd.to_datetime(simulated_df.index)

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

		era_res = requests.get(app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv', verify=False).content

		simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
		simulated_df[simulated_df < 0] = 0
		simulated_df.index = pd.to_datetime(simulated_df.index)
		simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
		simulated_df.index = pd.to_datetime(simulated_df.index)

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

		era_res = requests.get(
			app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv',
			verify=False).content

		simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
		simulated_df[simulated_df < 0] = 0
		simulated_df.index = pd.to_datetime(simulated_df.index)
		simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
		simulated_df.index = pd.to_datetime(simulated_df.index)

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
		if get_data['startdate'] != '':
			startdate = get_data['startdate']
			res = requests.get(
				app.get_custom_setting(
					'api_source') + '/api/ForecastStats/?reach_id=' + comid + '&date=' + startdate + '&return_format=csv',
				verify=False).content
		else:
			res = requests.get(
				app.get_custom_setting('api_source') + '/api/ForecastStats/?reach_id=' + comid + '&return_format=csv',
				verify=False).content

		stats_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
		stats_df.index = pd.to_datetime(stats_df.index)
		stats_df[stats_df < 0] = 0
		stats_df.index = stats_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
		stats_df.index = pd.to_datetime(stats_df.index)

		init_time = stats_df.index[0]
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename=streamflow_forecast_{0}_{1}_{2}_{3}.csv'.format(watershed, subbasin, comid, init_time)

		stats_df.to_csv(encoding='utf-8', header=True, path_or_buf=response)

		return response

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No forecast data found.'})


def shp_to_geojson(request):
	get_data = request.GET

	try:
		model = get_data['model']
		watershed = get_data['watershed']
		subbasin = get_data['subbasin']

		driver = ogr.GetDriverByName('ESRI Shapefile')
		if model == 'LIS-RAPID':
			reprojected_shp_path = os.path.join(
				app.get_custom_setting('lis_path'),
				'-'.join([watershed, subbasin]).replace(' ', '_'),
				'-'.join([watershed, subbasin, 'drainage_line']).replace(' ', '_'),
				'-'.join([watershed, subbasin, 'drainage_line', '3857.shp']).replace(' ', '_')
			)
		elif model == 'HIWAT-RAPID':
			reprojected_shp_path = os.path.join(
				app.get_custom_setting('hiwat_path'),
				'-'.join([watershed, subbasin]).replace(' ', '_'),
				'-'.join([watershed, subbasin, 'drainage_line']).replace(' ', '_'),
				'-'.join([watershed, subbasin, 'drainage_line', '3857.shp']).replace(' ', '_')
			)

		if not os.path.exists(reprojected_shp_path):

			raw_shp_path = reprojected_shp_path.replace('-3857', '')

			raw_shp_src = driver.Open(raw_shp_path)
			raw_shp = raw_shp_src.GetLayer()

			in_prj = raw_shp.GetSpatialRef()

			out_prj = osr.SpatialReference()

			out_prj.ImportFromWkt(
				"""
				PROJCS["WGS 84 / Pseudo-Mercator",
					GEOGCS["WGS 84",
						DATUM["WGS_1984",
							SPHEROID["WGS 84",6378137,298.257223563,
								AUTHORITY["EPSG","7030"]],
							AUTHORITY["EPSG","6326"]],
						PRIMEM["Greenwich",0,
							AUTHORITY["EPSG","8901"]],
						UNIT["degree",0.0174532925199433,
							AUTHORITY["EPSG","9122"]],
						AUTHORITY["EPSG","4326"]],
					PROJECTION["Mercator_1SP"],
					PARAMETER["central_meridian",0],
					PARAMETER["scale_factor",1],
					PARAMETER["false_easting",0],
					PARAMETER["false_northing",0],
					UNIT["metre",1,
						AUTHORITY["EPSG","9001"]],
					AXIS["X",EAST],
					AXIS["Y",NORTH],
					EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs"],
					AUTHORITY["EPSG","3857"]]
				"""
			)

			coordTrans = osr.CoordinateTransformation(in_prj, out_prj)

			reprojected_shp_src = driver.CreateDataSource(reprojected_shp_path)
			reprojected_shp = reprojected_shp_src.CreateLayer('-'.join([watershed, subbasin,
																		'drainage_line', '3857']).encode('utf-8'),
															  geom_type=ogr.wkbLineString)

			raw_shp_lyr_def = raw_shp.GetLayerDefn()
			for i in range(0, raw_shp_lyr_def.GetFieldCount()):
				field_def = raw_shp_lyr_def.GetFieldDefn(i)
				if field_def.name in ['COMID', 'watershed', 'subbasin']:
					reprojected_shp.CreateField(field_def)

			# get the output layer's feature definition
			reprojected_shp_lyr_def = reprojected_shp.GetLayerDefn()

			# loop through the input features
			in_feature = raw_shp.GetNextFeature()
			while in_feature:
				# get the input geometry
				geom = in_feature.GetGeometryRef()
				# reproject the geometry
				geom.Transform(coordTrans)
				# create a new feature
				out_feature = ogr.Feature(reprojected_shp_lyr_def)
				# set the geometry and attribute
				out_feature.SetGeometry(geom)
				out_feature.SetField('COMID', in_feature.GetField(in_feature.GetFieldIndex('COMID')))
				# out_feature.SetField('watershed', in_feature.GetField(in_feature.GetFieldIndex('watershed')))
				# out_feature.SetField('subbasin', in_feature.GetField(in_feature.GetFieldIndex('subbasin')))
				# add the feature to the shapefile
				reprojected_shp.CreateFeature(out_feature)
				# dereference the features and get the next input feature
				out_feature = None
				in_feature = raw_shp.GetNextFeature()

			fc = {
				'type': 'FeatureCollection',
				'features': []
			}

			for feature in reprojected_shp:
				fc['features'].append(feature.ExportToJson(as_object=True))

			with open(reprojected_shp_path.replace('.shp', '.json'), 'w') as f:
				json.dump(fc, f)

			# Save and close the shapefiles
			raw_shp_src = None
			reprojected_shp_src = None

		shp_src = driver.Open(reprojected_shp_path)
		shp = shp_src.GetLayer()

		extent = list(shp.GetExtent())
		xmin, ymin, xmax, ymax = extent[0], extent[2], extent[1], extent[3]

		with open(reprojected_shp_path.replace('.shp', '.json'), 'r') as f:
			geojson_streams = json.load(f)

			geojson_layer = {
				'source': 'GeoJSON',
				'options': json.dumps(geojson_streams),
				'legend_title': '-'.join([watershed, subbasin, 'drainage_line']),
				'legend_extent': [xmin, ymin, xmax, ymax],
				'legend_extent_projection': 'EPSG:3857',
				'feature_selection': True
			}

			return JsonResponse(geojson_layer)

	except Exception as e:
		print(str(e))
		return JsonResponse({'error': 'No shapefile found.'})


def get_daily_seasonal_streamflow_chart(request):
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

		 era_res = requests.get(
			 app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv',
			 verify=False).content

		 simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
		 simulated_df[simulated_df < 0] = 0
		 simulated_df.index = pd.to_datetime(simulated_df.index)
		 simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
		 simulated_df.index = pd.to_datetime(simulated_df.index)

		 dayavg_df = hydrostats.data.daily_average(simulated_df, rolling=True)

		 hydroviewer_figure = geoglows.plots.daily_averages(dayavg_df, titles={'Reach ID': comid})

		 chart_obj = PlotlyView(hydroviewer_figure)

		 context = {
			 'gizmo_object': chart_obj,
		}

		 return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

	 except Exception as e:
		 print(str(e))
		 return JsonResponse({'error': 'No historic data found for calculating flow duration curve.'})


def get_monthly_seasonal_streamflow_chart(request):
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

		 era_res = requests.get(
			 app.get_custom_setting('api_source') + '/api/HistoricSimulation/?reach_id=' + comid + '&return_format=csv',
			 verify=False).content

		 simulated_df = pd.read_csv(io.StringIO(era_res.decode('utf-8')), index_col=0)
		 simulated_df[simulated_df < 0] = 0
		 simulated_df.index = pd.to_datetime(simulated_df.index)
		 simulated_df.index = simulated_df.index.to_series().dt.strftime("%Y-%m-%d")
		 simulated_df.index = pd.to_datetime(simulated_df.index)

		 monavg_df = hydrostats.data.monthly_average(simulated_df)

		 hydroviewer_figure = geoglows.plots.daily_averages(monavg_df, titles={'Reach ID': comid})

		 chart_obj = PlotlyView(hydroviewer_figure)

		 context = {
			 'gizmo_object': chart_obj,
		}

		 return render(request, '{0}/gizmo_ajax.html'.format(base_name), context)

	 except Exception as e:
		 print(str(e))
		 return JsonResponse({'error': 'No historic data found for calculating flow duration curve.'})


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

		'''Getting Forecast Stats'''
		if get_data['startdate'] != '':
			startdate = get_data['startdate']
			res = requests.get(
				app.get_custom_setting(
					'api_source') + '/api/ForecastStats/?reach_id=' + comid + '&date=' + startdate + '&return_format=csv',
				verify=False).content

			ens = requests.get(
				app.get_custom_setting(
					'api_source') + '/api/ForecastEnsembles/?reach_id=' + comid + '&date=' + startdate + '&ensemble=all&return_format=csv',
				verify=False).content

		else:
			res = requests.get(
				app.get_custom_setting('api_source') + '/api/ForecastStats/?reach_id=' + comid + '&return_format=csv',
				verify=False).content

			ens = requests.get(
				app.get_custom_setting('api_source') + '/api/ForecastEnsembles/?reach_id=' + comid + '&ensemble=all&return_format=csv',
				verify=False).content

		stats_df = pd.read_csv(io.StringIO(res.decode('utf-8')), index_col=0)
		stats_df.index = pd.to_datetime(stats_df.index)
		stats_df[stats_df < 0] = 0
		stats_df.index = stats_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
		stats_df.index = pd.to_datetime(stats_df.index)

		ensemble_df = pd.read_csv(io.StringIO(ens.decode('utf-8')), index_col=0)
		ensemble_df.index = pd.to_datetime(ensemble_df.index)
		ensemble_df[ensemble_df < 0] = 0
		ensemble_df.index = ensemble_df.index.to_series().dt.strftime("%Y-%m-%d %H:%M:%S")
		ensemble_df.index = pd.to_datetime(ensemble_df.index)

		'''Getting Return Periods'''
		res = requests.get(
			app.get_custom_setting('api_source') + '/api/ReturnPeriods/?reach_id=' + comid + '&return_format=csv',
			verify=False).content
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
