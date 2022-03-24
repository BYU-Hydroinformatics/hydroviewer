/* Global Variables */
var default_extent,
    current_layer,
    current_feature,
    feature_layer,
    stream_geom,
    layers,
    wmsLayer,
    wmsLayer2,
    vectorLayer,
    feature,
    featureOverlay,
    forecastFolder,
    select_interaction,
    two_year_warning,
    five_year_warning,
    ten_year_warning,
    twenty_five_year_warning,
    fifty_year_warning,
    hundred_year_warning,
    map,
    wms_layers;


var $loading = $('#view-file-loading');
var m_downloaded_historical_streamflow = false;
var m_downloaded_flow_duration = false;

const glofasURL = `http://globalfloods-ows.ecmwf.int/glofas-ows/ows.py`

//create symbols for warnings
var hundred_symbols = [new ol.style.RegularShape({
    points: 3,
    radius: 5,
    fill: new ol.style.Fill({
        color: 'rgba(128,0,246,0.6)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(128,0,246,1)',
        width: 1
    })
}), new ol.style.RegularShape({
    points: 3,
    radius: 9,
    fill: new ol.style.Fill({
        color: 'rgba(128,0,246,1)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(128,0,246,0.4)',
        width: 1
    })
})];

var fifty_symbols = [new ol.style.RegularShape({
    points: 3,
    radius: 5,
    fill: new ol.style.Fill({
        color: 'rgba(128,0,106,0.6)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(128,0,106,1)',
        width: 1
    })
}), new ol.style.RegularShape({
    points: 3,
    radius: 9,
    fill: new ol.style.Fill({
        color: 'rgba(128,0,106,1)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(128,0,106,0.4)',
        width: 1
    })
})];

var twenty_five_symbols = [new ol.style.RegularShape({
    points: 3,
    radius: 5,
    fill: new ol.style.Fill({
        color: 'rgba(255,0,0,0.6)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(255,0,0,1)',
        width: 1
    })
}), new ol.style.RegularShape({
    points: 3,
    radius: 9,
    fill: new ol.style.Fill({
        color: 'rgba(255,0,0,1)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(255,0,0,0.4)',
        width: 1
    })
})];

//symbols
var ten_symbols = [new ol.style.RegularShape({
    points: 3,
    radius: 5,
    fill: new ol.style.Fill({
        color: 'rgba(255,56,5,0.6)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(255,56,5,1)',
        width: 1
    })
}), new ol.style.RegularShape({
    points: 3,
    radius: 9,
    fill: new ol.style.Fill({
        color: 'rgba(255,56,5,1)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(255,56,5,0.4)',
        width: 1
    })
})];

var five_symbols = [new ol.style.RegularShape({
    points: 3,
    radius: 5,
    fill: new ol.style.Fill({
        color: 'rgba(253,154,1,0.6)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(253,154,1,1)',
        width: 1
    })
}), new ol.style.RegularShape({
    points: 3,
    radius: 9,
    fill: new ol.style.Fill({
        color: 'rgba(253,154,1,1)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(253,154,1,0.4)',
        width: 1
    })
})];

//symbols
var two_symbols = [new ol.style.RegularShape({
    points: 3,
    radius: 5,
    fill: new ol.style.Fill({
        color: 'rgba(254,240,1,0.6)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(254,240,1,1)',
        width: 1
    })
}), new ol.style.RegularShape({
    points: 3,
    radius: 9,
    fill: new ol.style.Fill({
        color: 'rgba(254,240,1,0.4)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(254,240,1,1)',
        width: 1
    })
})];


function toggleAcc(layerID) {
    let layer = wms_layers[layerID];
    if (document.getElementById(`wmsToggle${layerID}`).checked) {
        // Turn the layer and legend on
        layer.setVisible(true);
        $("#wmslegend" + layerID).show(200);
    } else {
        layer.setVisible(false);
        $("#wmslegend" + layerID).hide(200);

    }
}



