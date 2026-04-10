"use client";

import { useState } from "react";

interface ExportControlsProps {
  searchId: string;
}

type ExportFormat = "pdf" | "excel" | "json";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * ExportControls — PDF / Excel / JSON download buttons for a search result.
 */
export default function ExportControls({ searchId }: ExportControlsProps) {
  const [loading, setLoading] = useState<ExportFormat | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (format: ExportFormat) => {
    setLoading(format);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/export/${searchId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail || `Export failed (${res.status})`);
      }

      const blob = await res.blob();
      const disposition = res.headers.get("Content-Disposition") || "";
      const filenamePart = disposition.match(/filename="?([^";]+)"?/);
      const filename = filenamePart?.[1] ?? `export_${searchId.slice(0, 8)}.${format === "excel" ? "xlsx" : format}`;

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setLoading(null);
    }
  };

  const buttons: { format: ExportFormat; label: string; icon: string }[] = [
    { format: "pdf", label: "PDF", icon: "📄" },
    { format: "excel", label: "Excel", icon: "📊" },
    { format: "json", label: "JSON", icon: "{ }" },
  ];

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.375rem' }}>
      {buttons.map(({ format, label }) => {
        const isActive = loading === format;
        return (
          <button
            key={format}
            onClick={() => handleExport(format)}
            disabled={loading !== null}
            title={`Export as ${label}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.375rem',
              padding: '0.375rem 0.625rem',
              fontSize: '0.65rem',
              fontFamily: 'var(--font-mono)',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              border: isActive ? '1px solid var(--amber-primary)' : '1px solid var(--border-main)',
              background: isActive ? 'var(--amber-pale)' : 'var(--bg-panel)',
              color: isActive ? 'var(--amber-deep)' : 'var(--text-secondary)',
              cursor: loading !== null ? (isActive ? 'wait' : 'not-allowed') : 'pointer',
              opacity: loading !== null && !isActive ? 0.5 : 1,
              transition: 'all 0.15s',
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={e => { if (!loading) { e.currentTarget.style.borderColor = 'var(--amber-primary)'; e.currentTarget.style.color = 'var(--amber-light)'; } }}
            onMouseLeave={e => { if (!loading) { e.currentTarget.style.borderColor = 'var(--border-main)'; e.currentTarget.style.color = 'var(--text-secondary)'; } }}
          >
            <span>{isActive ? '…' : '↓'}</span>
            <span>{isActive ? `${label}…` : label}</span>
          </button>
        );
      })}
      {error && (
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.65rem',
            color: 'var(--risk-critical-bright)',
            marginLeft: '0.25rem',
          }}
        >
          {error}
        </span>
      )}
    </div>
  );
}
