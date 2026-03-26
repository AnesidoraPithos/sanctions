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
    <div className="flex items-center gap-2">
      {buttons.map(({ format, label, icon }) => (
        <button
          key={format}
          onClick={() => handleExport(format)}
          disabled={loading !== null}
          title={`Export as ${label}`}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all
            ${loading === format
              ? "border-blue-600 bg-blue-950/40 text-blue-400 cursor-wait"
              : "border-gray-700 bg-gray-900/50 text-gray-300 hover:border-blue-600 hover:text-blue-300"
            }
            disabled:opacity-60
          `}
        >
          <span>{loading === format ? "⏳" : icon}</span>
          <span>{loading === format ? "Exporting…" : label}</span>
        </button>
      ))}
      {error && (
        <span className="text-xs text-red-400 ml-2">{error}</span>
      )}
    </div>
  );
}
