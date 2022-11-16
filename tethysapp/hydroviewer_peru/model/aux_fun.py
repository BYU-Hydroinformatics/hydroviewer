def get_zoom_coords(df, lat='Latitude', lon='Longitude'):

    threshold = 0.05
    df[lat] = df[lat].astype(float)
    df[lon] = df[lon].astype(float)


    min_lat = df[lat].min() - threshold
    max_lat = df[lat].max() + threshold

    min_lon = df[lon].min() - threshold
    max_lon = df[lon].max() + threshold

    lat_coord = [min_lat, max_lat, min_lat, max_lat]
    lon_coord = [min_lon, min_lon, max_lon, max_lon]
    return lat_coord, lon_coord