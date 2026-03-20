"use client";

import React, { useEffect, useRef, useState } from "react";
import cytoscape, { Core, LayoutOptions } from "cytoscape";
import { NetworkGraphProps } from "@/lib/types";

/**
 * NetworkGraph Component
 *
 * Interactive network graph visualization using Cytoscape.js
 * Displays entity relationships with zoom, pan, drag, and node selection
 */

type LayoutName = "breadthfirst" | "circle" | "concentric" | "grid" | "random";

const LAYOUT_OPTIONS: { name: LayoutName; label: string }[] = [
  { name: "breadthfirst", label: "Hierarchical" },
  { name: "concentric", label: "Concentric" },
  { name: "circle", label: "Circle" },
  { name: "grid", label: "Grid" },
];

export default function NetworkGraph({
  networkData,
  height = 600,
  onNodeClick,
}: NetworkGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [selectedLayout, setSelectedLayout] = useState<LayoutName>("breadthfirst");
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [filters, setFilters] = useState({
    showDirectors: true,
    showShareholders: true,
    showTransactions: true,
  });

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current || !networkData) return;

    // Create Cytoscape instance
    const cy = cytoscape({
      container: containerRef.current,
      elements: {
        nodes: networkData.nodes,
        edges: networkData.edges,
      },
      style: [
        // Node styles
        {
          selector: "node",
          style: {
            "background-color": "data(color)",
            label: "data(label)",
            width: "data(size)",
            height: "data(size)",
            "text-valign": "center",
            "text-halign": "center",
            "font-size": "10px",
            color: "#ffffff",
            "text-outline-color": "#0b1121",
            "text-outline-width": 2,
          },
        },
        // Parent company node
        {
          selector: "node[node_type = 'parent']",
          style: {
            "background-color": "#3b82f6",
            "border-width": 3,
            "border-color": "#60a5fa",
          },
        },
        // Subsidiary node
        {
          selector: "node[node_type = 'subsidiary']",
          style: {
            "background-color": "#10b981",
          },
        },
        // Sister company node
        {
          selector: "node[node_type = 'sister']",
          style: {
            "background-color": "#a855f7",
          },
        },
        // Director node
        {
          selector: "node[node_type = 'director']",
          style: {
            "background-color": "#f59e0b",
            shape: "hexagon",
          },
        },
        // Shareholder node
        {
          selector: "node[node_type = 'shareholder']",
          style: {
            "background-color": "#eab308",
            shape: "diamond",
          },
        },
        // Sanctions hit highlighting
        {
          selector: "node[sanctions_hit > 0]",
          style: {
            "border-width": 3,
            "border-color": "#ef4444",
            "border-style": "solid",
          },
        },
        // Selected node
        {
          selector: "node:selected",
          style: {
            "border-width": 4,
            "border-color": "#60a5fa",
            "background-color": "#2563eb",
          },
        },
        // Edge styles
        {
          selector: "edge",
          style: {
            width: "data(edge_width)",
            "line-color": "data(edge_color)",
            "target-arrow-color": "data(edge_color)",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            opacity: 0.6,
          },
        },
        // Selected edge
        {
          selector: "edge:selected",
          style: {
            width: 3,
            "line-color": "#60a5fa",
            "target-arrow-color": "#60a5fa",
            opacity: 1,
          },
        },
      ],
      layout: {
        name: selectedLayout,
        animate: true,
        animationDuration: 500,
      } as LayoutOptions,
      minZoom: 0.3,
      maxZoom: 3,
      wheelSensitivity: 0.2,
    });

    // Handle node click
    cy.on("tap", "node", (evt) => {
      const node = evt.target;
      const nodeData = node.data();
      setSelectedNode(nodeData);
      if (onNodeClick) {
        onNodeClick(nodeData.id);
      }
    });

    // Handle background click (deselect)
    cy.on("tap", (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;

    // Cleanup
    return () => {
      cy.destroy();
    };
  }, [networkData, onNodeClick]);

  // Update layout when changed
  useEffect(() => {
    if (!cyRef.current) return;

    const layout = cyRef.current.layout({
      name: selectedLayout,
      animate: true,
      animationDuration: 500,
    } as LayoutOptions);

    layout.run();
  }, [selectedLayout]);

  // Apply filters
  useEffect(() => {
    if (!cyRef.current) return;

    const cy = cyRef.current;

    // Show/hide director nodes
    cy.nodes('[node_type = "director"]').style(
      "display",
      filters.showDirectors ? "element" : "none"
    );

    // Show/hide shareholder nodes
    cy.nodes('[node_type = "shareholder"]').style(
      "display",
      filters.showShareholders ? "element" : "none"
    );

    // Show/hide transaction edges
    cy.edges('[relationship = "transacted_with"]').style(
      "display",
      filters.showTransactions ? "element" : "none"
    );
  }, [filters]);

  // Export graph as PNG
  const exportAsPNG = () => {
    if (!cyRef.current) return;

    const png = cyRef.current.png({ full: true, scale: 2 });
    const link = document.createElement("a");
    link.download = "network-graph.png";
    link.href = png;
    link.click();
  };

  // Fit graph to viewport
  const fitGraph = () => {
    if (!cyRef.current) return;
    cyRef.current.fit(undefined, 50);
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-gray-900/50 border border-gray-700 rounded-lg">
        {/* Layout Selector */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Layout:</label>
          <select
            value={selectedLayout}
            onChange={(e) => setSelectedLayout(e.target.value as LayoutName)}
            className="px-3 py-1.5 text-sm bg-gray-800 text-white border border-gray-600 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {LAYOUT_OPTIONS.map((option) => (
              <option key={option.name} value={option.name}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.showDirectors}
              onChange={(e) =>
                setFilters({ ...filters, showDirectors: e.target.checked })
              }
              className="rounded text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900"
            />
            <span>Directors</span>
          </label>

          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.showShareholders}
              onChange={(e) =>
                setFilters({ ...filters, showShareholders: e.target.checked })
              }
              className="rounded text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900"
            />
            <span>Shareholders</span>
          </label>

          <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.showTransactions}
              onChange={(e) =>
                setFilters({ ...filters, showTransactions: e.target.checked })
              }
              className="rounded text-blue-500 focus:ring-blue-500 focus:ring-offset-gray-900"
            />
            <span>Transactions</span>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={fitGraph}
            className="px-3 py-1.5 text-sm bg-gray-800 text-white border border-gray-600 rounded hover:bg-gray-700 transition"
          >
            Fit to View
          </button>
          <button
            onClick={exportAsPNG}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Export PNG
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <div className="flex gap-4">
        {/* Main Graph */}
        <div
          ref={containerRef}
          style={{ height: `${height}px` }}
          className="flex-1 bg-gray-950 border border-gray-700 rounded-lg"
        />

        {/* Node Details Panel */}
        {selectedNode && (
          <div className="w-80 p-4 bg-gray-900/50 border border-gray-700 rounded-lg space-y-3 overflow-y-auto"
           style={{ maxHeight: `${height}px` }}>
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">
                {selectedNode.label}
              </h3>
              <div className="inline-block px-2 py-1 text-xs rounded bg-blue-900/50 text-blue-300 mb-3">
                {selectedNode.node_type}
              </div>
            </div>

            <div className="space-y-2 text-sm">
              {selectedNode.entity_type && (
                <div>
                  <span className="text-gray-400">Type:</span>{" "}
                  <span className="text-white">{selectedNode.entity_type}</span>
                </div>
              )}

              {selectedNode.jurisdiction && (
                <div>
                  <span className="text-gray-400">Jurisdiction:</span>{" "}
                  <span className="text-white">{selectedNode.jurisdiction}</span>
                </div>
              )}

              {selectedNode.ownership_pct !== undefined && (
                <div>
                  <span className="text-gray-400">Ownership:</span>{" "}
                  <span className="text-white">{selectedNode.ownership_pct}%</span>
                </div>
              )}

              {selectedNode.title && (
                <div>
                  <span className="text-gray-400">Title:</span>{" "}
                  <span className="text-white">{selectedNode.title}</span>
                </div>
              )}

              {selectedNode.nationality && (
                <div>
                  <span className="text-gray-400">Nationality:</span>{" "}
                  <span className="text-white">{selectedNode.nationality}</span>
                </div>
              )}

              {selectedNode.sanctions_hit > 0 && (
                <div className="mt-3 p-2 bg-red-900/20 border border-red-700 rounded">
                  <span className="text-red-400 font-semibold">
                    ⚠️ {selectedNode.sanctions_hit} sanctions hit(s)
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="p-4 bg-gray-900/50 border border-gray-700 rounded-lg">
        <div className="text-sm font-medium text-gray-300 mb-3">Legend</div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-500"></div>
            <span className="text-gray-400">Parent Company</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-gray-400">Subsidiary</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-purple-500"></div>
            <span className="text-gray-400">Sister Company</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-orange-500" style={{ clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)" }}></div>
            <span className="text-gray-400">Director</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500" style={{ clipPath: "polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)" }}></div>
            <span className="text-gray-400">Shareholder</span>
          </div>
        </div>
      </div>

      {/* Statistics */}
      {networkData.statistics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-gray-900/50 border border-gray-700 rounded-lg">
            <div className="text-2xl font-bold text-blue-400">
              {networkData.statistics.total_nodes}
            </div>
            <div className="text-xs text-gray-400">Total Nodes</div>
          </div>
          <div className="p-3 bg-gray-900/50 border border-gray-700 rounded-lg">
            <div className="text-2xl font-bold text-green-400">
              {networkData.statistics.companies}
            </div>
            <div className="text-xs text-gray-400">Companies</div>
          </div>
          <div className="p-3 bg-gray-900/50 border border-gray-700 rounded-lg">
            <div className="text-2xl font-bold text-orange-400">
              {networkData.statistics.people}
            </div>
            <div className="text-xs text-gray-400">People</div>
          </div>
          <div className="p-3 bg-gray-900/50 border border-gray-700 rounded-lg">
            <div className="text-2xl font-bold text-purple-400">
              {networkData.statistics.num_countries || 0}
            </div>
            <div className="text-xs text-gray-400">Countries</div>
          </div>
        </div>
      )}
    </div>
  );
}
