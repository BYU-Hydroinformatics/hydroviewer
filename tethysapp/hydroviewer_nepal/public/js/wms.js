/* Global Variables */
var current_layer,
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
    map;
var model = 'ecmwf-rapid';
var $loading = $('#view-file-loading');
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
}),new ol.style.RegularShape({
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
}),new ol.style.RegularShape({
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
}),new ol.style.RegularShape({
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


function init_map(){


    var base_layer = new ol.layer.Tile({
        source: new ol.source.BingMaps({
            key: 'eLVu8tDRPeQqmBlKAjcw~82nOqZJe2EpKmqd-kQrSmg~AocUZ43djJ-hMBHQdYDyMbT-Enfsk0mtUIGws1WeDuOvjY4EXCH-9OK3edNLDgkc',
            imagerySet: 'AerialWithLabels'
        })
    });


    featureOverlay = new ol.layer.Vector({
        source: new ol.source.Vector()
    });

    two_year_warning = new ol.layer.Vector({
        source: new ol.source.Vector(),
        style: new ol.style.Style({
            image: new ol.style.RegularShape({
                fill: new ol.style.Fill({color: 'yellow'}),
                stroke: new ol.style.Stroke({color: 'black', width: 0.5}),
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
                fill: new ol.style.Fill({color: 'red'}),
                stroke: new ol.style.Stroke({color: 'black', width: 0.5}),
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
                fill: new ol.style.Fill({color: 'rgba(128,0,128,0.8)'}),
                stroke: new ol.style.Stroke({color: 'black', width: 0.5}),
                points: 3,
                radius: 10,
                angle: 0
            })
        })
    });




    layers = [base_layer,two_year_warning,ten_year_warning,twenty_year_warning,featureOverlay];
    map = new ol.Map({
        target: 'map',
        view: new ol.View({
            center: ol.proj.transform([84, 28.2], 'EPSG:4326', 'EPSG:3857'),
            zoom: 3,
            minZoom: 2,
            maxZoom: 18,
            zoom:7.5
        }),
        layers:layers
    });

}

function view_watershed(){
    map.removeInteraction(select_interaction);
    map.removeLayer(wmsLayer);
    $("#get-started").modal('hide');
    if ($('#watershedSelect option:selected').val() !== "") {

//        $("#inner-app-content").addClass("row");
//        $("#map").addClass("col-md-7");
//        $("#graph").removeClass("hidden");
//        $("#graph").addClass("col-md-5");

        $("#watershed-info").empty();

        $('#dates').addClass('hidden');

        //$('#plot').addClass('hidden');

        map.updateSize();

        var workspace = 'spt-30935191ace55f90bd1e61456f1ef016';
        var watershed = $('#watershedSelect option:selected').text().split(' (')[0].replace(' ', '_').toLowerCase();
        var subbasin = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '').toLowerCase();
        var watershed_display_name = $('#watershedSelect option:selected').text().split(' (')[0];
        var subbasin_display_name = $('#watershedSelect option:selected').text().split(' (')[1].replace(')', '');
        $("#watershed-info").append('<h3>Current Watershed: '+watershed_display_name+'</h3><h5>Subbasin Name: '+subbasin_display_name);

        var layerName = workspace+':'+watershed+'-'+subbasin+'-drainage_line';
        wmsLayer = new ol.layer.Image({
            source: new ol.source.ImageWMS({
                url: 'http://tethys.byu.edu:8181/geoserver/wms',
                params: {'LAYERS':layerName},
                serverType: 'geoserver',
                crossOrigin: 'Anonymous'
            })
        });

        get_warning_points(watershed,subbasin);
        map.addLayer(wmsLayer);

        $loading.addClass('hidden');
        var ajax_url ='http://tethys.byu.edu:8181/geoserver/'+workspace+'/'+watershed+'-'+subbasin+'-drainage_line/wfs?request=GetCapabilities';

        var capabilities = $.ajax(ajax_url, {
            type: 'GET',
            data: {
                service: 'WFS',
                version: '1.0.0',
                request: 'GetCapabilities',
                outputFormat: 'text/javascript'
            },
            success: function () {
                var x = capabilities.responseText
                    .split('<FeatureTypeList>')[1]
                    .split(workspace + ':' + watershed + '-' + subbasin)[1]
                    .split('LatLongBoundingBox ')[1]
                    .split('/></FeatureType>')[0];

                var minx = Number(x.split('"')[1]);
                var miny = Number(x.split('"')[3]);
                var maxx = Number(x.split('"')[5]);
                var maxy = Number(x.split('"')[7]);
                if(watershed=='south_asia'){
                    var extent = ol.proj.transform([64.5,9.5], 'EPSG:4326', 'EPSG:3857').concat(ol.proj.transform([105.5, 31.5], 'EPSG:4326', 'EPSG:3857'));

                    map.getView().fit(extent, map.getSize())
                }else{
                    var extent = ol.proj.transform([minx, miny], 'EPSG:4326', 'EPSG:3857').concat(ol.proj.transform([maxx, maxy], 'EPSG:4326', 'EPSG:3857'));

                    map.getView().fit(extent, map.getSize())
                }

            }
        });

    } else {
//        $("#inner-app-content").removeClass("row");
//        $("#map").removeClass("col-md-7");
//        $("#graph").addClass("hidden");
//        $("#graph").removeClass("col-md-5");

        map.updateSize();
        //map.removeInteraction(select_interaction);
        map.removeLayer(wmsLayer);
        map.getView().fit([-13599676.07249856, -6815054.405920124, 13599676.07249856, 11030851.461876547], map.getSize());
    }
}

function get_warning_points(watershed,subbasin){
    $.ajax({
        type: 'GET',
        url: 'ecmwf-rapid/get-warning-points/',
        dataType: 'json',
        data: {
            'watershed': watershed,
            'subbasin': subbasin
        },
        error: function (error) {
            console.log(error);
        },
        success: function (result) {

            map.getLayers().item(1).getSource().clear();
            map.getLayers().item(2).getSource().clear();
            map.getLayers().item(3).getSource().clear();

            if(result.warning2 != 'undefined'){
                var warLen2 = result.warning2.length;
                for (var i = 0; i < warLen2; ++i) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning2[i].lon,
                            result.warning2[i].lat],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: result.warning2[i].size
                    });
                    map.getLayers().item(1).getSource().addFeature(feature);
                }
                map.getLayers().item(1).setVisible(true);
            }

            if(result.warning10 != 'undefined'){
                var warLen10 = result.warning10.length;
                for (var j = 0; j < warLen10; ++j) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning10[j].lon,
                            result.warning10[j].lat],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: result.warning10[j].size
                    });
                    map.getLayers().item(2).getSource().addFeature(feature);
                }
                map.getLayers().item(2).setVisible(true);
            }

            if(result.warning20 != 'undefined'){
                var warLen20 = result.warning20.length;
                for (var k = 0; k < warLen20; ++k) {
                    var geometry = new ol.geom.Point(ol.proj.transform([result.warning20[k].lon,
                            result.warning20[k].lat],
                        'EPSG:4326', 'EPSG:3857'));
                    var feature = new ol.Feature({
                        geometry: geometry,
                        point_size: result.warning20[k].size
                    });
                    map.getLayers().item(3).getSource().addFeature(feature);
                }
                map.getLayers().item(3).setVisible(true);
            }

        }
    });
}

