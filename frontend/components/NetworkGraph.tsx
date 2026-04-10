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

// Dossier palette for graph nodes
const NODE_COLORS = {
  parent:      "#a87008",  // amber-primary
  subsidiary:  "#00bcd4",  // cyan-main
  sister:      "#d4a017",  // amber-light
  director:    "#e89b0c",  // amber-main
  shareholder: "#7a5800",  // amber-deep
};

const labelStyle: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: '0.7rem',
  letterSpacing: '0.08em',
  color: 'var(--text-muted)',
};

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

    const cy = cytoscape({
      container: containerRef.current,
      elements: {
        nodes: networkData.nodes,
        edges: networkData.edges,
      },
      style: [
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
            color: "#e8d5a0",
            "text-outline-color": "#050c17",
            "text-outline-width": 2,
          },
        },
        {
          selector: "node[node_type = 'parent']",
          style: {
            "background-color": NODE_COLORS.parent,
            "border-width": 3,
            "border-color": "#d4a017",
          },
        },
        {
          selector: "node[node_type = 'subsidiary']",
          style: {
            "background-color": NODE_COLORS.subsidiary,
          },
        },
        {
          selector: "node[node_type = 'sister']",
          style: {
            "background-color": NODE_COLORS.sister,
          },
        },
        {
          selector: "node[node_type = 'director']",
          style: {
            "background-color": NODE_COLORS.director,
            shape: "hexagon",
          },
        },
        {
          selector: "node[node_type = 'shareholder']",
          style: {
            "background-color": NODE_COLORS.shareholder,
            shape: "diamond",
          },
        },
        {
          selector: "node[sanctions_hit > 0]",
          style: {
            "border-width": 3,
            "border-color": "#ef4444",
            "border-style": "solid",
          },
        },
        {
          selector: "node:selected",
          style: {
            "border-width": 4,
            "border-color": "#f5c842",
            "background-color": "#c8960a",
          },
        },
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
        {
          selector: "edge:selected",
          style: {
            width: 3,
            "line-color": "#d4a017",
            "target-arrow-color": "#d4a017",
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

    cy.on("tap", "node", (evt) => {
      const node = evt.target;
      const nodeData = node.data();
      setSelectedNode(nodeData);
      if (onNodeClick) {
        onNodeClick(nodeData.id);
      }
    });

    cy.on("tap", (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cyRef.current = cy;

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
    cy.nodes('[node_type = "director"]').style("display", filters.showDirectors ? "element" : "none");
    cy.nodes('[node_type = "shareholder"]').style("display", filters.showShareholders ? "element" : "none");
    cy.edges('[relationship = "transacted_with"]').style("display", filters.showTransactions ? "element" : "none");
  }, [filters]);

  const exportAsPNG = () => {
    if (!cyRef.current) return;
    const png = cyRef.current.png({ full: true, scale: 2 });
    const link = document.createElement("a");
    link.download = "network-graph.png";
    link.href = png;
    link.click();
  };

  const fitGraph = () => {
    if (!cyRef.current) return;
    cyRef.current.fit(undefined, 50);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Controls */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          padding: '0.875rem 1rem',
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-dim)',
        }}
      >
        {/* Layout Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <label style={labelStyle}>Layout:</label>
          <select
            value={selectedLayout}
            onChange={(e) => setSelectedLayout(e.target.value as LayoutName)}
            className="intel-select"
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', minWidth: '8rem' }}
          >
            {LAYOUT_OPTIONS.map((option) => (
              <option key={option.name} value={option.name}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          {[
            { key: 'showDirectors', label: 'Directors' },
            { key: 'showShareholders', label: 'Shareholders' },
            { key: 'showTransactions', label: 'Transactions' },
          ].map(({ key, label }) => (
            <label
              key={key}
              style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', cursor: 'pointer', ...labelStyle }}
            >
              <input
                type="checkbox"
                checked={filters[key as keyof typeof filters]}
                onChange={(e) => setFilters({ ...filters, [key]: e.target.checked })}
                style={{ accentColor: 'var(--amber-primary)', width: '0.8rem', height: '0.8rem' }}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={fitGraph}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.65rem',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              padding: '0.3rem 0.75rem',
              background: 'transparent',
              border: '1px solid var(--border-main)',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--amber-primary)'; e.currentTarget.style.color = 'var(--amber-light)'; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-main)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
          >
            Fit to View
          </button>
          <button
            onClick={exportAsPNG}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.65rem',
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              padding: '0.3rem 0.75rem',
              background: 'var(--amber-primary)',
              border: '1px solid var(--amber-primary)',
              color: 'var(--bg-void)',
              cursor: 'pointer',
              fontWeight: 600,
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.background = 'var(--amber-light)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'var(--amber-primary)'; }}
          >
            Export PNG
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <div style={{ display: 'flex', gap: '1rem' }}>
        {/* Main Graph */}
        <div
          ref={containerRef}
          style={{
            height: `${height}px`,
            flex: 1,
            background: 'var(--bg-void)',
            border: '1px solid var(--border-dim)',
          }}
        />

        {/* Node Details Panel */}
        {selectedNode && (
          <div
            style={{
              width: '18rem',
              padding: '1rem',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-main)',
              overflowY: 'auto',
              maxHeight: `${height}px`,
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem',
            }}
          >
            <div>
              <h3
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: 'var(--text-bright)',
                  margin: '0 0 0.5rem 0',
                  lineHeight: 1.4,
                }}
              >
                {selectedNode.label}
              </h3>
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.62rem',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  padding: '0.15rem 0.5rem',
                  background: 'rgba(168,112,8,0.12)',
                  border: '1px solid var(--amber-deep)',
                  color: 'var(--amber-light)',
                  display: 'inline-block',
                }}
              >
                {selectedNode.node_type}
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
              {selectedNode.entity_type && (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>Type:</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{selectedNode.entity_type}</span>
                </div>
              )}
              {selectedNode.jurisdiction && (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>Jurisdiction:</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{selectedNode.jurisdiction}</span>
                </div>
              )}
              {selectedNode.ownership_pct !== undefined && (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>Ownership:</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{selectedNode.ownership_pct}%</span>
                </div>
              )}
              {selectedNode.title && (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>Title:</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{selectedNode.title}</span>
                </div>
              )}
              {selectedNode.nationality && (
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <span style={{ color: 'var(--text-muted)', flexShrink: 0 }}>Nationality:</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{selectedNode.nationality}</span>
                </div>
              )}
              {selectedNode.sanctions_hit > 0 && (
                <div
                  style={{
                    marginTop: '0.5rem',
                    padding: '0.5rem 0.75rem',
                    background: 'var(--risk-critical-bg)',
                    border: '1px solid var(--risk-critical)',
                  }}
                >
                  <span style={{ color: 'var(--risk-critical-bright)', fontWeight: 600, fontSize: '0.72rem' }}>
                    ⚠ {selectedNode.sanctions_hit} sanctions hit{selectedNode.sanctions_hit !== 1 ? 's' : ''}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div
        style={{
          padding: '0.875rem 1rem',
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-dim)',
        }}
      >
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          Legend
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: '0.625rem',
          }}
        >
          {[
            { color: NODE_COLORS.parent, label: 'Parent Company', shape: 'circle' },
            { color: NODE_COLORS.subsidiary, label: 'Subsidiary', shape: 'circle' },
            { color: NODE_COLORS.sister, label: 'Sister Company', shape: 'circle' },
            { color: NODE_COLORS.director, label: 'Director', shape: 'hexagon' },
            { color: NODE_COLORS.shareholder, label: 'Shareholder', shape: 'diamond' },
          ].map(({ color, label, shape }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div
                style={{
                  width: '0.875rem',
                  height: '0.875rem',
                  background: color,
                  flexShrink: 0,
                  borderRadius: shape === 'circle' ? '50%' : undefined,
                  clipPath: shape === 'hexagon'
                    ? 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)'
                    : shape === 'diamond'
                    ? 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)'
                    : undefined,
                }}
              />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                {label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Statistics */}
      {networkData.statistics && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: '1px',
            background: 'var(--border-void)',
            border: '1px solid var(--border-void)',
          }}
        >
          {[
            { value: networkData.statistics.total_nodes, label: 'Total Nodes' },
            { value: networkData.statistics.companies, label: 'Companies' },
            { value: networkData.statistics.people, label: 'People' },
            { value: networkData.statistics.num_countries || 0, label: 'Countries' },
          ].map(({ value, label }) => (
            <div
              key={label}
              style={{
                background: 'var(--bg-surface)',
                padding: '0.875rem 1rem',
              }}
            >
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: 'var(--amber-light)',
                  lineHeight: 1,
                  marginBottom: '0.25rem',
                }}
              >
                {value}
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                {label}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
