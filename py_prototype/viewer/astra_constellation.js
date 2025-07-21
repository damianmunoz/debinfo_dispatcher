fetch('deb_graph.json')
  .then(res => res.json())
  .then(data => {
    
    data.nodes.forEach(node => {
      switch (node.group) {
        case 'Principal': node.z = -300; break;
        case 'Step': node.z = -150; break;
        case 'Resource': node.z = 0; break;
        case 'Artifact': node.z = 150; break;
        default: node.z = 300;
      }

      
      node.fx = null;
      node.fy = null;
    });

    
    const Graph = ForceGraph3D()(document.body)
      .graphData(data)
      .nodeLabel(node => `${node.group}: ${node.id}`)
      .nodeAutoColorBy('group')
      .linkLabel(link => link.label)
      .linkWidth(1.5)
      .linkDirectionalParticles(2)
      .linkDirectionalParticleSpeed(0.005)
      .linkColor(link => {
        switch (link.label) {
          case 'used_by': return 'deepskyblue';
          case 'carries_out': return 'violet';
          case 'produces': return 'gold';
          case 'consumes': return 'tomato';
          default: return 'gray';
        }
      })
      .nodeThreeObjectExtend(true) 
      .d3Force('charge').strength(-200); 
  });

