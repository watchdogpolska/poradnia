var area = d3.svg.area()
    .interpolate("monotone")
    .x(function(d) { return x(d.date); })
    .y0(function(d) { return y(0); })
    .y1(function(d) { return y(d.reaction_time); });

function reaction_chart(error, data) {
  if (error) throw error;

  data.forEach(function(d) {
    d.date = parseDate(d.date);
  });

  setAxisDomains(color, x, y, "date", data);

  chart.append("path")
      .datum(data)
      .attr("class", "area")
      .attr("d", area)
      .style("fill", color("reaction_time"));

  drawAxes(chart, xAxis, yAxis);

  var legend = d3Legend(color.domain(), legendConfig);
  chart.call(legend);
}
