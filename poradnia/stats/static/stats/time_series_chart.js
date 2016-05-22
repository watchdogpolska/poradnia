function timeSeriesChart() {
  var margin = {top: 20, right: 30, bottom: 30, left: 40},
      width = 960,
      height = 500,
      chartWidth = width - margin.left - margin.right,
      chartHeight = 400 - margin.top,
      extraWidth = width - margin.left - margin.right,
      extraHeight = 100 - margin.bottom - margin.top,
      extraSpacing = 100,
      extraMargin = 10;

  var legendRowHeight = 16,
      legendGap = 4;

  var x = d3.time.scale().range([0, chartWidth]),
      y = d3.scale.linear().range([chartHeight, 0]),
      color = d3.scale.category20c(),
      extraX = d3.scale.linear().range([0, extraWidth]);

  var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom")
      .tickFormat(tickFormat);

  var yAxis = d3.svg.axis()
      .scale(y)
      .orient("left");

  var svg = d3.select(".chart")
      .attr("viewBox", "0 0 "
                       + width
                       + " "
                       + height)
      .attr("preserveAspectRatio", "xMinYMin meet");

  var chart = svg.append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var area = d3.svg.area()
      .interpolate("monotone")
      .x(function(d) { return x(d.date); });

  var legend = d3Legend()
      .rowHeight(legendRowHeight)
      .gap(legendGap)
      .mapping(mapping);

  var extra = d3_extra.extra();

  var extraContainer = svg.append("g")
      .attr("transform", "translate(" + margin.left + "," + chartHeight + ")");

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

      legend.color(color);

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
          .attr("transform", "translate(0," + chartHeight + ")")
          .call(xAxis);

      chart.append("g")
          .attr("class", "y axis")
          .call(yAxis);

      chart.append("g")
          .attr("class", "legend")
          .call(legend);

      extra.data(data);

      extra.extras([
          function(data) {
            return {
              label: "max",
              value: d3.max(data, function(d) {
                return d3.sum(keys.map(function(key) { return d[key]; }))
              })
            }
          },
          function(data) {
            return {
              label: "min",
              value: d3.min(data, function(d) {
                return d3.sum(keys.map(function(key) { return d[key]; }))
              })
            }
          },
          function(data) {
            return {
              label: "mean",
              value: d3.mean(data, function(d) {
                return d3.sum(keys.map(function(key) { return d[key]; }))
              }).toFixed(2)
            }
          }
      ]).refresh();

      var extraG = extraContainer.selectAll(".extra")
          .data(extra.values())
        .enter().append("g")
          .attr("class", "extra")
          .attr("transform", function(d, i) { return "translate(" + (i * extraSpacing + extraMargin) + ", " + extraHeight + ")"; });

      extraG.append("rect")
          .attr("width", extraSpacing - 2 * extraMargin)
          .attr("height", extraHeight)
          .attr("rx", 10);

      extraG.append("text")
          .attr("x", extraSpacing / 2 - extraMargin)
          .attr("y", 20)
          .attr("text-anchor", "middle")
          .text(function(d) { return mapping[d.label]; });

      extraG.append("text")
          .attr("x", extraSpacing / 2 - extraMargin)
          .attr("y", 40)
          .attr("text-anchor", "middle")
          .text(function(d) { return d.value; });

    });
  }

  return f;
}