function init_map() {
    var base_layer = new ol.layer.Tile({
        source: new ol.source.BingMaps({
            key: 'eLVu8tDRPeQqmBlKAjcw~82nOqZJe2EpKmqd-kQrSmg~AocUZ43djJ-hMBHQdYDyMbT-Enfsk0mtUIGws1WeDuOvjY4EXCH-9OK3edNLDgkc',
            imagerySet: 'Road'
            //            imagerySet: 'AerialWithLabels'
        })
    });


    wms_layers = [
        new ol.layer.Tile({
            source: new ol.source.TileWMS({
                url: glofasURL,
                params: { LAYERS: 'AccRainEGE', TILED: true },
                serverType: 'mapserver'
                // crossOrigin: 'Anonymous'
            }),
            visible: false
        }),
        new ol.layer.Tile({
            source: new ol.source.TileWMS({
                url: glofasURL,
                params: { LAYERS: 'EGE_probRgt50', TILED: true },
                serverType: 'mapserver'
                // crossOrigin: 'Anonymous'
            }),
            visible: false
        }),
        new ol.layer.Tile({
            source: new ol.source.TileWMS({
                url: glofasURL,
                params: { LAYERS: 'EGE_probRgt150', TILED: true },
                serverType: 'mapserver'
                // crossOrigin: 'Anonymous'
            }),
            visible: false
        }),
        new ol.layer.Tile({
            source: new ol.source.TileWMS({
                url: glofasURL,
                params: { LAYERS: 'EGE_probRgt300', TILED: true },
                serverType: 'mapserver'
                // crossOrigin: 'Anonymous'
            }),
            visible: false
        })
    ];


    featureOverlay = new ol.layer.Vector({
        source: new ol.source.Vector()
    });

    two_year_warning = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            image: new ol.style.RegularShape({
                fill: new ol.style.Fill({ color: 'rgba(254,240,1,1)' }),
                stroke: new ol.style.Stroke({ color: 'black', width: 0.5 }),
                points: 3,
                radius: 10,
                angle: 0
            })
        })
    });

    five_year_warning = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            image: new ol.style.RegularShape({
                fill: new ol.style.Fill({ color: 'rgba(253,154,1,1)' }),
                stroke: new ol.style.Stroke({ color: 'black', width: 0.5 }),
                points: 3,
                radius: 10,
                angle: 0
            })
        })
    });

    ten_year_warning = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            image: new ol.style.RegularShape({
                fill: new ol.style.Fill({ color: 'rgba(255,56,5,1)' }),
                stroke: new ol.style.Stroke({ color: 'black', width: 0.5 }),
                points: 3,
                radius: 10,
                angle: 0
            })
        })
    });

    twenty_five_year_warning = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            image: new ol.style.RegularShape({
                fill: new ol.style.Fill({ color: 'rgba(255,0,0,1)' }),
                stroke: new ol.style.Stroke({ color: 'black', width: 0.5 }),
                points: 3,
                radius: 10,
                angle: 0
            })
        })
    });

    fifty_year_warning = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            image: new ol.style.RegularShape({
                fill: new ol.style.Fill({ color: 'rgba(128,0,106,1)' }),
                stroke: new ol.style.Stroke({ color: 'black', width: 0.5 }),
                points: 3,
                radius: 10,
                angle: 0
            })
        })
    });

    hundred_year_warning = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            image: new ol.style.RegularShape({
                fill: new ol.style.Fill({ color: 'rgba(128,0,246,1)' }),
                stroke: new ol.style.Stroke({ color: 'black', width: 0.5 }),
                points: 3,
                radius: 10,
                angle: 0
            })
        })
    });


    if ($('#model option:selected').text() === 'ECMWF-RAPID') {
        var wmsLayer = new ol.layer.Image({
            source: new ol.source.ImageWMS({
                url: JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "") + '/wms',
                params: { 'LAYERS': 'province_boundaries' },
                serverType: 'geoserver',
                crossOrigin: 'Anonymous'
            })
        });

        layers = [base_layer, two_year_warning, five_year_warning, ten_year_warning, twenty_five_year_warning, fifty_year_warning, hundred_year_warning].concat(wms_layers).concat([wmsLayer, featureOverlay])
        // layers = [base_layer, two_year_warning, five_year_warning, ten_year_warning, twenty_five_year_warning, fifty_year_warning, hundred_year_warning].concat(wms_layers)
    } else {
        layers = [base_layer, two_year_warning, five_year_warning, ten_year_warning, twenty_five_year_warning, fifty_year_warning, hundred_year_warning].concat(wms_layers).concat([featureOverlay])
    }

    var lon = Number(JSON.parse($('#zoom_info').val()).split(',')[0]);
    var lat = Number(JSON.parse($('#zoom_info').val()).split(',')[1]);
    var zoomLevel = Number(JSON.parse($('#zoom_info').val()).split(',')[2]);
    map = new ol.Map({
        target: 'map',
        view: new ol.View({
            center: ol.proj.transform([lon, lat], 'EPSG:4326', 'EPSG:3857'),
            zoom: zoomLevel,
            minZoom: 2,
            maxZoom: 18,
        }),
        layers: layers
    });

    default_extent = map.getView().calculateExtent(map.getSize());

}

