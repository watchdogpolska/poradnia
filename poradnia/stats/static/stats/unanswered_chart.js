var area = d3.svg.area()
    .interpolate("monotone")
    .x(function(d) { return x(d.date); })
    .y0(function(d) { return y(0); })
    .y1(function(d) { return y(d[color.domain()[0]]); });

function unanswered_chart(error, data) {
  if (error) throw error;

  data.forEach(function(d) {
    d.date = parseDate(d.date);
  });

  setAxisDomains(color, x, y, "date", data);

  chart.append("path")
      .datum(data)
      .attr("class", "area")
      .attr("d", area)
      .style("fill", color(color.domain()[0]));

  drawAxes(chart, xAxis, yAxis);

  var legend = d3Legend(color.domain(), {'legendSpacing': legendSpacing, 'legendRectSize': legendRectSize});
  chart.call(legend)
}
