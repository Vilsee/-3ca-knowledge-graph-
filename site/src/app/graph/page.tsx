'use client';
import { useState, useEffect, useMemo, useRef } from 'react';
import GraphComponent from '@/components/GraphComponent';

export default function GraphPage() {
  const [graphData, setGraphData] = useState<{nodes: any[], links: any[]}>({ nodes: [], links: [] });
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Filters
  const [nodeColoring, setNodeColoring] = useState('By Node Type');
  const [relTypes, setRelTypes] = useState<Record<string, boolean>>({
    'STUDIES_CANCER_TYPE': true,
    'HAS_DISEASE': true,
    'USES_TECH': true,
    'SHARES_DISEASE_WITH': false
  });
  const [minScore, setMinScore] = useState(0);
  const [edgeThreshold, setEdgeThreshold] = useState(0);
  
  const [selectedNode, setSelectedNode] = useState<any>(null);

  useEffect(() => {
    fetch('/data/kg.json')
      .then(res => res.json())
      .then(data => {
        const links = data.edges || data.links || [];
        
        // Pre-process nodes to have size (degree) and standard colors
        const degreeMap: Record<string, number> = {};
        links.forEach((l: any) => {
          degreeMap[l.source] = (degreeMap[l.source] || 0) + 1;
          degreeMap[l.target] = (degreeMap[l.target] || 0) + 1;
        });
        
        const nodes = (data.nodes || []).map((n: any) => {
          // Identify type from prefix or attribute
          let type = n.type || 'Unknown';
          if (n.id.startsWith('study_')) type = 'Study';
          if (n.id.startsWith('cancertype_')) type = 'CancerType';
          if (n.id.startsWith('disease_')) type = 'Disease';
          if (n.id.startsWith('tech_')) type = 'Technology';
          
          return {
            ...n,
            type,
            label: n.title || n.id.replace(/^(study_|cancertype_|disease_|tech_)/, ''),
            size: type === 'Study' ? Math.max(3, (degreeMap[n.id] || 1) * 0.5) : 8
          };
        });
        
        setGraphData({ nodes, links });
      });
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight
      });
      
      const handleResize = () => {
        if (containerRef.current) {
          setDimensions({
            width: containerRef.current.clientWidth,
            height: containerRef.current.clientHeight
          });
        }
      };
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, []);

  const getNodeColor = (node: any) => {
    if (nodeColoring === 'By Node Type') {
      if (node.type === 'Study') return '#3b82f6'; // Blue
      if (node.type === 'CancerType') return '#ef4444'; // Red
      if (node.type === 'Disease') return '#22c55e'; // Green
      if (node.type === 'Technology') return '#f97316'; // Orange
    }
    return '#888888';
  };

  const filteredData = useMemo(() => {
    const validLinks = graphData.links.filter(link => {
      // relationship type toggle
      const type = link.type || (link.weight ? 'SHARES_DISEASE_WITH' : 'UNKNOWN'); // fallback
      if (!relTypes[type] && relTypes[type] !== undefined) return false;
      
      // weight thresholds
      if (type === 'SHARES_DISEASE_WITH') {
        const weight = link.weight || 1;
        if (weight < minScore) return false;
      }
      
      return true;
    });

    const validNodeIds = new Set();
    validLinks.forEach(l => {
      validNodeIds.add(l.source.id || l.source);
      validNodeIds.add(l.target.id || l.target);
    });
    
    // Always include isolated nodes if they haven't been filtered globally?
    // The user's density slider usually prunes low-degree nodes. 
    // For simplicity, we just filter nodes that have no valid links.
    const validNodes = graphData.nodes.filter(n => validNodeIds.has(n.id));

    return { nodes: validNodes, links: validLinks };
  }, [graphData, relTypes, minScore, edgeThreshold]);

  const toggleRelType = (type: string) => {
    setRelTypes(prev => ({ ...prev, [type]: !prev[type] }));
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[#05080F]">
      {/* Left Sidebar - Controls */}
      <div className="w-[300px] bg-[#0A0F1C] border-r border-white/5 flex flex-col z-10 shrink-0 overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold text-white mb-2">Network Configuration</h2>
          
          <div className="mt-8 space-y-6">
            <div>
              <label className="text-white/60 text-xs font-medium uppercase tracking-wider mb-2 block">Select Node Coloring</label>
              <select 
                className="w-full bg-[#05080F] border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#EF4444]"
                value={nodeColoring}
                onChange={e => setNodeColoring(e.target.value)}
              >
                <option>By Node Type</option>
                <option>Monochrome</option>
              </select>
            </div>

            <div>
              <label className="text-white/60 text-xs font-medium uppercase tracking-wider mb-2 block">Relationship Type</label>
              <div className="space-y-2 bg-[#05080F] p-3 rounded-md border border-white/5">
                {Object.keys(relTypes).map(type => (
                  <label key={type} className="flex items-center gap-3 cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={relTypes[type]} 
                      onChange={() => toggleRelType(type)}
                      className="accent-[#3b82f6]"
                    />
                    <span className="text-sm text-white/80">{type}</span>
                  </label>
                ))}
              </div>
            </div>
            
            <div>
              <label className="text-white/60 text-xs font-medium uppercase tracking-wider flex justify-between mb-2">
                <span>Min. Association Score</span>
                <span className="text-[#3b82f6]">{minScore}</span>
              </label>
              <input 
                type="range" 
                min="0" max="10" step="1" 
                value={minScore} 
                onChange={e => setMinScore(parseInt(e.target.value))}
                className="w-full accent-[#3b82f6]"
              />
              <div className="flex justify-between text-white/30 text-[10px] mt-1">
                <span>0</span>
                <span>10</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 relative" ref={containerRef}>
        <div className="absolute top-6 left-6 z-10 pointer-events-none">
          <h2 className="text-2xl font-bold text-white">Interactive Network Explorer</h2>
          <p className="text-white/50 text-sm">Graph Controls: scroll to zoom, drag to pan</p>
        </div>
        
        {graphData.nodes.length > 0 && (
          <GraphComponent
            graphData={filteredData}
            width={dimensions.width}
            height={dimensions.height}
            nodeColor={getNodeColor}
            nodeVal={(n: any) => n.size || 5}
            nodeLabel={(n: any) => n.label}
            linkColor={() => 'rgba(255,255,255,0.1)'}
            onNodeClick={(node: any) => setSelectedNode(node)}
            backgroundColor="#05080F"
          />
        )}
      </div>

      {/* Right Sidebar - Stats */}
      <div className="w-[280px] bg-[#0A0F1C] border-l border-white/5 flex flex-col z-10 shrink-0">
        <div className="p-6 flex-1 overflow-y-auto">
          <h3 className="text-white text-sm font-bold uppercase tracking-wider mb-4 border-b border-white/10 pb-2">Network Stats</h3>
          <div className="mb-8">
            <div className="text-white/60 text-sm mb-1">Nodes: <span className="text-white ml-2">{filteredData.nodes.length}</span></div>
            <div className="text-white/60 text-sm">Edges: <span className="text-white ml-2">{filteredData.links.length}</span></div>
          </div>

          <h3 className="text-white text-sm font-bold uppercase tracking-wider mb-4 border-b border-white/10 pb-2">Node Legend</h3>
          <div className="mb-8 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-[#3b82f6]"></div>
              <span className="text-white/80 text-sm">Study</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-[#ef4444]"></div>
              <span className="text-white/80 text-sm">Cancer Type</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-[#22c55e]"></div>
              <span className="text-white/80 text-sm">Disease</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-[#f97316]"></div>
              <span className="text-white/80 text-sm">Technology</span>
            </div>
          </div>

          <h3 className="text-white text-sm font-bold uppercase tracking-wider mb-4 border-b border-white/10 pb-2">Selected Node</h3>
          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <div className="text-white/50 text-[10px] uppercase tracking-wider mb-1">ID</div>
                <div className="text-white text-sm break-all font-mono">{selectedNode.id}</div>
              </div>
              <div>
                <div className="text-white/50 text-[10px] uppercase tracking-wider mb-1">Type</div>
                <div className="text-white text-sm">{selectedNode.type}</div>
              </div>
              <div>
                <div className="text-white/50 text-[10px] uppercase tracking-wider mb-1">Label</div>
                <div className="text-white text-sm">{selectedNode.label}</div>
              </div>
              {selectedNode.type === 'Study' && (
                <>
                  <div>
                    <div className="text-white/50 text-[10px] uppercase tracking-wider mb-1">Degree (Size)</div>
                    <div className="text-white text-sm">{selectedNode.size * 2}</div>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="text-white/30 text-sm italic">Click a node to view details.</div>
          )}
        </div>
      </div>
    </div>
  );
}
