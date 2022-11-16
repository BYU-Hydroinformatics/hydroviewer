var create_rules = function(properties){
    var sld_rules = ''
    for (const element of properties) {
        sld_rules +=
        `<Rule>
        <Name>${element['val']}</Name>
        <ogc:Filter>
          <ogc:PropertyIsEqualTo>
            <ogc:PropertyName>${element['names']}</ogc:PropertyName>
            <ogc:Literal>${element['val']}</ogc:Literal>
          </ogc:PropertyIsEqualTo>
        </ogc:Filter>
        <LineSymbolizer>
          <Stroke>
            <CssParameter name="stroke">${element['stroke_color']}</CssParameter>
            <CssParameter name="stroke-width">${element['stroke_width']}</CssParameter>
          </Stroke>
        </LineSymbolizer>
      </Rule>`;
    };
    return sld_rules
}

var create_style = function(layer,properties){
    //console.log(layer);
    //Display styling for the selected watershed boundaries
    var sld_string =
        '<StyledLayerDescriptor version="1.0.0"\
        xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"\
        xmlns="http://www.opengis.net/sld"\
        xmlns:ogc="http://www.opengis.net/ogc"\
        xmlns:xlink="http://www.w3.org/1999/xlink"\
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'+
        '<NamedLayer><Name>' +
        layer +
        '</Name><UserStyle><FeatureTypeStyle>' +
        create_rules(properties) +
        '</FeatureTypeStyle>\
        </UserStyle>\
        </NamedLayer>\
        </StyledLayerDescriptor>';
    return sld_string
}

