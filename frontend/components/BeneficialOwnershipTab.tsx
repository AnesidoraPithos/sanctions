"use client";

import { BeneficialOwner } from "@/lib/types";

interface BeneficialOwnershipTabProps {
  beneficialOwners: BeneficialOwner[];
}

function SourceBadge({ source }: { source: string }) {
  const isOccrp = source.toLowerCase().includes("occrp") || source.toLowerCase().includes("aleph");
  const isOpenOwnership =
    source.toLowerCase().includes("openownership") ||
    source.toLowerCase().includes("open ownership");

  const style: React.CSSProperties = {
    fontFamily: 'var(--font-mono)',
    fontSize: '0.65rem',
    letterSpacing: '0.08em',
    textTransform: 'uppercase' as const,
    padding: '0.2rem 0.5rem',
    border: '1px solid',
    display: 'inline-block',
  };

  if (isOccrp) {
    return (
      <span style={{ ...style, background: 'rgba(168,112,8,0.12)', borderColor: 'var(--amber-primary)', color: 'var(--amber-light)' }}>
        OCCRP
      </span>
    );
  }
  if (isOpenOwnership) {
    return (
      <span style={{ ...style, background: 'rgba(0,188,188,0.1)', borderColor: 'var(--cyan-main)', color: 'var(--cyan-bright)' }}>
        OpenOwnership
      </span>
    );
  }
  return (
    <span style={{ ...style, background: 'var(--bg-panel)', borderColor: 'var(--border-main)', color: 'var(--text-muted)' }}>
      {source}
    </span>
  );
}

const thStyle: React.CSSProperties = {
  padding: '0.5rem 1rem',
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

export default function BeneficialOwnershipTab({
  beneficialOwners,
}: BeneficialOwnershipTabProps) {
  if (!beneficialOwners || beneficialOwners.length === 0) {
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
          No beneficial ownership records found in OCCRP Aleph or the Open
          Ownership Register for this entity.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Summary */}
      <div
        style={{
          background: 'rgba(0,188,188,0.06)',
          border: '1px solid var(--cyan-dark)',
          borderLeft: '3px solid var(--cyan-main)',
          padding: '0.875rem 1rem',
        }}
      >
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', margin: 0, lineHeight: 1.5 }}>
          <span style={{ color: 'var(--cyan-bright)', fontWeight: 600 }}>{beneficialOwners.length}</span>{" "}
          beneficial owner record{beneficialOwners.length !== 1 ? "s" : ""}{" "}
          retrieved from OCCRP Aleph and the Open Ownership Register.
        </p>
      </div>

      {/* Table */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr>
                <th style={thStyle}>Name</th>
                <th style={thStyle}>Nationality</th>
                <th style={thStyle}>Ownership %</th>
                <th style={thStyle}>Source</th>
                <th style={thStyle}>Verification Date</th>
              </tr>
            </thead>
            <tbody>
              {beneficialOwners.map((owner, idx) => (
                <tr
                  key={idx}
                  style={{
                    background: idx % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-panel)',
                    borderBottom: '1px solid var(--border-void)',
                  }}
                >
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span style={{ color: 'var(--text-bright)', fontWeight: 500, fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {owner.name}
                    </span>
                    {owner.source_url && (
                      <div>
                        <a
                          href={owner.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: 'var(--amber-primary)', fontSize: '0.72rem', fontFamily: 'var(--font-mono)', textDecoration: 'none', letterSpacing: '0.04em' }}
                        >
                          View record →
                        </a>
                      </div>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
                    {owner.nationality || "—"}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
                    {owner.ownership_pct != null
                      ? `${owner.ownership_pct.toFixed(1)}%`
                      : "—"}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <SourceBadge source={owner.source} />
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                    {owner.verification_date || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