function view_watershed() {
    map.removeInteraction(select_interaction);
    map.removeLayer(wmsLayer);
    $("#get-started").modal('hide');
    if ($('#model option:selected').text() === 'ECMWF-RAPID' && $('#watershedSelect option:selected').val() !== "") {

        $("#watershed-info").empty();

        $('#dates').addClass('hidden');

        var workspace = JSON.parse($('#geoserver_endpoint').val())[1];
        var model = $('#model option:selected').text();
        var watershed = $('#watershedSelect option:selected').text().split(' (')[0].replace(' ', '_').toLowerCase();
        var subbasin = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '').toLowerCase();
        var watershed_display_name = $('#watershedSelect option:selected').text().split(' (')[0];
        var subbasin_display_name = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '');
        $("#watershed-info").append('<h3>Current Watershed: ' + watershed_display_name + '</h3><h5>Subbasin Name: ' + subbasin_display_name);

        var layerName = workspace + ':' + watershed + '-' + subbasin + '-geoglows-drainage_line';
        wmsLayer = new ol.layer.Image({
            source: new ol.source.ImageWMS({
                //url: JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "") + '/wms',
                url: 'https://geoserver.hydroshare.org/geoserver/HS-dd069299816c4f1b82cd1fb2d59ec0ab/wms',
                //params: { 'LAYERS': layerName },
                params: {'LAYERS': 'south_america-colombia-geoglows-drainage_line' },
                serverType: 'geoserver',
                crossOrigin: 'Anonymous'
            }),
            opacity: 0.4
        });
        feature_layer = wmsLayer;


        get_warning_points(model, watershed, subbasin);

        wmsLayer2 = new ol.layer.Image({
            source: new ol.source.ImageWMS({
                //url: JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "")+'/wms',
                url: 'https://geoserver.hydroshare.org/geoserver/HS-dd069299816c4f1b82cd1fb2d59ec0ab/wms',
                params: {'LAYERS':"FEWS_Stations_N"},
                serverType: 'geoserver',
                crossOrigin: 'Anonymous'
            }),
            opacity: 0.7
        });
        feature_layer2 = wmsLayer2;

        map.addLayer(wmsLayer);
        map.addLayer(wmsLayer2);

        $loading.addClass('hidden');
        //var ajax_url = JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "") + '/' + workspace + '/' + watershed + '-' + subbasin + '-drainage_line/wfs?request=GetCapabilities';
        var ajax_url = 'https://geoserver.hydroshare.org/geoserver/wfs?request=GetCapabilities';

        var capabilities = $.ajax(ajax_url, {
            type: 'GET',
            data: {
                service: 'WFS',
                version: '1.0.0',
                request: 'GetCapabilities',
                outputFormat: 'text/javascript'
            },
            success: function() {
                var x = capabilities.responseText
                    .split('<FeatureTypeList>')[1]
                    //.split(workspace + ':' + watershed + '-' + subbasin)[1]
                    .split('HS-dd069299816c4f1b82cd1fb2d59ec0ab:south_america-colombia-geoglows-drainage_line')[1]
                    .split('LatLongBoundingBox ')[1]
                    .split('/></FeatureType>')[0];

                var minx = Number(x.split('"')[1]);
                var miny = Number(x.split('"')[3]);
                var maxx = Number(x.split('"')[5]);
                var maxy = Number(x.split('"')[7]);
                var extent = ol.proj.transform([minx, miny], 'EPSG:4326', 'EPSG:3857').concat(ol.proj.transform([maxx, maxy], 'EPSG:4326', 'EPSG:3857'));

                map.getView().fit(extent, map.getSize())
            }
        });

    } else if ($('#model option:selected').text() === 'LIS-RAPID' && $('#watershedSelect option:selected').val() !== "") {
        $("#watershed-info").empty();

        $('#dates').addClass('hidden');

        var model = $('#model option:selected').text();
        var watershed = $('#watershedSelect option:selected').text().split(' (')[0].replace(' ', '_').toLowerCase();
        var subbasin = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '').toLowerCase();
        var watershed_display_name = $('#watershedSelect option:selected').text().split(' (')[0];
        var subbasin_display_name = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '');
        $("#watershed-info").append('<h3>Current Watershed: ' + watershed_display_name + '</h3><h5>Subbasin Name: ' + subbasin_display_name);

        var layerName = workspace + ':' + watershed + '-' + subbasin + '-drainage_line';
        $.ajax({
            type: 'GET',
            url: 'get-lis-shp/',
            dataType: 'json',
            data: {
                'model': model,
                'watershed': watershed,
                'subbasin': subbasin
            },
            beforeSend: function () {
                $('#featureLoader').show();
            },
            success: function(result) {
                wmsLayer = new ol.layer.Vector({
                    renderMode: 'image',
                    source: new ol.source.Vector({
                        features: (new ol.format.GeoJSON()).readFeatures(result.options)
                    }),
                    style: new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: 'blue',
                            width: 1
                        })
                    })
                });

                wmsLayer2 = new ol.layer.Image({
                	source: new ol.source.ImageWMS({
                		//url: JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "")+'/wms',
                		url: 'https://geoserver.hydroshare.org/geoserver/HS-dd069299816c4f1b82cd1fb2d59ec0ab/wms',
                		params: {'LAYERS':"FEWS_Stations_N"},
                		serverType: 'geoserver',
                		crossOrigin: 'Anonymous'
                	})
                });

                feature_layer2 = wmsLayer2;

                map.addLayer(wmsLayer);
                map.addLayer(wmsLayer2);

                feature_layer = wmsLayer;

                map.getView().fit(result.legend_extent, map.getSize())
            },
            complete: function(){
                $('#featureLoader').hide();
            }
        });

    } else if ($('#model option:selected').text() === 'HIWAT-RAPID' && $('#watershedSelect option:selected').val() !== "") {
        $("#watershed-info").empty();

        $('#dates').addClass('hidden');

        var model = $('#model option:selected').text();
        var watershed = $('#watershedSelect option:selected').text().split(' (')[0].replace(' ', '_').toLowerCase();
        var subbasin = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '').toLowerCase();
        var watershed_display_name = $('#watershedSelect option:selected').text().split(' (')[0];
        var subbasin_display_name = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '');
        $("#watershed-info").append('<h3>Current Watershed: ' + watershed_display_name + '</h3><h5>Subbasin Name: ' + subbasin_display_name);

        var layerName = workspace + ':' + watershed + '-' + subbasin + '-drainage_line';
        $.ajax({
            type: 'GET',
            url: 'get-hiwat-shp/',
            dataType: 'json',
            data: {
                'model': model,
                'watershed': watershed,
                'subbasin': subbasin
            },
            beforeSend: function () {
                $('#featureLoader').show();
            },
            success: function(result) {
                wmsLayer = new ol.layer.Vector({
                    renderMode: 'image',
                    source: new ol.source.Vector({
                        features: (new ol.format.GeoJSON()).readFeatures(result.options)
                    }),
                    style: new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: 'blue',
                            width: 1
                        })
                    })
                });

                wmsLayer2 = new ol.layer.Image({
                	source: new ol.source.ImageWMS({
                		//url: JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "")+'/wms',
                		url: 'https://geoserver.hydroshare.org/geoserver/HS-dd069299816c4f1b82cd1fb2d59ec0ab/wms',
                		params: {'LAYERS':"FEWS_Stations_N"},
                		serverType: 'geoserver',
                		crossOrigin: 'Anonymous'
                	})
                });

                feature_layer2 = wmsLayer2;

                map.addLayer(wmsLayer);
                map.addLayer(wmsLayer2);

                feature_layer = wmsLayer;

                map.getView().fit(result.legend_extent, map.getSize())
            },
            complete: function(){
                $('#featureLoader').hide();
            }
        });

    } else {

        map.updateSize();
        //map.removeInteraction(select_interaction);
        map.removeLayer(wmsLayer);
        map.getView().fit(default_extent, map.getSize());
    }
}

