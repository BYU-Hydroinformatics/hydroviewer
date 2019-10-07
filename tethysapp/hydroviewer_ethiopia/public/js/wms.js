/* Global Variables */
var default_extent,
    current_layer,
    current_feature,
    feature_layer,
    stream_geom,
    layers,
    wmsLayer,
    vectorLayer,
    feature,
    featureOverlay,
    forecastFolder,
    select_interaction,
    two_year_warning,
    ten_year_warning,
    twenty_year_warning,
    map,
    wms_layers;


var $loading = $('#view-file-loading');
var m_downloaded_historical_streamflow = false;
var m_downloaded_flow_duration = false;

const glofasURL = `http://globalfloods-ows.ecmwf.int/glofas-ows/ows.py`

//create symbols for warnings
var twenty_symbols = [new ol.style.RegularShape({
    points: 3,
    radius: 5,
    fill: new ol.style.Fill({
        color: 'rgba(128,0,128,0.8)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(128,0,128,1)',
        width: 1
    })
}), new ol.style.RegularShape({
    points: 3,
    radius: 9,
    fill: new ol.style.Fill({
        color: 'rgba(128,0,128,0.3)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(128,0,128,1)',
        width: 1
    })
})];

//symbols
var ten_symbols = [new ol.style.RegularShape({
    points: 3,
    radius: 5,
    fill: new ol.style.Fill({
        color: 'rgba(255,0,0,0.7)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(255,0,0,1)',
        width: 1
    })
}), new ol.style.RegularShape({
    points: 3,
    radius: 9,
    fill: new ol.style.Fill({
        color: 'rgba(255,0,0,0.3)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(255,0,0,1)',
        width: 1
    })
})];

