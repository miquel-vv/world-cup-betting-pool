document.addEventListener("DOMContentLoaded", function (event){
    var path = $(location)[0].pathname.split('/')
    var type = path[1]
    var team = path.slice(-1)[0];
    console.log(type);
    console.log(team);
    $.getJSON("/api/v2/"+ type + "/" + team)
        .then(function(data){
            console.log(data)
            drawChart(data)
        })
})

function drawChart(country_data){
    
    country = Object.getOwnPropertyNames(country_data)[0]
    data = country_data[country]

    var svgWidth = document.querySelector('svg').parentNode.clientWidth - 20;
    var svgHeight = document.querySelector('svg').parentNode.clientHeight - 20;
    var svgPadding = 45;

    var barPadding = 10;
    var barWidth = (svgWidth-svgPadding*2)/data.length - barPadding;

    var max = d3.max(data, function(d){
        return d.points;
    })
    var min = 0;

    var graph = d3.select('svg')
        .attr("width", svgWidth)
        .attr("height", svgHeight);

    var yScale = d3.scaleLinear()
                    .domain([0, max+10])
                    .range([svgHeight - svgPadding, 0]);

    /* var maxPosition = data.reduce(function(a, b){
        return Math.max(a, b.position)
    }, 0) */

    var yScaleLine = d3.scaleLinear()
        .domain([1, 30])
        .range([svgPadding, svgHeight - svgPadding])
    
    var yAxis = d3.axisLeft(yScaleLine)
        .tickSize(-svgWidth + svgPadding*2)
        .tickSizeOuter(0)
        .tickValues([1,5,10,15,20,25,30]);
    
    var xScale = d3.scaleBand()
        .domain(data.map(function(d){
        return d.round;
        }))
        .range([svgPadding, svgWidth - svgPadding])
        .paddingInner(0.05);
    
    var xAxis = d3.axisBottom(xScale);

    graph
        .append("text")
        .attr("x", (svgWidth / 2))             
        .attr("y", (svgPadding / 2))
        .attr("text-anchor", "middle")  
        .style("font-size", "16px") 
        .style("text-decoration", "underline")  
        .text("Position and Points of " + country[0].toUpperCase() + country.substring(1));

    graph
        .append('g')
        .attr("transform", "translate(0,"+ (svgHeight - svgPadding/2) +")")
        .classed("xAxis", true)
        .call(xAxis);

    graph
      .append('g')
      .attr("transform", "translate("+svgPadding +","+svgPadding/2+")")
      .call(yAxis);

    graph.append('text')
        .attr('class', 'y label')
        .attr('text-anchor', 'end')
        .attr('x', -(svgHeight-svgPadding)/2)
        .attr('y', svgPadding/2)
        .attr('transform', 'rotate(-90)')
        .text('Position')

    var bars = graph.append('g')

    bars
      .selectAll("rect")
      .data(data)
      .enter()
      .append("rect")
        .attr("width", barWidth)
        .attr("height", function(d){
            return (svgHeight-svgPadding) - yScale(d.points);
        })
        .attr("y", function(d){
            return yScale(d.points) + svgPadding/2;
        })
        .attr("x", function(d){
            return xScale(d.round);
        })
        .classed("points", true)
        .attr("data-legend", function(d){return "Points"});
    
    bars
      .selectAll("text")
      .data(data)
      .enter()
      .append("text")
        .attr("x", function(d){
            return xScale(d.round) + barWidth/2;
        })
        .attr("y",function(d){
            return yScale(d.points) + svgPadding/3;
        })
        .classed("points_label", true)
        .text(function(d){
            return d.points + " Points";
        })
        .style("text-anchor", "middle");

    var line = d3.line()
        .x(function(d){
            return xScale(d.round) + barWidth/2;
        })
        .y(function(d){
            return yScaleLine(d.position) + svgPadding/2;
        });
    
    graph.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#6AB187")
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round")
        .attr("stroke-width", 2.5)
        .attr("d", line)
        .attr("data-legend", function(d){return "Position"});

    graph.selectAll(".dot")
        .data(data)
        .enter()
        .append("circle") 
        .attr("cx", function(d) { return xScale(d.round) + barWidth/2 })
        .attr("cy", function(d) { return yScaleLine(d.position) + svgPadding/2 })
        .attr("r", 5)
        .attr("fill", "#6AB187");
    
}