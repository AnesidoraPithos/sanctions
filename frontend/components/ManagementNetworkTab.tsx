"use client";

import { useState } from "react";
import { DirectorPivot } from "@/lib/types";

interface ManagementNetworkTabProps {
  directorPivots: DirectorPivot[];
}

const thStyle: React.CSSProperties = {
  padding: '0.4rem 1rem',
  textAlign: 'left',
  fontFamily: 'var(--font-mono)',
  fontSize: '0.65rem',
  letterSpacing: '0.14em',
  textTransform: 'uppercase',
  color: 'var(--text-muted)',
  background: 'var(--bg-panel)',
  fontWeight: 500,
  borderBottom: '1px solid var(--border-main)',
};

export default function ManagementNetworkTab({
  directorPivots,
}: ManagementNetworkTabProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  if (!directorPivots || directorPivots.length === 0) {
    return (
      <div
        style={{
          background: 'var(--bg-panel)',
          border: '1px solid var(--border-dim)',
          padding: '2rem',
          textAlign: 'center',
        }}
      >
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', margin: 0 }}>
          No interlocking directorate data found. This may occur when SEC EDGAR
          has no filings linking directors to other companies.
        </p>
      </div>
    );
  }

  const toggle = (idx: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  const totalCompanies = directorPivots.reduce(
    (sum, p) => sum + (p.companies?.length || 0),
    0
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Summary */}
      <div
        style={{
          background: 'rgba(168,112,8,0.06)',
          border: '1px solid var(--amber-deep)',
          borderLeft: '3px solid var(--amber-primary)',
          padding: '0.875rem 1rem',
        }}
      >
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', margin: 0, lineHeight: 1.5 }}>
          <span style={{ color: 'var(--amber-light)', fontWeight: 600 }}>{directorPivots.length}</span>{" "}
          director{directorPivots.length !== 1 ? "s" : ""} analysed —{" "}
          <span style={{ color: 'var(--amber-light)', fontWeight: 600 }}>{totalCompanies}</span>{" "}
          interlocking company link{totalCompanies !== 1 ? "s" : ""} found via SEC EDGAR filings.
        </p>
      </div>

      {directorPivots.map((pivot, idx) => {
        const isOpen = expanded.has(idx);
        const companyCount = pivot.companies?.length || 0;
        const initial = pivot.director_name?.charAt(0)?.toUpperCase() || "?";

        return (
          <div
            key={idx}
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-dim)',
              overflow: 'hidden',
            }}
          >
            {/* Director card header */}
            <button
              type="button"
              onClick={() => toggle(idx)}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.875rem 1.25rem',
                textAlign: 'left',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
                transition: 'background 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-panel)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem' }}>
                {/* Avatar */}
                <div
                  style={{
                    width: '2rem',
                    height: '2rem',
                    background: 'rgba(168,112,8,0.1)',
                    border: '1px solid var(--amber-deep)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <span style={{ color: 'var(--amber-light)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 700 }}>
                    {initial}
                  </span>
                </div>
                <div>
                  <p style={{ margin: 0, fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-bright)', fontFamily: 'var(--font-mono)' }}>
                    {pivot.director_name || "Unknown"}
                  </p>
                  {pivot.title && (
                    <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', letterSpacing: '0.04em' }}>
                      {pivot.title}
                    </p>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.65rem',
                    letterSpacing: '0.08em',
                    padding: '0.2rem 0.5rem',
                    background: 'rgba(168,112,8,0.1)',
                    border: '1px solid var(--amber-deep)',
                    color: 'var(--amber-light)',
                  }}
                >
                  {companyCount} link{companyCount !== 1 ? "s" : ""}
                </span>
                <span style={{ color: 'var(--text-faint)', fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>
                  {isOpen ? "▲" : "▼"}
                </span>
              </div>
            </button>

            {/* Expanded company table */}
            {isOpen && (
              <div style={{ borderTop: '1px solid var(--border-dim)' }}>
                {companyCount === 0 ? (
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', padding: '1rem 1.25rem', margin: 0 }}>
                    No related company filings found for this director.
                  </p>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                      <thead>
                        <tr>
                          <th style={thStyle}>Company</th>
                          <th style={thStyle}>Role</th>
                          <th style={thStyle}>Filing Date</th>
                          <th style={thStyle}>Source</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pivot.companies.map((company, cIdx) => (
                          <tr
                            key={cIdx}
                            style={{
                              background: cIdx % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-panel)',
                              borderBottom: '1px solid var(--border-void)',
                            }}
                          >
                            <td style={{ padding: '0.625rem 1rem', color: 'var(--text-bright)', fontWeight: 500, fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
                              {company.company_name}
                            </td>
                            <td style={{ padding: '0.625rem 1rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                              {company.role || "—"}
                            </td>
                            <td style={{ padding: '0.625rem 1rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                              {company.filing_date || "—"}
                            </td>
                            <td style={{ padding: '0.625rem 1rem' }}>
                              {company.source_url ? (
                                <a
                                  href={company.source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{ color: 'var(--amber-primary)', fontSize: '0.72rem', fontFamily: 'var(--font-mono)', textDecoration: 'none', letterSpacing: '0.04em' }}
                                >
                                  SEC EDGAR →
                                </a>
                              ) : (
                                <span style={{ color: 'var(--text-faint)', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
