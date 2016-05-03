var area = d3.svg.area()
    .interpolate("monotone")
    .x(function(d) { return x(d.date); })
    .y0(function(d) { return y(d.y0); })
    .y1(function(d) { return y(d.y0 + d.y); });

var stack = d3.layout.stack()
    .values(function(d) { return d.values; });

function created_chart(error, data) {
  if (error) throw error;

  data.forEach(function(d) {
    d.date = parseDate(d.date);
  });

  setAxisDomains(color, x, y, "date", data);

  var statuses = stack(color.domain().map(function(status) {
      return {
        status: status,
        values: data.map(function(d) {
          return {date: d.date, y: d[status]};
        })
      }
  }));

  var status = chart.selectAll(".status")
      .data(statuses)
    .enter().append("g")
      .attr("class", "status")

  status.append("path")
      .attr("class", "area")
      .attr("d", function(d) { return area(d.values); })
      .style("fill", function(d) { return color(d.status); });

  drawAxes(chart, xAxis, yAxis);

  var legend = d3Legend(color.domain(), legendConfig);
  chart.call(legend);
}
