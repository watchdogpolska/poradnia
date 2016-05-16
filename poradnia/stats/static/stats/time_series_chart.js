function timeSeriesChart() {
  var margin = {top: 20, right: 30, bottom: 30, left: 40},
      width = 960 - margin.left - margin.right,
      height = 500 - margin.top - margin.bottom;

  var legendRowHeight = 16,
      legendGap = 4;

  var x = d3.time.scale().range([0, width]),
      y = d3.scale.linear().range([height, 0]),
      color = d3.scale.category20c();

  var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom")
      .tickFormat(tickFormat);

  var yAxis = d3.svg.axis()
      .scale(y)
      .orient("left");

  var chart = d3.select(".chart")
    .attr("viewBox", "0 0 "
                     + (width + margin.left + margin.right)
                     + " "
                     + (height + margin.top + margin.bottom))
    .attr("preserveAspectRatio", "xMinYMin meet")
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var area = d3.svg.area()
      .interpolate("monotone")
      .x(function(d) { return x(d.date); });

  var legend = d3Legend()
      .rowHeight(legendRowHeight)
      .gap(legendGap)
      .mapping(mapping);

  function f(url, keys) {

    d3.json(url, function(error, data) {
      if (error) throw error;

      var parseDate = localeFormat.timeFormat("%Y-%m-%d").parse;

      data.forEach(function(d) {
        d.date = parseDate(d.date);
      });

      color.domain(keys);

      x.domain(d3.extent(data, function(d) { return d.date; }));

      y.domain([0, d3.max(data, function(d) {
        return d3.sum(color.domain().map(function(key) {
          return d[key];
        }))
      })]);

      if (keys.length >= 1) {
        // stack
        var stack = d3.layout.stack()
            .values(function(d) { return d.values; });

        area.y0(function(d) { return y(d.y0); })
          .y1(function(d) { return y(d.y0 + d.y); });

        var layers = stack(color.domain().map(function(layer) {
            return {
              layer: layer,
              values: data.map(function(d) {
                return {date: d.date, y: d[layer]};
              })
            }
        }));

        var layer = chart.selectAll(".layer")
            .data(layers)
          .enter().append("g")
            .attr("class", "layer")
            .append("path")
                .attr("class", "area")
                .attr("d", function(d) { return area(d.values); })
                .style("fill", function(d) { return color(d.layer); });

      } else {
        // single
        var key = keys[0];

        area.y0(function(d) { return y(0); })
          .y1(function(d) { return y(d[key]); });

        chart.append("path")
            .datum(data)
            .attr("class", "area")
            .attr("d", area)
            .style("fill", color(key));
      }

      chart.append("g")
          .attr("class", "x axis")
          .attr("transform", "translate(0," + height + ")")
          .call(xAxis);

      chart.append("g")
          .attr("class", "y axis")
          .call(yAxis);

      legend.color(color);

      chart.append("g")
          .attr("class", "legend")
          .call(legend);
    });
  }

  return f;
}
