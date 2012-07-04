function resp_time_chart1(var1,var2)
{
    console.info(var1);

}

function resp_time_chart(container_id, data_series) {
    var chart;
    chart = new Highcharts.Chart({
        chart: {
            renderTo: container_id,
            zoomType: 'x',
            animation: false,
            backgroundColor: '#f9f9f9',
            type: 'areaspline',
        },
        title: {
            text: 'Cхема нагрузки и распределение квантилей времён ответов'
        },
        subtitle: {
            text: 'Тут нужен какой-либо текст?'
        },
        xAxis: [{
            type: 'datetime',
        }],
        yAxis: [{ // Primary yAxis
            labels: {
                formatter: function() {
                    return this.value +'ms';
                },
                style: {
                    color: '#89A54E'
                }
            },
            title: {
                text: 'Responce Time',
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
                    return this.value +'rps';
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
            //backgroundColor: '#CCCCCC',
            borderRadius: '10',
            borderColor: 'black',
            borderWidth: 2,
            //backgroundColor: 'gray',
            shared: true,
            crosshairs: {
                color: 'black',
                dashStyle: 'solid',
            },
            formatter: function() {
                return Highcharts.dateFormat('%B %e, %H:%M:%S', this.x) + '<br>' + this.points[2].y + ' rps';
            },
        },
    });

    series_color = {
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

    $.each(data_series, function(index, s) {
            up_common = {
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
        chart.addSeries(s);
    });
}
