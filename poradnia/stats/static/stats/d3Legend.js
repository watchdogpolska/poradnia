function d3Legend(domain, config) {

  var domain = domain,
      config = config;

  function legend(vis) {

      var legend = vis.selectAll('.legend')
          .data(domain)
        .enter()
          .append('g')
          .attr('class', 'legend')
          .attr('transform', function(d, i) {
            var height = config.legendRectSize + config.legendSpacing;
            var horz = config.legendRectSize;
            var vert = i * height;
            return 'translate(' + horz + ',' + vert + ')';
          });

      legend.append('rect')
          .attr('width', config.legendRectSize)
          .attr('height', config.legendRectSize)
          .style('fill', (function(d) { return color(d); }));

      legend.append('text')
          .attr('x', config.legendSpacing + config.legendRectSize)
          .attr('y', config.legendSpacing + config.legendRectSize / 2)
          .text(function(d) { return d; });
      }

  return legend;
}
