function d3Legend() {

  var color = null,
      mapping = {},
      gap = 5,
      rowHeight = 20;

  function legend(vis) {

      var legend = vis.selectAll('.legend')
          .data(color.domain())
        .enter()
          .append('g')
          .attr('class', 'legendItem')
          .attr('transform', function(d, i) {
            var height = rowHeight + gap;
            var horz = rowHeight;
            var vert = i * height;
            return 'translate(' + horz + ',' + vert + ')';
          });

      legend.append('rect')
          .attr('width', rowHeight)
          .attr('height', rowHeight)
          .style('fill', (function(d) { return color(d); }));

      legend.append('text')
          .attr('x', gap + rowHeight)
          .attr('y', gap + rowHeight / 2)
          .text(function(d) { return mapping[d] || d; });
      }

  legend.rowHeight = function(_) {
    return arguments.length ? (
      rowHeight = _,
      legend
    ) : rowHeight;
  };

  legend.gap = function(_) {
    return arguments.length ? (
      gap = _,
      legend
    ) : gap;
  };

  legend.color = function(_) {
    return arguments.length ? (
      color = _,
      legend
    ) : color;
  };

  legend.mapping = function(_) {
    return arguments.length ? (
      mapping = _,
      legend
    ) : mapping;
  };

  return legend;
}
