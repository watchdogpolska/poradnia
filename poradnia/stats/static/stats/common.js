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

var chart = d3.select(".chart")
  .attr("viewBox", "0 0 "
                   + (width + margin.left + margin.right)
                   + " "
                   + (height + margin.top + margin.bottom))
  .attr("preserveAspectRatio", "xMinYMin meet")
  .append("g")
  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

function setAxisDomains(color, x, y, dateKey, data) {
  color.domain(d3.keys(data[0]).filter(function(key) { return key !== dateKey; }));
  x.domain(d3.extent(data, function(d) { return d[dateKey]; }));
  y.domain([0, d3.max(data, function(d) {
    return arraySum(color.domain().map(function(key) {
      return d[key];
    }))
  })]);
}

function drawAxes(svg, xAxis, yAxis) {
  svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(0," + height + ")")
      .call(xAxis);

  svg.append("g")
      .attr("class", "y axis")
      .call(yAxis);
}

function arraySum(arr) {
  return arr.reduce(
    function(prev, curr) {
      return prev + curr;
    },
    0
  )
}