function get_available_dates(watershed, subbasin,comid) {

    $.ajax({
        type: 'GET',
        url: 'ecmwf-rapid/get-available-dates/',
        dataType: 'json',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'comid':comid
        },
        error: function () {
            $('#dates').html(
                '<p class="alert alert-danger" style="text-align: center"><strong>An error occurred while retrieving the available dates</strong></p>'
            );

            setTimeout(function () {
                $('#dates').addClass('hidden')
            }, 5000);
        },
        success: function (dates) {
            datesParsed = JSON.parse(dates.available_dates);
            $('#datesSelect').empty();

            $.each(datesParsed, function(i, p) {
                var val_str = p.slice(1).join();
                $('#datesSelect').append($('<option></option>').val(val_str).html(p[0]));
            });

        }
    });
}

function get_return_periods(watershed, subbasin, comid) {
    $.ajax({
        type: 'GET',
        url: 'ecmwf-rapid/get-return-periods/',
        dataType: 'json',
        data: {
            'watershed': watershed,
            'subbasin': subbasin,
            'comid': comid
        },
        error: function () {
            $('#info').html(
                '<p class="alert alert-warning" style="text-align: center"><strong>Return Periods are not available for this dataset.</strong></p>'
            );

            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
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

function get_time_series(model, watershed, subbasin, comid, startdate) {
    $loading.removeClass('hidden');
    $("#plot").addClass('hidden');
    $('#dates').addClass('hidden');
    $.ajax({
        type: 'GET',
        url: 'ecmwf-rapid/get-time-series/',
        data: {
            'model': model,
            'watershed': watershed,
            'subbasin': subbasin,
            'comid': comid,
            'startdate': startdate
        },
        error: function () {
            $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the forecast</strong></p>');
            $('#info').removeClass('hidden');

            setTimeout(function () {
                $('#info').addClass('hidden')
            }, 5000);
        },
        success: function (data) {
            if (data.error = false) {
            $("#plot").removeClass('hidden');
            $('#dates').removeClass('hidden');
            $('#long-term-chart').removeClass('hidden');
            $('#long-term-chart').html(data);

            } else if (data.error) {
                $('#info').html('<p class="alert alert-danger" style="text-align: center"><strong>An unknown error occurred while retrieving the forecast</strong></p>');
                $('#info').removeClass('hidden');

                setTimeout(function () {
                    $('#info').addClass('hidden')
                }, 5000);
            } else {
                $('#info').html('<p><strong>An unexplainable error occurred.</strong></p>').removeClass('hidden');
            }
        }
    });
}


function map_events(){
    map.on('pointermove', function(evt) {
        if (evt.dragging) {
            return;
        }
        var pixel = map.getEventPixel(evt.originalEvent);
        var hit = map.forEachLayerAtPixel(pixel, function(layer) {
            if (layer != layers[0] && layer != layers[1] && layer != layers[2] && layer != layers[3]){
                current_layer = layer;
                return true;}
        });
        map.getTargetElement().style.cursor = hit ? 'pointer' : '';
    });

    map.on("singleclick",function(evt) {

        $("#graph").modal('show');

        if (map.getTargetElement().style.cursor == "pointer") {
            var view = map.getView();
            var viewResolution = view.getResolution();

            var wms_url = current_layer.getSource().getGetFeatureInfoUrl(evt.coordinate, viewResolution, view.getProjection(), {'INFO_FORMAT': 'application/json'}); //Get the wms url for the clicked point
            if (wms_url) {
                $loading.removeClass('hidden');
                //Retrieving the details for clicked point via the url
                $('#dates').addClass('hidden');
                //$('#plot').addClass('hidden');
                $.ajax({
                    type: "GET",
                    url: wms_url,
                    dataType: 'json',
                    success: function (result) {
                        var comid = result["features"][0]["properties"]["COMID"];
                        var startdate = '';
                        var watershed = (result["features"][0]["properties"]["watershed"]).toLowerCase();
                        var subbasin = (result["features"][0]["properties"]["subbasin"]).toLowerCase();
                        var workspace = 'spt-30935191ace55f90bd1e61456f1ef016';

                        var model = 'ecmwf-rapid';
                        $('#info').addClass('hidden');
                        add_feature(workspace,watershed,subbasin,comid);

                        get_available_dates(watershed, subbasin,comid);
                        get_time_series(model, watershed, subbasin, comid, startdate);
                    },
                    error: function (XMLHttpRequest, textStatus, errorThrown) {
                        console.log(Error);
                    }
                });
            }
        } else {
            $("#container").empty()
            $("#container").append('</h1><p>Please click on a valid stream.</p>');
        }
    });

}

function add_feature(workspace,watershed,subbasin,comid){
    map.removeLayer(featureOverlay);

    var vectorSource = new ol.source.Vector({
        format: new ol.format.GeoJSON(),
        url: function (extent) {
            return 'http://tethys.byu.edu:8181/geoserver/ows?service=wfs&' +
                'version=2.0.0&request=getfeature&typename='+workspace+':'+watershed+'-'+subbasin+'-drainage_line'+'&CQL_FILTER=COMID='+comid+'&outputFormat=application/json&srsname=EPSG:3857&' + ',EPSG:3857';
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
    map.getLayers().item(5)

}
$(function(){
    $('#app-content-wrapper').removeClass('show-nav');
    $(".toggle-nav").removeClass('toggle-nav');
    init_map();
    map_events();
    $('#datesSelect').change(function() { //when date is changed
        var sel_val = ($('#datesSelect option:selected').val()).split(',');
        var startdate = sel_val[0];
        var watershed = sel_val[1];
        var subbasin = sel_val[2];
        var comid = sel_val[3];
        var model = 'ecmwf-rapid';
        get_time_series(model, watershed, subbasin, comid, startdate);
    });
});