function get_warning_points(model, watershed, subbasin) {
    $.ajax({
        type: 'GET',
        url: 'get-warning-points/',
        dataType: 'json',
        data: {
            'model': model,
            'watershed': watershed,
            'subbasin': subbasin
        },
        error: function(error) {
            console.log(error);
        },
        success: function(result) {

            map.getLayers().item(1).getSource().clear();
            map.getLayers().item(2).getSource().clear();
            map.getLayers().item(3).getSource().clear();
            map.getLayers().item(4).getSource().clear();
            map.getLayers().item(5).getSource().clear();
            map.getLayers().item(6).getSource().clear();

            if (result.warning2 != 'undefined') {

                var warLen2 = result.warning2.length;
                for (var i = 0; i < warLen2; ++i) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning2[i][1],
                            result.warning2[i][0]
                        ],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: 40
                    });
                    map.getLayers().item(1).getSource().addFeature(feature);
                }
                map.getLayers().item(1).setVisible(false);
            }
            if (result.warning5 != 'undefined') {
                var warLen5 = result.warning5.length;
                for (var i = 0; i < warLen5; ++i) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning5[i][1],
                            result.warning5[i][0]
                        ],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: 40
                    });
                    map.getLayers().item(2).getSource().addFeature(feature);
                }
                map.getLayers().item(2).setVisible(false);
            }
            if (result.warning10 != 'undefined') {
                var warLen10 = result.warning10.length;
                for (var i = 0; i < warLen10; ++i) {
					var geometry = new ol.geom.Point(ol.proj.transform([result.warning10[i][1],
							result.warning10[i][0]
						],
						'EPSG:4326', 'EPSG:3857'));
					var feature = new ol.Feature({
						geometry: geometry,
						point_size: 40
				});
				map.getLayers().item(3).getSource().addFeature(feature);
                }
                map.getLayers().item(3).setVisible(false);

            }
            if (result.warning25 != 'undefined') {
                var warLen25 = result.warning25.length;
                for (var i = 0; i < warLen25; ++i) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning25[i][1],
                            result.warning25[i][0]
                        ],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: 40
                    });
                    map.getLayers().item(4).getSource().addFeature(feature);
                }
                map.getLayers().item(4).setVisible(false);
            }
            if (result.warning50 != 'undefined') {
                var warLen50 = result.warning50.length;
                for (var i = 0; i < warLen50; ++i) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning50[i][1],
                            result.warning50[i][0]
                        ],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: 40
                    });
                    map.getLayers().item(5).getSource().addFeature(feature);
                }
                map.getLayers().item(5).setVisible(false);
            }
            if (result.warning100 != 'undefined') {
                var warLen100 = result.warning100.length;
                for (var i = 0; i < warLen100; ++i) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning100[i][1],
                            result.warning100[i][0]
                        ],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: 40
                    });
                    map.getLayers().item(6).getSource().addFeature(feature);
                }
                map.getLayers().item(6).setVisible(false);
            }
        }
    });
}


function get_available_dates(model, watershed, subbasin, comid) {
    if (model === 'ECMWF-RAPID') {
        $.ajax({
            type: 'GET',
            url: 'get-available-dates/',
            dataType: 'json',
            data: {
                'watershed': watershed,
                'subbasin': subbasin,
                'comid': comid
            },
            error: function() {
                $('#dates').html(
                    '<p class="alert alert-danger" style="text-align: center"><strong>An error occurred while retrieving the available dates</strong></p>'
                );

                setTimeout(function() {
                    $('#dates').addClass('hidden')
                }, 5000);
            },
            success: function(dates) {
                datesParsed = JSON.parse(dates.available_dates);
                $('#datesSelect').empty();

                $.each(datesParsed, function(i, p) {
                    var val_str = p.slice(1).join();
                    $('#datesSelect').append($('<option></option>').val(val_str).html(p[0]));
                });

            }
        });
    }
}


