import os
import json
import numpy as np
import pandas as pd

import json
import pandas as pd
import numpy as np

from .aux_fun import *


class Stations_manage:
	def __init__(self, dir_path): 
		"""
		Station manage object
		"""
		# Load static attibute
		self.dir_path = dir_path
		self.save_path = os.sep.join(dir_path.split(os.sep)[:-1])
		self.gnrl_dict = {"columns int search" : ['CodEstacao'],
						  "columns str search" : ['NomeEstaca', 'NomeRio'],
						  "columns coords" : ['Latitude', 'Longitude'],
						}
		self.full_data = self.read_file()
		
		# Internal methods to work
		self.__fix_columns_data__()

		# Slice full dataframe
		self.data = self.full_data[self.gnrl_dict["columns int search"] + self.gnrl_dict["columns str search"] + self.gnrl_dict["columns coords"]].copy()
		self.data.reset_index(inplace=True)
		self.data.rename(columns={'index':'ID_tmp'}, inplace=True)

		# App method - Extract search list
		self.__extract_search_list__()


	def __call__(self, search_id: str):
		'''
        Input: 
            search_data : str = value to search
		'''

		# Extract coords of the station
		coords = self.__coordssearch__(search_id)

        # Assert does not existence of the station
		if len(coords) < 1:
			return 'COLOMBIA.json', coords, 404, '', ''

        # Extract coords of the polygon
		lat_coord, lon_coord = get_zoom_coords(df=coords, lat='Latitude', lon='Longitude')

        # Build station output file
		output_station_file, station_file_cont = self.__printstaiongeojson__(df=coords)

        # Build coundary output file
		output_file, boundary_file_cont = self.__printgeojson__(lat_coord=lat_coord, lon_coord=lon_coord)

		return output_file, output_station_file, 200, station_file_cont, boundary_file_cont


	# Get methods
	def get_search_list(self):
		return self.__search_list__


	# Methoda
	def read_file(self):
		data = json.load(open(self.dir_path))['features']
		df = pd.DataFrame()
		for line in data:
			line_data = line['properties']
			col_names = list(line_data.keys())
			col_data = [line_data[ii] for ii in col_names]
			tmp = pd.DataFrame(data= [col_data],
							   columns=col_names)
			df = pd.concat([df, tmp], ignore_index=True)

		for column in df.columns:
			df[column] = df[column].astype(str)

		return df


	# Hidden methods
	def __extract_search_list__(self):
		rv = self.full_data[self.gnrl_dict['columns int search'] + self.gnrl_dict['columns str search']].copy()
		rv = np.unique(rv.values.ravel('F'))
		self.__search_list__ = rv.tolist()


	def __fix_columns_data__(self):
		# Change for str columns
		for col_name in self.gnrl_dict['columns str search']:
			self.full_data[col_name] = self.full_data[col_name].str.lower()
			self.full_data[col_name] = list(map(lambda x: x.replace('á', 'a'), self.full_data[col_name]))
			self.full_data[col_name] = list(map(lambda x: x.replace('é', 'e'), self.full_data[col_name]))
			self.full_data[col_name] = list(map(lambda x: x.replace('í', 'i'), self.full_data[col_name]))
			self.full_data[col_name] = list(map(lambda x: x.replace('ó', 'o'), self.full_data[col_name]))
			self.full_data[col_name] = list(map(lambda x: x.replace('ú', 'u'), self.full_data[col_name]))
			self.full_data[col_name] = list(map(lambda x: x.replace('ñ', 'n'), self.full_data[col_name]))
			self.full_data[col_name] = self.full_data[col_name].str.upper()
			self.full_data[col_name] = self.full_data[col_name].str.lstrip()
			self.full_data[col_name] = self.full_data[col_name].str.rstrip()

		# Change for int columns
		for col_name in self.gnrl_dict['columns int search']:
			self.full_data[col_name] = list(map(lambda x : str(int(float(x))), self.full_data[col_name]))


	def __coordssearch__(self, search_id):

		# Identify type of input
		try:
			# Search by code
			seach_case = 'int'
			search_id = str(int(search_id))
			columns_to_search = self.gnrl_dict['columns int search']
		except:
			# Search by name
			search_case = 'name'
			search_id = str(search_id).upper()
			columns_to_search = self.gnrl_dict['columns str search']

        
        # Extract column to search
		search_df = pd.DataFrame()
		for col in columns_to_search:
			tmp_df = pd.DataFrame()
			tmp_df['ID_tmp'] = self.data['ID_tmp']

           
			if seach_case == 'int':
				tmp_df['values'] = self.data[col].astype(str)
			elif seach_case == 'str':
				# TODO: Add decodifficator for spañish when by name is used
				tmp_df['values'] = self.data[col].astype(str)
			else:
				# TODO: Add search by lat,lon
				pass

			search_df = pd.concat([search_df, tmp_df], ignore_index=True)

		idtmp_to_search = search_df.loc[search_df['values'] == search_id]

		valids = self.data[columns_to_search].isin(idtmp_to_search['values'].values).values
		rv = self.data.loc[valids].copy()

		return rv


	def __printstaiongeojson__(self, df):

		lon = self.gnrl_dict['columns coords'][1]
		lat = self.gnrl_dict['columns coords'][0]

		# TODO: Add variable name file for multyple user. And remove path
		# pathdir and name file
		# file_name = str(uuid.uuid4()) + '.json'
		file_name = 'station_geojson' + '.json'
		file_path = os.sep.join([self.save_path, file_name])


		# Build json
		feature = []
		for _, row in df.iterrows():
			feature.append({'type' : "Feature",
							"geometry" : {"type" : "Point",
										  "coordinates":[row[lon], row[lat]]}})
		json_file = {"type" : "FeatureCollection",
					 "features" : feature}


		with open(file_path, 'w', encoding='utf-8') as f:
			json.dump(json_file, f, ensure_ascii=False, indent=4)

		return file_name, json_file


	def __printgeojson__(self, lat_coord, lon_coord):
        
		# TODO: Add variable name file for multyple user. And remove path
		# pathdir and name file
		# file_name = str(uuid.uuid4()) + '.json'
		file_name = 'boundary_geojson' + '.json'
		file_path = os.sep.join([self.save_path, file_name])

		# Print json
		json_file = {"type":"FeatureCollection", 
                    "features": [{ "type" : "Feature",
                                   "geometry" : { "type"       : "Polygon",
                                                  "coordinates" : [[[lon_coord[0], lat_coord[0]],
                                                                    [lon_coord[1], lat_coord[1]],
                                                                    [lon_coord[3], lat_coord[3]],
                                                                    [lon_coord[2], lat_coord[2]]]]
                                                }
                                }]
                    }


		with open(file_path, 'w', encoding='utf-8') as f:
			json.dump(json_file, f, ensure_ascii=False, indent=4)

		return file_name, json_file
