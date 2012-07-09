function resp_perc_parser(s) {
    /* Add fields to data series object according to it's name.
    Args:
        s: dict, data series.
    Returns:
        s: dict, ready to be added highcharts data series
           for respoce percentiles chart.
    */
    var series_color = {
        'rps': '#990000',
        '100': '#002A8F',
        '99': '#7CB3F1',
        '98': '#35962B',
        '95': '#CAF100',
        '90': '#F9FD5F',
        '85': '#EAAF00',
        '80': '#FF7D00',
        '75': '#FF5700',
        '50': '#F51D30',
    };

    var up_common = {
        legendIndex: 0,
        color: series_color[s.name],
        marker: {
          enabled: false
        },
    };
    $.extend(s, up_common); 
    
    if (s.name == 'rps') {
        up = {
            type: 'line',
            yAxis: 1,
        };
    } else if (parseInt(s.name) < 99) {
        up = {
            name: s.name + '%',
            type: 'area',
        };
    } else if (parseInt(s.name) >= 99) {
        up = {
            name: s.name + '%',
            type: 'line',
        };
    } else {
        console.error('Unknown series name: ' + s.name)
    };
    
    $.extend(s, up); 
    return s;
}

function status_codes_parser(s) {
    /* Add fields to data series object according to it's name.
    Args:
        s: dict, data series.
    Returns:
        s: dict, ready to be added highcharts data series
           for HTTP status codes chart.
    */

    // see: http://httpstatus.es/
    function color_by_name(name) {
        if (name == 'rps') {
            return '#990000'
        };
        var group = parseInt(name / 100)
        if (group == 1) {
            color = '#FFE175';
        } else if (group == 2) {
            color = '#68B160';
        } else if (group == 3) {
            color = '#6FD1E0';
        } else if (group == 4) {
            color = '#5258B6';
        } else if (group == 5) {
            color = '#F8584F';
        } else {
            color = '#640092';
        };
        return color
    }

    var up_common = {
        legendIndex: 0,
        color: color_by_name(s.name),
        //color: series_color[s.name],
        marker: {
          enabled: false
        },
    };
    $.extend(s, up_common); 
    
    if (s.name == 'rps') {
        up = {
            type: 'line',
            yAxis: 1,
        };
    } else if (s.name > 99 && s.name < 600) {
        up = {
            type: 'area',
        };
    } else {
        console.error('Unknown series name: ' + s.name)
    };
    
    $.extend(s, up); 
    return s;
}

function errno_parser(s) {
    /* Add fields to data series object according to it's name.
    Args:
        s: dict, data series.
    Returns:
        s: dict, ready to be added highcharts data series
           for errno chart.
    */

    function generateColors(pointsNum) {
        var scope = 255,
            step = Math.round(scope / pointsNum),
            colors = [];
    
        for (var i=0; i<pointsNum; i++) {
            // rgb(96, 96, 96)'
            //colors.push([step * (i+1), 0 , scope - step * (i+1)]);
            colors.push ('rgb(' + step * (i+1) + ', ' + 0 + ', ' + scope - step * (i+1 + ')'));
        }
    
        return colors;
    }
    // see: https://gist.github.com/2413028
    var colors = generateColors(132)
    function color_by_name(name, colors) {
        if (name == 'rps') {
            return '#990000'
        };
        color = colors[name]
        return color
    }

    var up_common = {
        legendIndex: 0,
        color: color_by_name(s.name, colors),
        marker: {
          enabled: false
        },
    };
    $.extend(s, up_common); 
    
    if (s.name == 'rps') {
        up = {
            type: 'line',
            yAxis: 1,
        };
    } else if (s.name > -1 && s.name < 200) {
        up = {
            type: 'area',
        };
    } else {
        console.error('Unknown series name: ' + s.name)
    };
    
    $.extend(s, up); 
    return s;
}



function base_chart(container_id, data_series, praser, opts_up) {
    /* Create highcharts chart object with default params.
    Args:
        container_id: str, DOM id to place chart in.
        data_series: dict, will be used by praser.
        praser: function, prepares data_series.
    Returns:
        nothing, just create a chart.
    */

    var opts = {
        'title': 'Some Title',
        //'subtitle': 'Any text here?',
        'subtitle': '',
        'yTitle': 'Responce Everywere',
        'postfix': ' ppc',
        'info_link': 'https://github.com/greggyNapalm/firebat_console',
    };

    $.extend(opts, opts_up);

    Highcharts.setOptions({
        global: {
            useUTC: false
        },
        lang: {
            infoTitle: 'info?',
        }
    });
    var chart;
    chart = new Highcharts.Chart({
        chart: {
            renderTo: container_id,
            zoomType: 'x',
            animation: false,
            backgroundColor: '#f9f9f9',
            type: 'areaspline',
        },

        credits: {
            enabled: false
        },

        title: {
            text: opts.title
        },

        subtitle: {
            text: opts.subtitle
        },

        xAxis: [{
            type: 'datetime',
        }],

        yAxis: [{ // Primary yAxis
            labels: {
                formatter: function() {
                    return this.value + opts.postfix;
                },
                style: {
                    color: '#89A54E'
                }
            },
            title: {
                text: opts.yTitle,
                style: {
                    color: '#89A54E'
                }
            }
        }, { // Secondary yAxis
            title: {
                text: 'Load',
                style: {
                    color: '#4572A7'
                }
            },
            labels: {
                formatter: function() {
                    return this.value +' rps';
                },
                style: {
                    color: '#4572A7'
                }
            },
            opposite: true
        }],

        plotOptions: {
            area: {
                fillOpacity: 1,
                lineWidth: 0,
                animation: false,
            },
        },

        tooltip: {
            backgroundColor: 'white',
            borderRadius: '10',
            borderColor: 'black',
            borderWidth: 2,
            shared: true,
            crosshairs: {
                color: 'black',
                dashStyle: 'solid',
            },
            formatter: function() {
                var point = this.points[this.points.length-1]
                //return Highcharts.dateFormat('%B %e, %H:%M:%S', this.x) + '<br>' + this.points[2].y + ' rps';
                return Highcharts.dateFormat('%B %e, %H:%M:%S', this.x) + '<br>' + point.y + ' rps';
            },
        },

        exporting: {
            buttons: {
                testButton: {
                    //symbol: 'url(./img/sun.png)',
                    symbol: 'diamond',
                    x: -62,
                    symbolFill: '#B5C9DF',
                    hoverSymbolFill: '#779ABF',
                    _titleKey: 'infoTitle',
                    onclick: function() {
                        window.open(opts.info_link)
                    }
                }
            }
        }
    });

    $.each(data_series, function(index, s) {
        if (s.name != 'rps') {
            //console.info(s.name, s.data[55], s.data[56], s.data[57]);
            $.each(s.data, function(idx, value) {
                value[0] = value[0]*1000  // make js time stamp from epoach
            });
        };
        chart.addSeries(praser(s));
    });
}