function get_time_series(model, watershed, subbasin, comid, startdate) {
    $loading.removeClass('hidden');
    $('#long-term-chart').addClass('hidden');
    $('#dates').addClass('hidden');
    $.ajax({
        type: 'GET',
        url: 'get-time-series/',
        data: {
            'model': model,
            'watershed': watershed,
            'subbasin': subbasin,
            'comid': comid,
            'startdate': startdate
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the forecast</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function() {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function(data) {
            if (!data.error) {
                $('#dates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#long-term-chart').removeClass('hidden');
                $('#long-term-chart').html(data);

                //resize main graph
                Plotly.Plots.resize($("#long-term-chart .js-plotly-plot")[0]);

                var params = {
                    watershed_name: watershed,
                    subbasin_name: subbasin,
                    reach_id: comid,
                    startdate: startdate,
                };

                $('#submit-download-forecast').attr({
                    target: '_blank',
                    href: 'get-forecast-data-csv?' + jQuery.param(params)
                });

                $('#download_forecast').removeClass('hidden');

            } else if (data.error) {
                $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the forecast</strong></p>');
                $('#info').removeClass('hidden');

                setTimeout(function() {
                    $('#info').addClass('hidden')
                }, 5000);
            } else {
                $('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            }
        }
    });
}


function get_historic_data(model, watershed, subbasin, comid, startdate) {
    $('#his-view-file-loading').removeClass('hidden');
    m_downloaded_historical_streamflow = true;
    $.ajax({
        type: 'GET',
        url: 'get-historic-data',
        data: {
            'model': model,
            'watershed': watershed,
            'subbasin': subbasin,
            'comid': comid,
            'startdate': startdate
        },
        success: function(data) {
            if (!data.error) {
                $('#his-view-file-loading').addClass('hidden');
                $('#historical-chart').removeClass('hidden');
                $('#historical-chart').html(data);

                var params = {
                    watershed_name: watershed,
                    subbasin_name: subbasin,
                    reach_id: comid,
                    daily: false
                };

                $('#submit-download-5-csv').attr({
                    target: '_blank',
                    href: 'get-historic-data-csv?' + jQuery.param(params)
                });

                $('#download_era_5').removeClass('hidden');

            } else if (data.error) {
                $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the historic data</strong></p>');
                $('#info').removeClass('hidden');

                setTimeout(function() {
                    $('#info').addClass('hidden')
                }, 5000);
            } else {
                $('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            }
        }
    });
};


function get_flow_duration_curve(model, watershed, subbasin, comid, startdate) {
    $('#fdc-view-file-loading').removeClass('hidden');
    m_downloaded_flow_duration = true;
    $.ajax({
        type: 'GET',
        url: 'get-flow-duration-curve',
        data: {
            'model': model,
            'watershed': watershed,
            'subbasin': subbasin,
            'comid': comid,
            'startdate': startdate
        },
        success: function(data) {
            if (!data.error) {
                $('#fdc-view-file-loading').addClass('hidden');
                $('#fdc-chart').removeClass('hidden');
                $('#fdc-chart').html(data);
            } else if (data.error) {
                $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the historic data</strong></p>');
                $('#info').removeClass('hidden');

                setTimeout(function() {
                    $('#info').addClass('hidden')
                }, 5000);
            } else {
                $('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            }
        }
    });
};

function get_daily_seasonal_streamflow(model, watershed, subbasin, comid, startdate) {
    $('#seasonal_d-view-file-loading').removeClass('hidden');
    m_downloaded_flow_duration = true;
    $.ajax({
        type: 'GET',
        url: 'get-daily-seasonal-streamflow',
        data: {
            'model': model,
            'watershed': watershed,
            'subbasin': subbasin,
            'comid': comid,
            'startdate': startdate
        },
        success: function(data) {
            if (!data.error) {
                $('#seasonal_d-view-file-loading').addClass('hidden');
                $('#seasonal_d-chart').removeClass('hidden');
                $('#seasonal_d-chart').html(data);
            } else if (data.error) {
                $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the historic data</strong></p>');
                $('#info').removeClass('hidden');

                setTimeout(function() {
                    $('#info').addClass('hidden')
                }, 5000);
            } else {
                $('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            }
        }
    });
};

function get_monthly_seasonal_streamflow(model, watershed, subbasin, comid, startdate) {
    $('#seasonal_m-view-file-loading').removeClass('hidden');
    m_downloaded_flow_duration = true;
    $.ajax({
        type: 'GET',
        url: 'get-monthly-seasonal-streamflow',
        data: {
            'model': model,
            'watershed': watershed,
            'subbasin': subbasin,
            'comid': comid,
            'startdate': startdate
        },
        success: function(data) {
            if (!data.error) {
                $('#seasonal_m-view-file-loading').addClass('hidden');
                $('#seasonal_m-chart').removeClass('hidden');
                $('#seasonal_m-chart').html(data);
            } else if (data.error) {
                $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the historic data</strong></p>');
                $('#info').removeClass('hidden');

                setTimeout(function() {
                    $('#info').addClass('hidden')
                }, 5000);
            } else {
                $('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            }
        }
    });
};


function get_forecast_percent(watershed, subbasin, comid, startdate) {
    //$loading.removeClass('hidden');
    // $("#forecast-table").addClass('hidden');
    $.ajax({
        type: 'GET',
        url: 'forecastpercent/',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'comid': comid,
            'startdate': startdate
        },
        error: function(xhr, errmsg, err) {
            $('#table').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+".</div>"); // add the error to the dom
			console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        },
        success: function(resp) {
          // console.log(resp)
          $('#forecast-table').html(resp);

          $("#forecast-table").removeClass('hidden');

          $("#forecast-table").show();
          // $('#table').html(resp);
        }
    });
}


function get_discharge_info (stationcode, stationname, startdateobs, enddateobs) {
    $('#observed-loading-Q').removeClass('hidden');
    $.ajax({
        url: 'get-discharge-data',
        type: 'GET',
        data: {'stationcode' : stationcode, 'stationname' : stationname, 'startdateobs' : startdateobs, 'enddateobs' : enddateobs},
        error: function () {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Discharge Data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#observed-loading-Q').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#observed-chart-Q').removeClass('hidden');
                $('#observed-chart-Q').html(data);

                //resize main graph
                Plotly.Plots.resize($("#observed-chart-Q .js-plotly-plot")[0]);

                var params = {
                    stationcode: stationcode,
                    stationname: stationname,
                };

                $('#submit-download-observed-discharge').attr({
                    target: '_blank',
                    href: 'get-observed-discharge-csv?' + jQuery.param(params)
                });

                $('#download_observed_discharge').removeClass('hidden');

                $('#submit-download-sensor-discharge').attr({
                    target: '_blank',
                    href: 'get-sensor-discharge-csv?' + jQuery.param(params)
                });

                $('#download_sensor_discharge').removeClass('hidden');

                } else if (data.error) {
                	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Discharge Data</strong></p>');
                	$('#info').removeClass('hidden');

                	setTimeout(function() {
                    	$('#info').addClass('hidden')
                	}, 5000);
            	} else {
                	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            	}
            }
    })
}

function get_waterlevel_info (stationcode, stationname, startdateobs, enddateobs) {
    $('#observed-loading-WL').removeClass('hidden');
    $.ajax({
        url: 'get-waterlevel-data',
        type: 'GET',
        data: {'stationcode' : stationcode, 'stationname' : stationname, 'startdateobs' : startdateobs, 'enddateobs' : enddateobs},
        error: function () {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Water Level Data</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (!data.error) {
                $('#observed-loading-WL').addClass('hidden');
                $('#dates').removeClass('hidden');
//                $('#obsdates').removeClass('hidden');
                $loading.addClass('hidden');
                $('#observed-chart-WL').removeClass('hidden');
                $('#observed-chart-WL').html(data);

                //resize main graph
                Plotly.Plots.resize($("#observed-chart-WL .js-plotly-plot")[0]);

                var params = {
                    stationcode: stationcode,
                    stationname: stationname,
                };

                $('#submit-download-observed-waterlevel').attr({
                    target: '_blank',
                    href: 'get-observed-waterlevel-csv?' + jQuery.param(params)
                });

                $('#download_observed_waterlevel').removeClass('hidden');

                $('#submit-download-sensor-waterlevel').attr({
                    target: '_blank',
                    href: 'get-sensor-waterlevel-csv?' + jQuery.param(params)
                });

                $('#download_sensor_waterlevel').removeClass('hidden');

                } else if (data.error) {
                	$('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the Discharge Data</strong></p>');
                	$('#info').removeClass('hidden');

                	setTimeout(function() {
                    	$('#info').addClass('hidden')
                	}, 5000);
            	} else {
                	$('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            	}
        }
    })
}

function map_events() {
    map.on('pointermove', function(evt) {
        if (evt.dragging) {
            return;
        }
        var model = $('#model option:selected').text();
        var pixel = map.getEventPixel(evt.originalEvent);
        if (model === 'ECMWF-RAPID') {
            var hit = map.forEachLayerAtPixel(pixel, function(layer) {
                if (layer == feature_layer || layer == feature_layer2) {
                    current_layer = layer;
                    return true;
                }
            });
        } else if (model === 'LIS-RAPID') {
            var hit = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
                if (layer == feature_layer || layer == feature_layer2) {
                    current_feature = feature;
                    return true;
                }
            });
        } else if (model === 'HIWAT-RAPID') {
            var hit = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
                if (layer == feature_layer || layer == feature_layer2) {
                    current_feature = feature;
                    return true;
                }
            });
        }

        map.getTargetElement().style.cursor = hit ? 'pointer' : '';
    });

    map.on("singleclick", function(evt) {
        var model = $('#model option:selected').text();

        if (map.getTargetElement().style.cursor == "pointer") {

            var view = map.getView();
            var viewResolution = view.getResolution();

            if (model === 'ECMWF-RAPID') {
                var wms_url = current_layer.getSource().getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(), { 'INFO_FORMAT': 'application/json' }); //Get the wms url for the clicked point

                if (current_layer["H"]["source"]["i"]["LAYERS"] == "FEWS_Stations_N") {

                        $("#obsgraph").modal('show');
                        $('#observed-chart-Q').addClass('hidden');
                        $('#observed-chart-WL').addClass('hidden');
                        $('#obsdates').addClass('hidden');
                        $('#observed-loading-Q').removeClass('hidden');
                        $('#observed-loading-WL').removeClass('hidden');
                        $("#station-info").empty()
                        $('#download_observed_discharge').addClass('hidden');
                        $('#download_sensor_discharge').addClass('hidden');
                        $('#download_observed_waterlevel').addClass('hidden');
                        $('#download_sensor_waterlevel').addClass('hidden');

                        $.ajax({
                            type: "GET",
                            url: wms_url,
                            dataType: 'json',
                            success: function (result) {
                                stationcode = result["features"][0]["properties"]["id"];
                                stationname = result["features"][0]["properties"]["nombre"];
                                $('#obsdates').removeClass('hidden');
                                var startdateobs = $('#startdateobs').val();
                                var enddateobs = $('#enddateobs').val();
                                $("#station-info").append('<h3>Current Station: '+ stationname + '</h3><h5>Station Code: '+ stationcode);
                                get_discharge_info (stationcode, stationname, startdateobs, enddateobs);
                                get_waterlevel_info (stationcode, stationname, startdateobs, enddateobs);

                            }
                        });

                }

                //if (wms_url) {
                else {

                    $("#graph").modal('show');
                    $("#tbody").empty()
                    $('#long-term-chart').addClass('hidden');
                    $("#forecast-table").addClass('hidden');
                    $('#historical-chart').addClass('hidden');
                    $('#fdc-chart').addClass('hidden');
                    $('#seasonal_d-chart').addClass('hidden');
                    $('#seasonal_m-chart').addClass('hidden');
                    $('#download_forecast').addClass('hidden');
                    $('#download_era_5').addClass('hidden');

                    $loading.removeClass('hidden');
                    //Retrieving the details for clicked point via the url
                    $('#dates').addClass('hidden');
                    //$('#plot').addClass('hidden');
                    $.ajax({
                        type: "GET",
                        url: wms_url,
                        dataType: 'json',
                        success: function(result) {
                            var model = $('#model option:selected').text();
                            comid = result["features"][0]["properties"]["COMID"];

                            var startdate = '';
                            if ("derived_fr" in (result["features"][0]["properties"])) {
                                var watershed = (result["features"][0]["properties"]["derived_fr"]).toLowerCase().split('-')[0];
                                var subbasin = (result["features"][0]["properties"]["derived_fr"]).toLowerCase().split('-')[1];
                            } else if (JSON.parse($('#geoserver_endpoint').val())[2]) {
                                var watershed = JSON.parse($('#geoserver_endpoint').val())[2].split('-')[0]
                                var subbasin = JSON.parse($('#geoserver_endpoint').val())[2].split('-')[1];
                            } else {
                                var watershed = (result["features"][0]["properties"]["watershed"]).toLowerCase();
                                var subbasin = (result["features"][0]["properties"]["subbasin"]).toLowerCase();
                            }

                            get_available_dates(model, watershed, subbasin, comid);
                            get_time_series(model, watershed, subbasin, comid, startdate);
                            get_historic_data(model, watershed, subbasin, comid, startdate);
                            get_flow_duration_curve(model, watershed, subbasin, comid, startdate);
                            get_daily_seasonal_streamflow(model, watershed, subbasin, comid, startdate);
                            get_monthly_seasonal_streamflow(model, watershed, subbasin, comid, startdate);
                            if (model === 'ECMWF-RAPID') {
                                get_forecast_percent(watershed, subbasin, comid, startdate);
                            };

                            var workspace = JSON.parse($('#geoserver_endpoint').val())[1];

                            $('#info').addClass('hidden');
                            add_feature(model, workspace, comid);

                        },
                        error: function(XMLHttpRequest, textStatus, errorThrown) {
                            console.log(Error);
                        }
                    });
                }



            }
        };
    });

}

function add_feature(model, workspace, comid) {
    map.removeLayer(featureOverlay);

    var watershed = $('#watershedSelect option:selected').text().split(' (')[0].replace(' ', '_').toLowerCase();
    var subbasin = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '').toLowerCase();

    if (model === 'ECMWF-RAPID') {
        var vectorSource = new ol.source.Vector({
            format: new ol.format.GeoJSON(),
            url: function(extent) {
                return JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "") + '/' + 'ows?service=wfs&' +
                    'version=2.0.0&request=getfeature&typename=' + workspace + ':' + watershed + '-' + subbasin + '-drainage_line' + '&CQL_FILTER=COMID=' + comid + '&outputFormat=application/json&srsname=EPSG:3857&' + ',EPSG:3857';
            },
            strategy: ol.loadingstrategy.bbox
        });

        featureOverlay = new ol.layer.Vector({
            source: vectorSource,
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: '#00BFFF',
                    width: 8
                })
            })
        });
        map.addLayer(featureOverlay);
        map.getLayers().item(5);

    } else if (model === 'LIS-RAPID') {
        var vectorSource;
        $.ajax({
            type: 'GET',
            url: 'get-lis-shp/',
            dataType: 'json',
            data: {
                'model': model,
                'watershed': workspace[0],
                'subbasin': workspace[1]
            },
            success: function(result) {
                JSON.parse(result.options).features.forEach(function(elm) {
                    if (elm.properties.COMID === parseInt(comid)) {
                        var filtered_json = {
                            "type": "FeatureCollection",
                            "features": [elm]
                        };
                        vectorSource = new ol.source.Vector({
                            features: (new ol.format.GeoJSON()).readFeatures(filtered_json)
                        });
                    }
                });

                featureOverlay = new ol.layer.Vector({
                    source: vectorSource,
                    style: new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: '#00BFFF',
                            width: 8
                        })
                    })
                });
                map.addLayer(featureOverlay);
                map.getLayers().item(5);
            }
        });

    } else if (model === 'HIWAT-RAPID') {
        var vectorSource;
        $.ajax({
            type: 'GET',
            url: 'get-hiwat-shp/',
            dataType: 'json',
            data: {
                'model': model,
                'watershed': workspace[0],
                'subbasin': workspace[1]
            },
            success: function(result) {
                JSON.parse(result.options).features.forEach(function(elm) {
                    if (elm.properties.COMID === parseInt(comid)) {
                        var filtered_json = {
                            "type": "FeatureCollection",
                            "features": [elm]
                        };
                        vectorSource = new ol.source.Vector({
                            features: (new ol.format.GeoJSON()).readFeatures(filtered_json)
                        });
                    }
                });

                featureOverlay = new ol.layer.Vector({
                    source: vectorSource,
                    style: new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: '#00BFFF',
                            width: 8
                        })
                    })
                });
                map.addLayer(featureOverlay);
                map.getLayers().item(5);
            }
        });
    }
}

