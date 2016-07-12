function createdChart(url) {
  var chart = timeSeriesChart();
  var keys = ["open", "assigned", "closed"];
  chart(url, keys);
}
