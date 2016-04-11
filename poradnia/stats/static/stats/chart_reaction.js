var margin = {top: 20, right: 30, bottom: 30, left: 40},
    width = 960 - margin.left - margin.right,
    height = 500 - margin.top - margin.bottom;

var legendRectSize = 16,
    legendSpacing = 4;

var x = d3.time.scale()
    .range([0, width]);

var y = d3.scale.linear()
    .range([height, 0]);

var color = d3.scale.category20c();

var xAxis = d3.svg.axis()
    .scale(x)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(y)
    .orient("left");

var parseDate = d3.time.format("%Y-%m-%d").parse;

var area = d3.svg.area()
    .interpolate("monotone")
    .x(function(d) { return x(d.date); })
    .y0(function(d) { return y(0); })
    .y1(function(d) { return y(d.time_delta); });

var chart = d3.select(".chart")
    .attr("viewBox", "0 0 "
                     + (width + margin.left + margin.right)
                     + " "
                     + (height + margin.top + margin.bottom))
    .attr("preserveAspectRatio", "xMinYMin meet")
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

function legendWrapper(domain, config) {

  var domain = domain,
      config = config;

  function legend(vis) {

      var legend = vis.selectAll('.legend')
          .data(domain)
        .enter()
          .append('g')
          .attr('class', 'legend')
          .attr('transform', function(d, i) {
            var height = config.legendRectSize + config.legendSpacing;
            var horz = config.legendRectSize;
            var vert = i * height;
            return 'translate(' + horz + ',' + vert + ')';
          });

      legend.append('rect')
          .attr('width', config.legendRectSize)
          .attr('height', config.legendRectSize)
          .style('fill', (function(d) { return color(d); }));

      legend.append('text')
          .attr('x', config.legendSpacing + config.legendRectSize)
          .attr('y', config.legendSpacing + config.legendRectSize / 2)
          .text(function(d) { return d; });
      }

  return legend;
}

function reaction_chart(error, data) {
  if (error) throw error;

  data.forEach(function(d) {
    d.date = parseDate(d.date);
  });

  x.domain(d3.extent(data, function(d) { return d.date; }));
  y.domain([0, d3.max(data, function(d) { return d.time_delta; })]);

  color.domain(d3.keys(data[0]).filter(function(key) { return key !== "date"; }));

  chart.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

  chart.append("g")
      .attr("class", "y axis")
      .call(yAxis);

  chart.append("path")
      .datum(data)
      .attr("class", "area")
      .attr("d", area)
      .style("fill", color("time_delta"));

  var legend = legendWrapper(color.domain(), {'legendSpacing': legendSpacing, 'legendRectSize': legendRectSize});

  chart.call(legend);
}
