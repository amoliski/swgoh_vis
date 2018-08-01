var c_manager = {
    data: undefined,
    fetch_data(){
        $.getJSON('//amoliski.pythonanywhere.com/swgoh/static/cache.json', function(data){
          this.data = data;
      });
    }

}








function c_manager(){
    var data;
    var parent = this;


    function fetch_data(){
      $.getJSON('/static/cache.json', function(data){
          parent.data = data;
      });

    };



}












  function init_gp_chart(datasets, index, timestamps){
        var entry_count = timestamps.length;
        var chart;
        for(var usr_data = 0; usr_data < datasets.length; usr_data++){
            var user = datasets[usr_data];
            if(user['data'].length < entry_count){
                var diff = entry_count - user['data'].length;
                for(var c = 0; c < diff; c++){
                    user['data'].unshift(NaN);
                }
            }
        }
        var config = {
                type: 'line',
                data: {labels: timestamps,datasets: datasets},
                options: {
                    responsive: true,
                    title:{display:true,text:'Total GP per User'},
                    hover: {mode: 'nearest',intersect: true},
                    scales: {
                        xAxes: [{type:'time', time:{
                            unit:'day',
                            unitStepSize: 1,
                            displayFormats: {
                                'day': 'MM/DD/YY'
                            }
                        }, display: true, scaleLabel: {display: true,labelString: 'Date'}}],
                        yAxes: [{display: true,scaleLabel: {display: true,labelString: 'Value'}}]
                    },
                }
            };
        var ctx = document.getElementById("canvas"+index).getContext("2d");
        console.log(config);
        chart = new Chart(ctx, config);
    }
    function init_overall_gp_chart(gp, timestamps){
        var chart;
        var config = {
                type: 'line',
                data: {labels: timestamps, datasets:  [{
                data: gp,
                backgroundColor: "rgb(0, 153, 255)",
                borderColor: "rgb(0, 133, 245)",
                fill: true,
                label: "Guild GP",
            }]},
                options: {
                    responsive: true,
                    title:{display:true,text:'Guild GP Growth'},
                    hover: {mode: 'nearest',intersect: true},
                    scales: {
                        xAxes: [{type:'time', time:{
                            unit:'day',
                            unitStepSize: 1,
                            displayFormats: {
                                'day': 'MM/DD/YY'
                            }
                        }, display: true, scaleLabel: {display: true,labelString: 'Date'}}],
                        yAxes: [{display: true,scaleLabel: {display: true,labelString: 'Value'}}]
                    },
                }
            };

        var ctx = document.getElementById("gpcanvas").getContext("2d");
        console.log(config);
        chart = new Chart(ctx, config);
    }
    function init_growth_chart(diffs, timestamps){

        var growth_chart = null;
        var config = {
                type: 'line',
                data: {labels: timestamps, datasets: diffs},
                options: {
                    responsive: true,
                    title:{display:true,text:'GP Growth'},
                    // tooltips: {mode: 'index',intersect: false,},
                    hover: {mode: 'nearest',intersect: true},
                    scales: {
                        xAxes: [{type:'time', time:{
                            unit:'day',
                            unitStepSize: 1,
                            displayFormats: {
                                'day': 'MM/DD/YY'
                            }
                        }, display: true, scaleLabel: {display: true,labelString: 'Date'}}],
                        yAxes: [{display: true,scaleLabel: {display: true,labelString: 'Value'}}]
                    },
                    legend:{
                        onHover: function(e, legend_item){
                            for(var i = 0; i < growth_chart.data.datasets.length; i++){
                                if(growth_chart.data.datasets[i].transColor){
                                    growth_chart.data.datasets[i].backgroundColor = growth_chart.data.datasets[i].transColor;
                                    growth_chart.data.datasets[i].borderColor = growth_chart.data.datasets[i].transColor;
                                }
                            }
                            var dsi = legend_item.datasetIndex;
                            growth_chart.hoveringLegendIndex = dsi;
                            var ds = growth_chart.data.datasets[dsi];
                            ds.backgroundColor = "red";
                            ds.borderColor = "red";

                            growth_chart.update()
                        }

                    },
                }
            };
            ctx = document.getElementById("canvas").getContext("2d");
            growth_chart = new Chart(ctx, config);



            growth_chart.hoveringLegendIndex = -1
            growth_chart.canvas.addEventListener('mousemove', function(e) {
              if (growth_chart.hoveringLegendIndex >= 0) {
                if (e.layerX < growth_chart.legend.left || growth_chart.legend.right < e.layerX
                  || e.layerY < growth_chart.legend.top || growth_chart.legend.bottom < e.layerY
                ) {
                  growth_chart.hoveringLegendIndex = -1
                  for (var i = 0; i < growth_chart.data.datasets.length; i++) {
                    var dataset = growth_chart.data.datasets[i]
                    dataset.borderColor = dataset.backupColor
                    dataset.backgroundColor = dataset.backupColor
                  }
                  growth_chart.update()
                }
              }
            })

    }

    function init_weekly_growth_chart(diffs, timestamps){

        var growth_chart = null;
        var config = {
                type: 'line',
                data: {labels: timestamps, datasets: diffs},
                options: {
                    responsive: true,
                    title:{display:true,text:'GP Growth (7 days)'},
                    // tooltips: {mode: 'index',intersect: false,},
                    hover: {mode: 'nearest',intersect: true},
                    scales: {
                        xAxes: [{type:'time', time:{
                            unit:'day',
                            unitStepSize: 1,
                            displayFormats: {
                                'day': 'MM/DD/YY'
                            }
                        }, display: true, scaleLabel: {display: true,labelString: 'Date'}}],
                        yAxes: [{display: true,scaleLabel: {display: true,labelString: 'Value'}}]
                    },
                    legend:{
                        onHover: function(e, legend_item){
                            for(var i = 0; i < growth_chart.data.datasets.length; i++){
                                if(growth_chart.data.datasets[i].transColor){
                                    growth_chart.data.datasets[i].backgroundColor = growth_chart.data.datasets[i].transColor;
                                    growth_chart.data.datasets[i].borderColor = growth_chart.data.datasets[i].transColor;
                                }
                            }
                            var dsi = legend_item.datasetIndex;
                            growth_chart.hoveringLegendIndex = dsi;
                            var ds = growth_chart.data.datasets[dsi];
                            ds.backgroundColor = "red";
                            ds.borderColor = "red";

                            growth_chart.update()
                        }

                    },
                }
            };
            ctx = document.getElementById("week_growth").getContext("2d");
            growth_chart = new Chart(ctx, config);



            growth_chart.hoveringLegendIndex = -1
            growth_chart.canvas.addEventListener('mousemove', function(e) {
              if (growth_chart.hoveringLegendIndex >= 0) {
                if (e.layerX < growth_chart.legend.left || growth_chart.legend.right < e.layerX
                  || e.layerY < growth_chart.legend.top || growth_chart.legend.bottom < e.layerY
                ) {
                  growth_chart.hoveringLegendIndex = -1
                  for (var i = 0; i < growth_chart.data.datasets.length; i++) {
                    var dataset = growth_chart.data.datasets[i]
                    dataset.borderColor = dataset.backupColor
                    dataset.backgroundColor = dataset.backupColor
                  }
                  growth_chart.update()
                }
              }
            })

    }

    function addMinutes(date, minutes) {
        return new Date(date.getTime() + minutes*60000);
    }

    function get_timestamps(timestrings){
        var timestamps = [];
        for(var k = 0; k < timestrings.length; k++){
            var date = new Date(timestrings[k]);
            date = addMinutes(date, -60*6);
            timestamps.push(date);
        }
        return timestamps
    }

    function init_charts(data, timestrings, gp, all_growth, weekly_growth){
        var timestamps = get_timestamps(timestrings);
        // For each user gp chart (split up for readability with ~13 users on each chart)
        data.reverse();
        for(var j = 0; j < data.length; j++){
            init_gp_chart(data[j], j, timestamps)
        }
        init_growth_chart(all_growth.data, all_growth.timestamps);
        init_overall_gp_chart(gp, timestamps);
        init_weekly_growth_chart(weekly_growth.data, weekly_growth.timestamps);



    }

    //$.getJSON('/static/cache.json', function(data){
    //    console.log(data);
    //    init_charts(data['charts'], data['timestamps'], data['gp'], data['all_growth'], data['weekly_growth']);
    //});