//symbols
var two_symbols = [new ol.style.RegularShape({
    points: 3,
    radius: 5,
    fill: new ol.style.Fill({
        color: 'rgba(255,255,0,0.7)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(255,255,0,1)',
        width: 1
    })
}), new ol.style.RegularShape({
    points: 3,
    radius: 9,
    fill: new ol.style.Fill({
        color: 'rgba(255,255,0,0.3)'
    }),
    stroke: new ol.style.Stroke({
        color: 'rgba(255,255,0,1)',
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
                fill: new ol.style.Fill({ color: 'yellow' }),
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
                fill: new ol.style.Fill({ color: 'red' }),
                stroke: new ol.style.Stroke({ color: 'black', width: 0.5 }),
                points: 3,
                radius: 10,
                angle: 0
            })
        })
    });

    twenty_year_warning = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            image: new ol.style.RegularShape({
                fill: new ol.style.Fill({ color: 'rgba(128,0,128,0.8)' }),
                stroke: new ol.style.Stroke({ color: 'black', width: 0.5 }),
                points: 3,
                radius: 10,
                angle: 0
            })
        })
    });


    if (JSON.parse($('#geoserver_endpoint').val())[3]) {
        var wmsLayer = new ol.layer.Image({
            source: new ol.source.ImageWMS({
                url: JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "") + '/wms',
                params: { 'LAYERS': JSON.parse($('#geoserver_endpoint').val())[3] },
                serverType: 'geoserver',
                crossOrigin: 'Anonymous'
            })
        });

        layers = [base_layer, two_year_warning, ten_year_warning, twenty_year_warning].concat(wms_layers).concat([wmsLayer, featureOverlay])
    } else {
        layers = [base_layer, two_year_warning, ten_year_warning, twenty_year_warning].concat(wms_layers).concat([featureOverlay])
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
        var layer_name = JSON.parse($('#geoserver_endpoint').val())[4];
        $("#watershed-info").append('<h3>Current Watershed: ' + watershed_display_name + '</h3><h5>Subbasin Name: ' + subbasin_display_name);

        var layerName = workspace + ':' + layer_name;
        wmsLayer = new ol.layer.Image({
            source: new ol.source.ImageWMS({
                url: JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "") + '/wms',
                params: { 'LAYERS': layerName },
                serverType: 'geoserver',
                crossOrigin: 'Anonymous'
            })
        });
        feature_layer = wmsLayer;

        get_warning_points(model, watershed, subbasin);

        map.addLayer(wmsLayer);

        $loading.addClass('hidden');
        var ajax_url = JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "") + '/' + workspace + '/' + layer_name + '/wfs?request=GetCapabilities';

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
                    .split(workspace + ':' + watershed + '-' + subbasin)[1]
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
        var layer_name = JSON.parse($('#geoserver_endpoint').val())[4];
        $("#watershed-info").append('<h3>Current Watershed: ' + watershed_display_name + '</h3><h5>Subbasin Name: ' + subbasin_display_name);

        var layerName = workspace + ':' + layer_name;
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

                map.addLayer(wmsLayer);

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
        var layer_name = JSON.parse($('#geoserver_endpoint').val())[4];
        $("#watershed-info").append('<h3>Current Watershed: ' + watershed_display_name + '</h3><h5>Subbasin Name: ' + subbasin_display_name);

        var layerName = workspace + ':' + layer_name;
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

                map.addLayer(wmsLayer);

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

            if (result.warning2 != 'undefined') {
                var warLen2 = result.warning2.length;
                for (var i = 0; i < warLen2; ++i) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning2[i].geometry.coordinates[0],
                            result.warning2[i].geometry.coordinates[1]
                        ],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: result.warning2[i].properties.size
                    });
                    map.getLayers().item(1).getSource().addFeature(feature);
                }
                map.getLayers().item(1).setVisible(false);
            }

            if (result.warning10 != 'undefined') {
                var warLen10 = result.warning10.length;
                for (var j = 0; j < warLen10; ++j) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning10[j].geometry.coordinates[0],
                            result.warning10[j].geometry.coordinates[1]
                        ],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: result.warning10[j].properties.size
                    });
                    map.getLayers().item(2).getSource().addFeature(feature);
                }
                map.getLayers().item(2).setVisible(false);
            }

            if (result.warning20 != 'undefined') {
                var warLen20 = result.warning20.length;
                for (var k = 0; k < warLen20; ++k) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning20[k].geometry.coordinates[0],
                            result.warning20[k].geometry.coordinates[1]
                        ],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: result.warning20[k].properties.size
                    });
                    map.getLayers().item(3).getSource().addFeature(feature);
                }
                map.getLayers().item(3).setVisible(false);
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

