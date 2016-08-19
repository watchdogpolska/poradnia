function createdChart(url) {
  var chart = timeSeriesChart();
  var keys = ["staff", "client"];
  chart(url, keys);
}
