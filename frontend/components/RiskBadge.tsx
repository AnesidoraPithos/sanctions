'use client';

import { useState, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { RiskLevel, RiskExplanation } from '@/lib/types';

const SCORING_METHODOLOGY = [
  {
    title: 'Regulatory & Legal Indicators',
    range: '0–50 pts',
    note: 'Highest item only',
    items: [
      { label: 'Active sanctions listings', pts: 50 },
      { label: 'Criminal investigations / charges', pts: 40 },
      { label: 'Civil enforcement actions', pts: 30 },
      { label: 'Regulatory violations / fines', pts: 25 },
      { label: 'Pending investigations', pts: 15 },
      { label: 'Past resolved issues (>3 years)', pts: 5 },
    ],
  },
  {
    title: 'Media Signal Strength',
    range: '0–20 pts',
    note: 'Additive up to max',
    items: [
      { label: 'Official gov sources (treasury.gov, justice.gov, state.gov)', pts: 10, suffix: 'each, max 20' },
      { label: 'Major credible news (Reuters, Bloomberg, WSJ, AP)', pts: 3, suffix: 'each, max 15' },
      { label: 'General media / blogs', pts: 1, suffix: 'each, max 5' },
    ],
  },
  {
    title: 'Severity Factors',
    range: '0–30 pts',
    note: 'Highest item only',
    items: [
      { label: 'National security concerns', pts: 30 },
      { label: 'Financial crimes (money laundering, fraud)', pts: 15 },
      { label: 'Export control violations', pts: 15 },
      { label: 'Corruption / bribery', pts: 12 },
      { label: 'Environmental / labor violations', pts: 8 },
      { label: 'Civil disputes', pts: 5 },
    ],
  },
  {
    title: 'Temporal Relevance',
    range: '0–10 pts',
    note: 'Highest item only',
    items: [
      { label: 'Issues within last 6 months', pts: 10 },
      { label: 'Issues within last 1 year', pts: 8 },
      { label: 'Issues within last 3 years', pts: 5 },
      { label: 'Older than 3 years', pts: 2 },
    ],
  },
];

interface RiskBadgeProps {
  level: RiskLevel;
  size?: 'sm' | 'md' | 'lg';
  explanation?: RiskExplanation;
}

const riskConfig: Record<RiskLevel, { label: string; clearance: string }> = {
  SAFE:      { label: 'Safe',           clearance: 'CLEARED' },
  LOW:       { label: 'Low Risk',       clearance: 'LOW RISK' },
  MID:       { label: 'Medium Risk',    clearance: 'MODERATE' },
  HIGH:      { label: 'High Risk',      clearance: 'HIGH RISK' },
  VERY_HIGH: { label: 'Very High Risk', clearance: 'CRITICAL' },
};

const RAW_SCORE_RE = /RAW:\s*(\d+)\s*→\s*SCORE:\s*(\d+)/;

function parseBreakdown(breakdown: string) {
  const rawScoreMatch = breakdown.match(RAW_SCORE_RE);
  const rawTotal = rawScoreMatch ? rawScoreMatch[1] : null;
  const cappedTotal = rawScoreMatch ? rawScoreMatch[2] : null;
  const wasCapped = rawTotal && cappedTotal && rawTotal !== cappedTotal;
  const segments = breakdown
    .replace(/\s*\|\s*RAW:.*$/, '')
    .split(' | ')
    .filter(Boolean);
  const rows = segments.map((seg) => {
    const colonIdx = seg.indexOf(':');
    if (colonIdx === -1) return { category: seg.trim(), detail: '' };
    return {
      category: seg.slice(0, colonIdx).trim(),
      detail: seg.slice(colonIdx + 1).trim(),
    };
  });
  return { rows, rawTotal, cappedTotal, wasCapped };
}

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 66
      ? 'var(--risk-critical)'
      : score >= 36
      ? 'var(--risk-mid)'
      : 'var(--risk-low)';

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: '0.375rem',
        }}
      >
        <span
          className="label-stamp"
          style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}
        >
          Intelligence Score
        </span>
        <span
          className="font-data"
          style={{ fontSize: '0.8rem', color: 'var(--amber-light)' }}
        >
          {score}
          <span style={{ fontSize: '0.75rem', color: 'var(--amber-primary)' }}>/100</span>
        </span>
      </div>
      <div
        style={{
          height: '4px',
          background: 'var(--bg-deep)',
          border: '1px solid var(--border-dim)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${score}%`,
            height: '100%',
            background: color,
            boxShadow: `0 0 8px ${color}`,
            transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        />
      </div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          marginTop: '0.25rem',
          letterSpacing: '0.06em',
        }}
      >
        <span>Low (0–35)</span>
        <span>Medium (36–65)</span>
        <span>High (66–100)</span>
      </div>
    </div>
  );
}

