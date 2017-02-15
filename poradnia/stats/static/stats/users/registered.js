function registeredChart(url) {
  var chart = timeSeriesChart();
  var keys = ["count"];
  chart(url, keys);
}
