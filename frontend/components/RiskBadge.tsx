'use client';

import { useState, useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { RiskLevel, RiskExplanation } from '@/lib/types';

const RISK_CATEGORIES = [
  {
    title: 'Regulatory & Legal Indicators',
    items: [
      'Active sanctions listings',
      'Criminal investigations/charges',
      'Civil enforcement actions',
      'Regulatory violations/fines',
      'Pending investigations',
      'Past resolved issues (>3 years)',
    ],
  },
  {
    title: 'Media Signal Strength',
    items: [
      'Official government sources (treasury.gov, justice.gov, state.gov)',
      'Major credible news (Reuters, Bloomberg, WSJ, AP)',
      'General media/blogs',
    ],
  },
  {
    title: 'Severity Factors',
    items: [
      'National security concerns',
      'Financial crimes (money laundering, fraud)',
      'Export control violations',
      'Corruption/bribery',
      'Environmental/labor violations',
      'Civil disputes',
    ],
  },
  {
    title: 'Temporal Relevance',
    items: [
      'Issues within last 6 months',
      'Issues within last 1 year',
      'Issues within last 3 years',
      'Older than 3 years',
    ],
  },
];

interface RiskBadgeProps {
  level: RiskLevel;
  size?: 'sm' | 'md' | 'lg';
  explanation?: RiskExplanation;
  /** When false, only the ? button is rendered (the badge is omitted — replaced by a dropdown in the parent). */
  showBadge?: boolean;
}

const riskConfig: Record<RiskLevel, { label: string; clearance: string }> = {
  SAFE:      { label: 'Safe',           clearance: 'CLEARED' },
  LOW:       { label: 'Low Risk',       clearance: 'LOW RISK' },
  MID:       { label: 'Medium Risk',    clearance: 'MODERATE' },
  HIGH:      { label: 'High Risk',      clearance: 'HIGH RISK' },
  VERY_HIGH: { label: 'Very High Risk', clearance: 'CRITICAL' },
};

function YesNoPill({ flagged }: { flagged: boolean }) {
  return (
    <span
      className="font-data"
      style={{
        fontSize: '0.7rem',
        padding: '0.1rem 0.45rem',
        background: flagged ? 'rgba(245, 180, 0, 0.12)' : 'rgba(255,255,255,0.04)',
        border: `1px solid ${flagged ? 'var(--amber-primary)' : 'var(--border-dim)'}`,
        color: flagged ? 'var(--amber-light)' : 'var(--text-muted)',
        letterSpacing: '0.08em',
        whiteSpace: 'nowrap' as const,
        flexShrink: 0,
      }}
    >
      {flagged ? 'YES' : 'NO'}
    </span>
  );
}

export default function RiskBadge({
  level,
  size = 'md',
  explanation,
  showBadge = true,
}: RiskBadgeProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  const config = riskConfig[level];

  const badgeSize = {
    sm: { fontSize: '0.75rem', padding: '0.22rem 0.6rem' },
    md: { fontSize: '0.75rem', padding: '0.25rem 0.7rem' },
    lg: { fontSize: '0.75rem', padding: '0.3rem 0.85rem' },
  }[size];

  const indicatorMap = useMemo(
    () =>
      new Map<string, boolean>(
        (explanation?.indicator_results ?? []).map((r) => [
          r.indicator.toLowerCase().trim(),
          r.flagged,
        ])
      ),
    [explanation?.indicator_results],
  );

  const yesCount = explanation?.yes_count ?? null;
  const totalCount = explanation?.total_count ?? null;

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
      {/* Classification badge — omitted when showBadge=false (parent renders a dropdown instead) */}
      {showBadge && (
        <span
          className={`risk-badge risk-badge-${level}`}
          style={{ ...badgeSize, cursor: explanation ? 'pointer' : 'default' }}
          onClick={explanation ? () => setShowExplanation(true) : undefined}
          title={explanation ? 'Click to view risk assessment details' : config.label}
        >
          {config.clearance}
        </span>
      )}

      {/* Info trigger */}
      {explanation && (
        <button
          onClick={() => setShowExplanation(true)}
          style={{
            width: '20px',
            height: '20px',
            background: 'var(--bg-panel)',
            border: '1px solid var(--border-main)',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            letterSpacing: 0,
            transition: 'border-color 0.2s, color 0.2s',
            flexShrink: 0,
          }}
          onMouseEnter={e => {
            e.currentTarget.style.borderColor = 'var(--amber-primary)';
            e.currentTarget.style.color = 'var(--amber-light)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.borderColor = 'var(--border-main)';
            e.currentTarget.style.color = 'var(--text-muted)';
          }}
          title="View risk categories"
          aria-label="Show risk categories"
        >
          ?
        </button>
      )}

      {/* ── Modal ── */}
      {showExplanation && explanation && mounted && createPortal(
        <>
          {/* Backdrop */}
          <div
            style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(4, 8, 15, 0.85)',
              zIndex: 9000,
              backdropFilter: 'blur(2px)',
            }}
            onClick={() => setShowExplanation(false)}
          />

          {/* Panel */}
          <div
            className="animate-fadeIn"
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-main)',
              zIndex: 9001,
              width: 'min(680px, 95vw)',
              maxHeight: '85vh',
              overflowY: 'auto',
              boxShadow: '0 0 60px rgba(0,0,0,0.6), 0 0 0 1px var(--border-dim)',
            }}
          >
            {/* Modal header */}
            <div
              style={{
                borderBottom: '1px solid var(--border-dim)',
                padding: '1rem 1.25rem',
                background: 'var(--bg-panel)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                position: 'sticky',
                top: 0,
                zIndex: 1,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <span className={`risk-badge risk-badge-${level}`} style={{ fontSize: '0.75rem' }}>
                  {config.clearance}
                </span>
                <span
                  className="font-editorial"
                  style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-bright)' }}
                >
                  Risk Assessment Details
                </span>
              </div>
              <button
                onClick={() => setShowExplanation(false)}
                style={{
                  background: 'transparent',
                  border: '1px solid var(--border-dim)',
                  color: 'var(--text-muted)',
                  width: '28px',
                  height: '28px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1rem',
                  transition: 'border-color 0.2s, color 0.2s',
                  flexShrink: 0,
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = 'var(--risk-critical)';
                  e.currentTarget.style.color = 'var(--risk-critical-bright)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border-dim)';
                  e.currentTarget.style.color = 'var(--text-muted)';
                }}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>

            {/* Modal body */}
            <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

              {/* Sanctions signal */}
              <div>
                <div className="label-stamp" style={{ marginBottom: '0.4rem' }}>
                  Sanctions Screening
                </div>
                <p
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    color: 'var(--text-main)',
                    margin: 0,
                    lineHeight: 1.6,
                    letterSpacing: '0.02em',
                  }}
                >
                  {explanation.sanctions_signal}
                </p>
              </div>

              <div style={{ borderTop: '1px solid var(--border-dim)' }} />

              {/* Intelligence signal + Risk Categories summary */}
              <div>
                <div className="label-stamp" style={{ marginBottom: '0.4rem' }}>
                  Intelligence Analysis
                </div>
                <p
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    color: 'var(--text-main)',
                    margin: 0,
                    lineHeight: 1.6,
                  }}
                >
                  {explanation.intelligence_signal}
                </p>

                {/* Risk Categories counter */}
                {yesCount !== null && totalCount !== null && totalCount > 0 && (
                  <div
                    style={{
                      marginTop: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                    }}
                  >
                    <div className="label-stamp" style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                      Risk Categories
                    </div>
                    <span
                      className="font-data"
                      style={{
                        fontSize: '0.85rem',
                        color: yesCount > 0 ? 'var(--amber-light)' : 'var(--risk-safe-bright)',
                      }}
                    >
                      {yesCount}
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {' '}/ {totalCount} flagged
                      </span>
                    </span>
                  </div>
                )}
              </div>

              {/* Risk Results accordion */}
              <div
                style={{
                  borderTop: '1px solid var(--border-dim)',
                  paddingTop: '1rem',
                }}
              >
                <button
                  onClick={() => setShowResults(!showResults)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    padding: 0,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    width: '100%',
                    transition: 'opacity 0.2s',
                  }}
                >
                  <span className="label-stamp-bright" style={{ fontSize: '0.75rem' }}>
                    Risk Results
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.75rem',
                      color: 'var(--amber-primary)',
                      transition: 'transform 0.2s',
                      display: 'inline-block',
                      transform: showResults ? 'rotate(180deg)' : 'none',
                    }}
                  >
                    ▾
                  </span>
                </button>

                {showResults && (
                  <div
                    className="animate-fadeIn"
                    style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}
                  >
                    {explanation.indicator_results && explanation.indicator_results.length > 0 ? (
                      RISK_CATEGORIES.map((category) => (
                        <div
                          key={category.title}
                          style={{ border: '1px solid var(--border-dim)', overflow: 'hidden' }}
                        >
                          <div
                            style={{
                              background: 'var(--bg-panel)',
                              borderBottom: '1px solid var(--border-dim)',
                              padding: '0.5rem 0.875rem',
                            }}
                          >
                            <span
                              className="label-stamp"
                              style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}
                            >
                              {category.title}
                            </span>
                          </div>
                          {category.items.map((itemLabel) => {
                            const key = itemLabel.toLowerCase().trim();
                            // fuzzy match: check if any indicator key contains our label or vice versa
                            let flagged: boolean | undefined;
                            for (const [k, v] of indicatorMap.entries()) {
                              if (k.includes(key.slice(0, 20)) || key.includes(k.slice(0, 20))) {
                                flagged = v;
                                break;
                              }
                            }
                            return (
                              <div
                                key={itemLabel}
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  gap: '1rem',
                                  padding: '0.375rem 0.875rem',
                                  borderBottom: '1px solid var(--border-void)',
                                }}
                              >
                                <span
                                  style={{
                                    fontFamily: 'var(--font-mono)',
                                    fontSize: '0.7rem',
                                    color: 'var(--text-secondary)',
                                  }}
                                >
                                  {itemLabel}
                                </span>
                                {flagged !== undefined ? (
                                  <YesNoPill flagged={flagged} />
                                ) : (
                                  <span
                                    className="font-data"
                                    style={{ fontSize: '0.7rem', color: 'var(--text-muted)', flexShrink: 0 }}
                                  >
                                    —
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      ))
                    ) : (
                      <p
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.75rem',
                          color: 'var(--text-muted)',
                          margin: 0,
                        }}
                      >
                        No indicator data available for this record.
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Footer */}
              <p
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  color: 'var(--text-muted)',
                  margin: 0,
                  lineHeight: 1.6,
                  borderTop: '1px solid var(--border-void)',
                  paddingTop: '0.875rem',
                }}
              >
                Indicator results are factual extractions from open-source intelligence. Staff should review all available evidence before reaching a determination.
              </p>
            </div>
          </div>
        </>,
        document.body
      )}
    </div>
  );
}
