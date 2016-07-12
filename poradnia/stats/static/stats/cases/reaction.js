function reactionChart(url) {
  var chart = timeSeriesChart();
  var keys = ["reaction_time"];
  chart(url, keys);
}
