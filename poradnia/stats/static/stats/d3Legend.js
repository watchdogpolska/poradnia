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
            var height = config.rectSize + config.spacing;
            var horz = config.rectSize;
            var vert = i * height;
            return 'translate(' + horz + ',' + vert + ')';
          });

      legend.append('rect')
          .attr('width', config.rectSize)
          .attr('height', config.rectSize)
          .style('fill', (function(d) { return color(d); }));

      legend.append('text')
          .attr('x', config.spacing + config.rectSize)
          .attr('y', config.spacing + config.rectSize / 2)
          .text(function(d) { return printable[d]; });
      }

  return legend;
}
