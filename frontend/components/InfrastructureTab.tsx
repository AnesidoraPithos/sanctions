"use client";

import { InfrastructureHit } from "@/lib/types";

interface InfrastructureTabProps {
  infrastructure: InfrastructureHit[];
}

export default function InfrastructureTab({
  infrastructure,
}: InfrastructureTabProps) {
  if (!infrastructure || infrastructure.length === 0) {
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
          No digital infrastructure data available. WHOIS correlation requires
          domains to be present in media intelligence results.
        </p>
      </div>
    );
  }

  const sharedCount = infrastructure.filter(
    (h) => (h.related_entities?.length || 0) > 0
  ).length;

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
          <span style={{ color: 'var(--cyan-bright)', fontWeight: 600 }}>{infrastructure.length}</span>{" "}
          domain{infrastructure.length !== 1 ? "s" : ""} analysed via WHOIS
          {sharedCount > 0 && (
            <>
              {" "}—{" "}
              <span style={{ color: 'var(--amber-light)', fontWeight: 600 }}>
                {sharedCount}
              </span>{" "}
              with shared registrant or nameserver infrastructure
            </>
          )}
          .
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '1rem',
        }}
      >
        {infrastructure.map((hit, idx) => {
          const hasRelated = (hit.related_entities?.length || 0) > 0;

          return (
            <div
              key={idx}
              style={{
                background: 'var(--bg-surface)',
                border: `1px solid ${hasRelated ? 'var(--amber-primary)' : 'var(--border-dim)'}`,
                padding: '1.25rem',
                position: 'relative',
              }}
            >
              {/* Domain header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.875rem', gap: '0.5rem', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.75rem',
                      letterSpacing: '0.04em',
                      padding: '0.2rem 0.5rem',
                      background: 'rgba(0,188,188,0.1)',
                      border: '1px solid var(--cyan-dark)',
                      color: 'var(--cyan-bright)',
                    }}
                  >
                    {hit.domain}
                  </span>
                  {hasRelated && (
                    <span
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.62rem',
                        letterSpacing: '0.1em',
                        textTransform: 'uppercase',
                        padding: '0.2rem 0.5rem',
                        background: 'rgba(168,112,8,0.12)',
                        border: '1px solid var(--amber-deep)',
                        color: 'var(--amber-light)',
                      }}
                    >
                      Shared infra
                    </span>
                  )}
                </div>
              </div>

              {/* WHOIS fields */}
              <dl style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                {hit.registrant_org && (
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <dt style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.08em', color: 'var(--text-muted)', width: '6rem', flexShrink: 0, paddingTop: '0.05rem' }}>
                      Registrant
                    </dt>
                    <dd style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-primary)', wordBreak: 'break-all', margin: 0 }}>
                      {hit.registrant_org}
                    </dd>
                  </div>
                )}
                {hit.registrar && (
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <dt style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.08em', color: 'var(--text-muted)', width: '6rem', flexShrink: 0, paddingTop: '0.05rem' }}>
                      Registrar
                    </dt>
                    <dd style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-secondary)', margin: 0 }}>
                      {hit.registrar}
                    </dd>
                  </div>
                )}
                {hit.creation_date && (
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <dt style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.08em', color: 'var(--text-muted)', width: '6rem', flexShrink: 0, paddingTop: '0.05rem' }}>
                      Created
                    </dt>
                    <dd style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-secondary)', margin: 0 }}>
                      {hit.creation_date}
                    </dd>
                  </div>
                )}
                {hit.nameservers && hit.nameservers.length > 0 && (
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <dt style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.08em', color: 'var(--text-muted)', width: '6rem', flexShrink: 0, paddingTop: '0.05rem' }}>
                      Nameservers
                    </dt>
                    <dd style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-primary)', margin: 0 }}>
                      {hit.nameservers.slice(0, 3).join(", ")}
                      {hit.nameservers.length > 3 && (
                        <span style={{ color: 'var(--text-faint)' }}>
                          {" "}+{hit.nameservers.length - 3} more
                        </span>
                      )}
                    </dd>
                  </div>
                )}
              </dl>

              {/* Related entity badges */}
              {hasRelated && (
                <div style={{ marginTop: '0.875rem', paddingTop: '0.875rem', borderTop: '1px solid var(--border-dim)' }}>
                  <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '0.5rem', marginTop: 0 }}>
                    Shares infrastructure with:
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                    {hit.related_entities.map((entity, eIdx) => (
                      <span
                        key={eIdx}
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.65rem',
                          letterSpacing: '0.04em',
                          padding: '0.2rem 0.5rem',
                          background: 'rgba(168,112,8,0.08)',
                          border: '1px solid var(--amber-deep)',
                          color: 'var(--amber-light)',
                        }}
                      >
                        {entity}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