function submit_model() {
    $('#model').on('change', function() {
        var base_path = location.pathname;

        if (base_path.includes('ecmwf-rapid') || base_path.includes('lis-rapid') || base_path.includes('hiwat-rapid')) {
            base_path = base_path.replace('/ecmwf-rapid', '').replace('/lis-rapid', '').replace('/hiwat-rapid', '');
        }

        if ($('#model option:selected').val() === 'ecmwf') {
            location.href = 'http://' + location.host + base_path + 'ecmwf-rapid/?model=ECMWF-RAPID';
        } else if ($('#model option:selected').val() === 'lis') {
            location.href = 'http://' + location.host + base_path + 'lis-rapid/?model=LIS-RAPID';
        } else if ($('#model option:selected').val() === 'hiwat') {
            location.href = 'http://' + location.host + base_path + 'hiwat-rapid/?model=HIWAT-RAPID';
        } else {
            location.href = 'http://' + location.host + base_path;
        }
    });
};

function resize_graphs() {
    $("#forecast_tab_link").click(function() {
        Plotly.Plots.resize($("#long-term-chart .js-plotly-plot")[0]);
    });

    $("#historical_tab_link").click(function() {
        if (m_downloaded_historical_streamflow) {
        	Plotly.Plots.resize($("#historical-chart .js-plotly-plot")[0]);
        }
    });

    $("#flow_duration_tab_link").click(function() {
        if (m_downloaded_flow_duration) {
            Plotly.Plots.resize($("#fdc-chart .js-plotly-plot")[0]);
            Plotly.Plots.resize($("#seasonal_d-chart .js-plotly-plot")[0]);
            Plotly.Plots.resize($("#seasonal_m-chart .js-plotly-plot")[0]);
        }
    });
    $("#observedQ_tab_link").click(function() {
        Plotly.Plots.resize($("#observed-chart-Q .js-plotly-plot")[0]);
    });
    $("#observedWL_tab_link").click(function() {
        Plotly.Plots.resize($("#observed-chart-WL .js-plotly-plot")[0]);
    });
};

