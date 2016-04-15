var area = d3.svg.area()
    .interpolate("monotone")
    .x(function(d) { return x(d.date); })
    .y0(function(d) { return y(0); })
    .y1(function(d) { return y(d.count); });

var chart = d3.select(".chart")
    .attr("viewBox", "0 0 "
                     + (width + margin.left + margin.right)
                     + " "
                     + (height + margin.top + margin.bottom))
    .attr("preserveAspectRatio", "xMinYMin meet")
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

function unanswered_chart(error, data) {
  if (error) throw error;

  data.forEach(function(d) {
    d.date = parseDate(d.date);
  });

  x.domain(d3.extent(data, function(d) { return d.date; }));
  y.domain([0, d3.max(data, function(d) { return d.count; })]);
  xAxis.ticks(data.length);

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
      .style("fill", color("count"));

  var legend = d3Legend(color.domain(), {'legendSpacing': legendSpacing, 'legendRectSize': legendRectSize});

  chart.call(legend)
}
