var area = d3.svg.area()
    .interpolate("monotone")
    .x(function(d) { return x(d.date); })
    .y0(function(d) { return y(d.y0); })
    .y1(function(d) { return y(d.y0 + d.y); });

var stack = d3.layout.stack()
    .values(function(d) { return d.values; });

var chart = d3.select(".chart")
    .attr("viewBox", "0 0 "
                     + (width + margin.left + margin.right)
                     + " "
                     + (height + margin.top + margin.bottom))
    .attr("preserveAspectRatio", "xMinYMin meet")
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

function created_chart(error, data) {
  if (error) throw error;

  data.forEach(function(d) {
    d.date = parseDate(d.date);
  });

  x.domain(d3.extent(data, function(d) { return d.date; }));
  y.domain([0, d3.max(data, function(d) { return d.closed + d.assigned + d.open; })]);
  xAxis.ticks(data.length);

  color.domain(d3.keys(data[0]).filter(function(key) { return key !== "date"; }));

  var statuses = stack(color.domain().map(function(status) {
      return {
        status: status,
        values: data.map(function(d) {
          return {date: d.date, y: d[status]};
        })
      }
  }));

  chart.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

  chart.append("g")
      .attr("class", "y axis")
      .call(yAxis);

  var status = chart.selectAll(".status")
      .data(statuses)
    .enter().append("g")
      .attr("class", "status")

  status.append("path")
      .attr("class", "area")
      .attr("d", function(d) { return area(d.values); })
      .style("fill", function(d) { return color(d.status); });

      var legend = d3Legend(color.domain(), {'legendSpacing': legendSpacing, 'legendRectSize': legendRectSize});

      chart.call(legend);
}