function get_return_periods(watershed, subbasin, comid) {
    $.ajax({
        type: 'GET',
        url: 'get-return-periods/',
        dataType: 'json',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'comid': comid
        },
        error: function() {
            $('#info').html(
                '<p class="alert alert-warning" style="text-align: center"><strong>Return Periods are not available for this dataset.</strong></p>'
            );

            $('#info').removeClass('hidden');

            setTimeout(function() {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function(data) {
            $("#container").highcharts().yAxis[0].addPlotBand({
                from: parseFloat(data.return_periods.twenty),
                to: parseFloat(data.return_periods.max),
                color: 'rgba(128,0,128,0.4)',
                id: '20-yr',
                label: {
                    text: '20-yr',
                    align: 'right'
                }
            });
            $("#container").highcharts().yAxis[0].addPlotBand({
                from: parseFloat(data.return_periods.ten),
                to: parseFloat(data.return_periods.twenty),
                color: 'rgba(255,0,0,0.3)',
                id: '10-yr',
                label: {
                    text: '10-yr',
                    align: 'right'
                }
            });
            $("#container").highcharts().yAxis[0].addPlotBand({
                from: parseFloat(data.return_periods.two),
                to: parseFloat(data.return_periods.ten),
                color: 'rgba(255,255,0,0.3)',
                id: '2-yr',
                label: {
                    text: '2-yr',
                    align: 'right'
                }
            });
        }
    });
}

function get_time_series(model, watershed, subbasin, comid, startdate, tot_drain_area, region) {
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
            'startdate': startdate,
            'tot_drain_area': tot_drain_area,
            'region': region
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


function get_historic_data(model, watershed, subbasin, comid, startdate, tot_drain_area, region) {
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
            'startdate': startdate,
            'tot_drain_area': tot_drain_area,
            'region': region
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

                $('#submit-download-interim-csv').attr({
                    target: '_blank',
                    href: 'get-historic-data-csv?' + jQuery.param(params)
                });

                $('#download_interim').removeClass('hidden');

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


function get_flow_duration_curve(model, watershed, subbasin, comid, startdate, tot_drain_area, region) {
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
            'startdate': startdate,
            'tot_drain_area': tot_drain_area,
            'region': region
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

function get_forecast_percent(watershed, subbasin, comid, startdate) {
    $('#mytable').addClass('hidden');
    $.ajax({
        url: 'forecastpercent/',
        type: 'GET',
        data: {
            'comid': comid,
            'watershed': watershed,
            'subbasin': subbasin,
            'startdate': startdate
        },
        error: function() {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the forecast table</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function() {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function(data) {
            $("#tbody").empty()
            var tbody = document.getElementById('tbody');

            var columNames = {
                'two': 'Percent Exceedance (2-yr)',
                'ten': 'Percent Exceedance (10-yr)',
                'twenty': 'Percent Exceedance (20-yr)',
            };

            for (var object1 in data) {
                if (object1 == "dates") {
                    cellcolor = ""
                } else if (object1 == "two") {
                    cellcolor = "yellow"
                } else if (object1 == "ten") {
                    cellcolor = "red"
                } else if (object1 == "twenty") {
                    cellcolor = "purple"
                }
                if (object1 == "percdates") {
                    var tr = "<tr id=" + object1.toString() + "><th>Dates</th>";
                    for (var value1 in data[object1]) {
                        tr += "<th>" + data[object1][value1].toString() + "</th>"
                    }
                    tr += "</tr>";
                    tbody.innerHTML += tr;
                } else {
                    var tr = "<tr id=" + object1.toString() + "><td>" + columNames[object1.toString()] + "</td>";
                    for (var value1 in data[object1]) {
                        if (parseInt(data[object1][value1]) == 0) {
                            tr += "<td class=" + cellcolor + "zero>" + data[object1][value1].toString() + "</td>"
                        } else if (parseInt(data[object1][value1]) <= 20) {
                            tr += "<td class=" + cellcolor + "twenty>" + data[object1][value1].toString() + "</td>"
                        } else if (parseInt(data[object1][value1]) <= 40) {
                            tr += "<td class=" + cellcolor + "fourty>" + data[object1][value1].toString() + "</td>"
                        } else if (parseInt(data[object1][value1]) <= 60) {
                            tr += "<td class=" + cellcolor + "sixty>" + data[object1][value1].toString() + "</td>"
                        } else if (parseInt(data[object1][value1]) <= 80) {
                            tr += "<td class=" + cellcolor + "eighty>" + data[object1][value1].toString() + "</td>"
                        } else {
                            tr += "<td class=" + cellcolor + "hundred>" + data[object1][value1].toString() + "</td>"
                        }
                    }
                    tr += "</tr>";
                    tbody.innerHTML += tr;
                }
            }

            $("#twenty").prependTo("#mytable");
            $("#ten").prependTo("#mytable");
            $("#two").prependTo("#mytable");
            $("#percdates").prependTo("#mytable");
            $('#mytable').removeClass('hidden');
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
                if (layer == feature_layer) {
                    current_layer = layer;
                    return true;
                }
            });
        } else if (model === 'LIS-RAPID') {
            var hit = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
                if (layer == feature_layer) {
                    current_feature = feature;
                    return true;
                }
            });
        } else if (model === 'HIWAT-RAPID') {
            var hit = map.forEachFeatureAtPixel(pixel, function(feature, layer) {
                if (layer == feature_layer) {
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
            $("#graph").modal('show');
            $("#tbody").empty()
            $('#long-term-chart').addClass('hidden');
            $('#historical-chartjson').addClass('hidden');
            $('#fdc-chart').addClass('hidden');
            $('#download_forecast').addClass('hidden');
            $('#download_interim').addClass('hidden');

            var view = map.getView();
            var viewResolution = view.getResolution();

            if (model === 'ECMWF-RAPID') {
                var wms_url = current_layer.getSource().getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(), { 'INFO_FORMAT': 'application/json' }); //Get the wms url for the clicked point

                if (wms_url) {
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
                            var comid = result["features"][0]["properties"]["COMID"];
                            var tot_drain_area = result["features"][0]["properties"]["Tot_Drain_"];
                            tot_drain_area = (tot_drain_area/1000000).toFixed(0)
                            var region = result["features"][0]["properties"]["region"];

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
                            get_time_series(model, watershed, subbasin, comid, startdate, tot_drain_area, region);
                            get_historic_data(model, watershed, subbasin, comid, startdate, tot_drain_area, region);
                            get_flow_duration_curve(model, watershed, subbasin, comid, startdate, tot_drain_area, region);
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
            } else if (model === 'LIS-RAPID') {
                var comid = current_feature.get('COMID');
                var watershed = $('#watershedSelect option:selected').val().split('-')[0]
                var subbasin = $('#watershedSelect option:selected').val().split('-')[1]

                get_time_series(model, watershed, subbasin, comid);

                $('#info').addClass('hidden');
                var workspace = [watershed, subbasin];

                add_feature(model, workspace, comid);
            } else if (model === 'HIWAT-RAPID') {
                var comid = current_feature.get('COMID');
                var watershed = $('#watershedSelect option:selected').val().split('-')[0]
                var subbasin = $('#watershedSelect option:selected').val().split('-')[1]

                get_time_series(model, watershed, subbasin, comid);

                $('#info').addClass('hidden');
                var workspace = [watershed, subbasin];

                add_feature(model, workspace, comid);
            }
        };
    });

}

function add_feature(model, workspace, comid) {
    map.removeLayer(featureOverlay);

    var watershed = $('#watershedSelect option:selected').text().split(' (')[0].replace(' ', '_').toLowerCase();
    var subbasin = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '').toLowerCase();
    var layer_name = JSON.parse($('#geoserver_endpoint').val())[4];

    if (model === 'ECMWF-RAPID') {
        var vectorSource = new ol.source.Vector({
            format: new ol.format.GeoJSON(),
            url: function(extent) {
                return JSON.parse($('#geoserver_endpoint').val())[0].replace(/\/$/, "") + '/' + 'ows?service=wfs&' +
                    'version=2.0.0&request=getfeature&typename=' + workspace + ':' + layer_name + '&CQL_FILTER=COMID=' + comid + '&outputFormat=application/json&srsname=EPSG:3857&' + ',EPSG:3857';
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
        }
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
        var sel_val = ($('#datesSelect option:selected').val()).split(',');
        var startdate = sel_val[0];
        var watershed = sel_val[1];
        var subbasin = sel_val[2];
        var comid = sel_val[3];
        var model = 'ECMWF-RAPID';
        $loading.removeClass('hidden');
        get_time_series(model, watershed, subbasin, comid, startdate);
        get_forecast_percent(watershed, subbasin, comid, startdate);
    });
});

$('#stp-stream-toggle').on('change', function() {
    wmsLayer.setVisible($('#stp-stream-toggle').prop('checked'))
})
$('#stp-20-toggle').on('change', function() {
    twenty_year_warning.setVisible($('#stp-20-toggle').prop('checked'))
})
$('#stp-10-toggle').on('change', function() {
    ten_year_warning.setVisible($('#stp-10-toggle').prop('checked'))
})
$('#stp-2-toggle').on('change', function() {
    two_year_warning.setVisible($('#stp-2-toggle').prop('checked'))
})