$(function() {
    $('#app-content-wrapper').removeClass('show-nav');
    $(".toggle-nav").removeClass('toggle-nav');

    //make sure active Plotly plots resize on window resize
    window.onresize = function() {
        $('#graph .modal-body .tab-pane.active .js-plotly-plot').each(function(){
            Plotly.Plots.resize($(this)[0]);
        });
    };

    init_map();
    map_events();
    submit_model();
    resize_graphs();
    // If there is a defined Watershed, then lets render it and hide the controls
    let ws_val = $('#watershed').find(":selected").text();
    if (ws_val && ws_val !== 'Select Watershed') {
        view_watershed();
        $("[name='update_button']").hide();
    }
    // If there is a button to save default WS, let's add handler
    $("[name='update_button']").click(() => {
        $.ajax({
            url: 'admin/setdefault',
            type: 'GET',
            dataType: 'json',
            data: {
                'ws_name': $('#model').find(":selected").text(),
                'model_name': $('#watershed').find(":selected").text()
            },
            success: function() {
                // Remove the set default button
                $("[name='update_button']").hide(500);
                console.log('Updated Defaults Successfully');
            }
        });
    })


    $('#datesSelect').change(function() { //when date is changed
    	//console.log($("#datesSelect").val());

        //var sel_val = ($('#datesSelect option:selected').val()).split(',');
        sel_val = $("#datesSelect").val()

        //var startdate = sel_val[0];
        var startdate = sel_val;
        startdate = startdate.replace("-","");
        startdate = startdate.replace("-","");

        //var watershed = sel_val[1];
        var watershed = 'south_america';

        //var subbasin = sel_val[2];
        var subbasin = 'geoglows';

        //var comid = sel_val[3];
        var model = 'ECMWF-RAPID';

        $loading.removeClass('hidden');
        get_time_series(model, watershed, subbasin, comid, startdate);
        get_forecast_percent(watershed, subbasin, comid, startdate);
    });
    $('#startdateobs').change(function() { //when date is changed
        var startdateobs = $('#startdateobs').val();
        var enddateobs = $('#enddateobs').val();
        $('#observed-loading-Q').removeClass('hidden');
        $('#observed-loading-WL').removeClass('hidden');
        get_discharge_info (stationcode, stationname, startdateobs, enddateobs);
        get_waterlevel_info (stationcode, stationname, startdateobs, enddateobs);
    });
    $('#enddateobs').change(function() { //when date is changed
        var startdateobs = $('#startdateobs').val();
        var enddateobs = $('#enddateobs').val();
        $('#observed-loading-Q').removeClass('hidden');
        $('#observed-loading-WL').removeClass('hidden');
        get_discharge_info (stationcode, stationname, startdateobs, enddateobs);
        get_waterlevel_info (stationcode, stationname, startdateobs, enddateobs);
    });
});


