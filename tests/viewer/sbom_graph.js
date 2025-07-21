fetch('../output/kawipiko-sbom-cdx_graph.json') 
  .then(res => res.json()) // Fetch the SBOM graph data
  .then(data => { // Process the data
    // Initialize the ForceGraph3D instance with the fetched data
    const Graph = ForceGraph3D() // Create a new ForceGraph3D instance
      (document.body)
      .graphData(data)
      .nodeLabel(node => node.id)
      .nodeAutoColorBy('group')
      .linkLabel(link => link.label)
      .linkWidth(1.5)
      .linkDirectionalParticles(2)
      .linkDirectionalParticleSpeed(0.005);
  });