export default function RiskBadge({ level, size = 'md', explanation }: RiskBadgeProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [showMethodology, setShowMethodology] = useState(false);
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  const config = riskConfig[level];
  const parsedBreakdown = useMemo(
    () =>
      explanation?.intelligence_breakdown
        ? parseBreakdown(explanation.intelligence_breakdown)
        : null,
    [explanation?.intelligence_breakdown],
  );

  const badgeSize = {
    sm: { fontSize: '0.75rem', padding: '0.22rem 0.6rem' },
    md: { fontSize: '0.75rem', padding: '0.25rem 0.7rem' },
    lg: { fontSize: '0.75rem', padding: '0.3rem 0.85rem' },
  }[size];

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
      {/* Classification badge */}
      <span
        className={`risk-badge risk-badge-${level}`}
        style={{ ...badgeSize, cursor: explanation ? 'pointer' : 'default' }}
        onClick={explanation ? () => setShowExplanation(true) : undefined}
        title={explanation ? 'Click to view risk assessment breakdown' : config.label}
      >
        {config.clearance}
      </span>

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
          title="View risk assessment breakdown"
          aria-label="Show risk explanation"
        >
          ?
        </button>
      )}

      {/* ── Modal (portal → renders directly on <body>, outside all stacking contexts) ── */}
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
                  Risk Assessment Breakdown
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

              {/* Intelligence signal */}
              <div>
                <div className="label-stamp" style={{ marginBottom: '0.4rem' }}>
                  Intelligence Analysis
                </div>
                <p
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.8rem',
                    color: 'var(--text-main)',
                    margin: '0 0 0.875rem',
                    lineHeight: 1.6,
                  }}
                >
                  {explanation.intelligence_signal}
                </p>
                {explanation.intelligence_score !== null && (
                  <ScoreBar score={explanation.intelligence_score} />
                )}
              </div>

              {/* Scoring breakdown */}
              {parsedBreakdown && parsedBreakdown.rows.length > 0 && (
                <>
                  <div style={{ borderTop: '1px solid var(--border-dim)' }} />
                  <div>
                    <div className="label-stamp" style={{ marginBottom: '0.625rem' }}>
                      Score Breakdown
                    </div>
                    <div
                      style={{
                        border: '1px solid var(--border-dim)',
                        overflow: 'hidden',
                      }}
                    >
                      {parsedBreakdown.rows.map((row, i) => (
                        <div
                          key={i}
                          style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            justifyContent: 'space-between',
                            gap: '1rem',
                            padding: '0.5rem 0.875rem',
                            borderBottom:
                              i < parsedBreakdown.rows.length - 1
                                ? '1px solid var(--border-void)'
                                : 'none',
                            background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                          }}
                        >
                          <span
                            className="label-stamp"
                            style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}
                          >
                            {row.category}
                          </span>
                          <span
                            className="font-data"
                            style={{ fontSize: '0.75rem', color: 'var(--text-main)', textAlign: 'right', whiteSpace: 'nowrap' }}
                          >
                            {row.detail}
                          </span>
                        </div>
                      ))}
                      {parsedBreakdown.rawTotal && (
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            padding: '0.5rem 0.875rem',
                            background: 'var(--bg-panel)',
                            borderTop: '1px solid var(--border-main)',
                          }}
                        >
                          <span
                            className="font-data"
                            style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}
                          >
                            {parsedBreakdown.wasCapped
                              ? `Raw: ${parsedBreakdown.rawTotal} → Capped`
                              : 'Total Score'}
                          </span>
                          <span
                            className="font-data"
                            style={{ fontSize: '0.875rem', color: 'var(--amber-light)', fontWeight: 600 }}
                          >
                            {parsedBreakdown.cappedTotal}
                            <span style={{ fontSize: '0.75rem', color: 'var(--amber-primary)' }}>/100</span>
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}

              <div style={{ borderTop: '1px solid var(--border-dim)' }} />

              {/* Final reasoning */}
              <div>
                <div className="label-stamp" style={{ marginBottom: '0.4rem' }}>
                  Final Assessment
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
                  {explanation.final_reasoning}
                </p>
              </div>

              {/* Methodology accordion */}
              <div
                style={{
                  borderTop: '1px solid var(--border-dim)',
                  paddingTop: '1rem',
                }}
              >
                <button
                  onClick={() => setShowMethodology(!showMethodology)}
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
                  <span
                    className="label-stamp-bright"
                    style={{ fontSize: '0.75rem' }}
                  >
                    Scoring Methodology
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.75rem',
                      color: 'var(--amber-primary)',
                      transition: 'transform 0.2s',
                      display: 'inline-block',
                      transform: showMethodology ? 'rotate(180deg)' : 'none',
                    }}
                  >
                    ▾
                  </span>
                </button>

                {showMethodology && (
                  <div
                    className="animate-fadeIn"
                    style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}
                  >
                    <p
                      style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.7rem',
                        color: 'var(--text-muted)',
                        margin: 0,
                        lineHeight: 1.5,
                      }}
                    >
                      Total score is capped at 100. Raw sums exceeding 100 are displayed as capped.
                    </p>
                    {SCORING_METHODOLOGY.map((category) => (
                      <div
                        key={category.title}
                        style={{ border: '1px solid var(--border-dim)', overflow: 'hidden' }}
                      >
                        <div
                          style={{
                            background: 'var(--bg-panel)',
                            borderBottom: '1px solid var(--border-dim)',
                            padding: '0.5rem 0.875rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: '0.5rem',
                          }}
                        >
                          <span
                            className="label-stamp"
                            style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}
                          >
                            {category.title}
                          </span>
                          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexShrink: 0 }}>
                            <span className="font-data" style={{ fontSize: '0.75rem', color: 'var(--amber-primary)' }}>
                              {category.range}
                            </span>
                            <span
                              style={{
                                fontFamily: 'var(--font-mono)',
                                fontSize: '0.75rem',
                                color: 'var(--text-secondary)',
                                fontStyle: 'italic',
                              }}
                            >
                              {category.note}
                            </span>
                          </div>
                        </div>
                        {category.items.map((item) => (
                          <div
                            key={item.label}
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
                              {item.label}
                            </span>
                            <span
                              className="font-data"
                              style={{
                                fontSize: '0.72rem',
                                color: 'var(--text-main)',
                                whiteSpace: 'nowrap',
                                flexShrink: 0,
                              }}
                            >
                              {item.pts} pts
                              {'suffix' in item ? (
                                <span style={{ color: 'var(--text-muted)', marginLeft: '0.25rem' }}>
                                  ({item.suffix})
                                </span>
                              ) : null}
                            </span>
                          </div>
                        ))}
                      </div>
                    ))}

                    {/* Scale reference */}
                    <div style={{ border: '1px solid var(--border-dim)', overflow: 'hidden' }}>
                      {[
                        { label: 'LOW / SAFE',  range: '0–35',   color: 'var(--risk-low)' },
                        { label: 'MEDIUM',       range: '36–65',  color: 'var(--risk-mid)' },
                        { label: 'HIGH / CRITICAL', range: '66–100', color: 'var(--risk-critical)' },
                      ].map((tier, i, arr) => (
                        <div
                          key={tier.label}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.75rem',
                            padding: '0.375rem 0.875rem',
                            borderBottom: i < arr.length - 1 ? '1px solid var(--border-void)' : 'none',
                          }}
                        >
                          <div
                            style={{
                              width: '8px',
                              height: '8px',
                              background: tier.color,
                              flexShrink: 0,
                            }}
                          />
                          <span
                            className="font-data"
                            style={{ fontSize: '0.75rem', color: 'var(--text-main)', letterSpacing: '0.1em' }}
                          >
                            {tier.label}
                          </span>
                          <span
                            className="font-data"
                            style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 'auto' }}
                          >
                            {tier.range}
                          </span>
                        </div>
                      ))}
                    </div>
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
                Risk assessment combines sanctions screening with AI-powered intelligence analysis for a
                comprehensive compliance evaluation.
              </p>
            </div>
          </div>
        </>,
        document.body
      )}
    </div>
  );
}