function getRegionGeoJsons() {

    let geojsons = region_index[$("#regions").val()]['geojsons'];
    for (let i in geojsons) {
        var regionsSource = new ol.source.Vector({
           url: staticGeoJSON + geojsons[i],
           format: new ol.format.GeoJSON()
        });

        var regionStyle = new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: 'red',
                width: 3
            })
        });

        var regionsLayer = new ol.layer.Vector({
            name: 'myRegion',
            source: regionsSource,
            style: regionStyle
        });

        map.getLayers().forEach(function(regionsLayer) {
        if (regionsLayer.get('name')=='myRegion')
            map.removeLayer(regionsLayer);
        });
        map.addLayer(regionsLayer)

        setTimeout(function() {
            var myExtent = regionsLayer.getSource().getExtent();
            map.getView().fit(myExtent, map.getSize());
        }, 500);
    }
}


$('#stp-stream-toggle').on('change', function() {
    wmsLayer.setVisible($('#stp-stream-toggle').prop('checked'))
})
$('#stp-stations-toggle').on('change', function() {
    wmsLayer2.setVisible($('#stp-stations-toggle').prop('checked'))
})
$('#stp-100-toggle').on('change', function() {
    hundred_year_warning.setVisible($('#stp-100-toggle').prop('checked'))
})
$('#stp-50-toggle').on('change', function() {
    fifty_year_warning.setVisible($('#stp-50-toggle').prop('checked'))
})
$('#stp-25-toggle').on('change', function() {
    twenty_five_year_warning.setVisible($('#stp-25-toggle').prop('checked'))
})
$('#stp-10-toggle').on('change', function() {
    ten_year_warning.setVisible($('#stp-10-toggle').prop('checked'))
})
$('#stp-5-toggle').on('change', function() {
    five_year_warning.setVisible($('#stp-5-toggle').prop('checked'))
})
$('#stp-2-toggle').on('change', function() {
    two_year_warning.setVisible($('#stp-2-toggle').prop('checked'))
})

// Regions gizmo listener
$('#regions').change(function() {getRegionGeoJsons()});
