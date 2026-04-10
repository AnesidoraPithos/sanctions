'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { api } from '@/lib/api-client';
import { HistoryEntry, RiskLevel, ResearchTier } from '@/lib/types';

const TIER_LABELS: Record<ResearchTier, string> = {
  base: 'Base',
  network: 'Network',
  deep: 'Deep',
};

function formatDate(ts: string) {
  try {
    return new Date(ts).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch {
    return ts;
  }
}

export default function SavedSearchesPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  useEffect(() => {
    api.getSavedSearches()
      .then((data) => { setEntries(data.entries); setIsLoading(false); })
      .catch(() => { setError('Failed to load saved searches'); setIsLoading(false); });
  }, []);

  const handleUnsave = async (searchId: string) => {
    setConfirmingId(null);
    setEntries((prev) => prev.filter((e) => e.search_id !== searchId));
    try {
      await api.unsaveResult(searchId);
    } catch {
      api.getSavedSearches().then((data) => setEntries(data.entries)).catch(() => {});
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-void)' }}>
      {/* Header — matches main page exactly */}
      <header style={{ borderBottom: '1px solid var(--border-dim)', background: 'var(--bg-deep)', position: 'relative', zIndex: 10 }}>
        <div style={{ height: '2px', background: 'linear-gradient(90deg, transparent, var(--amber-primary), transparent)' }} />
        <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '1.25rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '1rem', textDecoration: 'none' }}>
            <Image src="/bear-logo.png" alt="BEAR²" width={44} height={44} style={{ display: 'block', opacity: 0.9 }} />
            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
                <span className="font-display" style={{ fontSize: '2.2rem', lineHeight: 1, color: 'var(--amber-light)', letterSpacing: '0.08em' }}>BEAR</span>
                <span className="font-display" style={{ fontSize: '1.2rem', lineHeight: 1, color: 'var(--amber-primary)', verticalAlign: 'super' }}>2</span>
              </div>
              <div className="label-stamp" style={{ fontSize: '0.55rem', marginTop: '0.15rem', color: 'var(--text-muted)' }}>
                Background Entity Assessment &amp; Risk Research
              </div>
            </div>
          </Link>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            {entries.length > 0 && (
              <span
                className="font-data"
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.65rem',
                  letterSpacing: '0.12em',
                  color: 'var(--amber-primary)',
                  border: '1px solid var(--border-dim)',
                  padding: '0.2rem 0.5rem',
                }}
              >
                {entries.length} saved
              </span>
            )}
            <Link
              href="/"
              className="btn-secondary"
              style={{ fontSize: '0.65rem', textDecoration: 'none' }}
            >
              ← New Search
            </Link>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: '1400px', margin: '0 auto', padding: '2.5rem 1.5rem 4rem' }}>
        {/* Page title */}
        <div style={{ marginBottom: '2rem' }}>
          <div className="label-stamp" style={{ marginBottom: '0.5rem' }}>// Saved Intelligence Briefs</div>
          <h1
            className="font-editorial"
            style={{ fontSize: 'clamp(1.4rem, 3vw, 2rem)', fontWeight: 700, color: 'var(--text-bright)', lineHeight: 1.2, margin: 0 }}
          >
            Saved Searches
          </h1>
        </div>

        {/* Loading */}
        {isLoading && (
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-dim)',
              padding: '3rem',
              textAlign: 'center',
            }}
          >
            <div
              style={{
                display: 'inline-block',
                width: '8px',
                height: '8px',
                background: 'var(--amber-primary)',
                animation: 'data-pulse 1s ease-in-out infinite',
                boxShadow: '0 0 6px var(--amber-primary)',
                marginBottom: '0.75rem',
              }}
            />
            <p className="label-stamp" style={{ color: 'var(--text-muted)' }}>Loading saved searches…</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            style={{
              background: 'var(--risk-critical-bg)',
              border: '1px solid var(--risk-critical)',
              padding: '1.5rem',
              display: 'flex',
              gap: '0.75rem',
              alignItems: 'center',
            }}
          >
            <span style={{ color: 'var(--risk-critical-bright)' }}>⚠</span>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--risk-critical-bright)', margin: 0 }}>{error}</p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !error && entries.length === 0 && (
          <div
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-dim)',
              padding: '4rem 2rem',
              textAlign: 'center',
            }}
          >
            <svg
              width="40"
              height="40"
              viewBox="0 0 20 20"
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              style={{ color: 'var(--border-main)', margin: '0 auto 1rem' }}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
            </svg>
            <p className="font-editorial" style={{ fontSize: '1rem', color: 'var(--text-bright)', marginBottom: '0.5rem' }}>
              No saved searches
            </p>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1.5rem', lineHeight: 1.6 }}>
              Use the Save button on any results page to bookmark important findings.
            </p>
            <Link href="/" className="btn-primary" style={{ textDecoration: 'none', display: 'inline-block', fontSize: '0.7rem' }}>
              Start a Search
            </Link>
          </div>
        )}

        {/* Results grid */}
        {!isLoading && !error && entries.length > 0 && (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: '1px',
              background: 'var(--border-void)',
              border: '1px solid var(--border-void)',
            }}
          >
            {entries.map((entry) => (
              <div
                key={entry.search_id}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                }}
              >
                {/* Entity name + remove */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem' }}>
                  <h3
                    className="font-editorial"
                    style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-bright)', lineHeight: 1.3, margin: 0, flex: 1 }}
                  >
                    {entry.entity_name}
                  </h3>
                  <button
                    onClick={() =>
                      confirmingId === entry.search_id
                        ? handleUnsave(entry.search_id)
                        : setConfirmingId(entry.search_id)
                    }
                    onBlur={() => setTimeout(() => setConfirmingId((id) => id === entry.search_id ? null : id), 150)}
                    title={confirmingId === entry.search_id ? 'Click again to confirm removal' : 'Remove bookmark'}
                    style={{
                      flexShrink: 0,
                      background: 'none',
                      border: '1px solid',
                      borderColor: confirmingId === entry.search_id ? 'var(--risk-high)' : 'transparent',
                      color: confirmingId === entry.search_id ? 'var(--risk-high-bright)' : 'var(--text-faint)',
                      cursor: 'pointer',
                      padding: '0.2rem 0.4rem',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.62rem',
                      letterSpacing: '0.06em',
                      transition: 'all 0.15s',
                    }}
                  >
                    {confirmingId === entry.search_id ? 'Remove?' : '×'}
                  </button>
                </div>

                {/* Risk + tier badges */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <div
                    className={`risk-badge risk-badge-${entry.risk_level as RiskLevel}`}
                    style={{ fontSize: '0.62rem' }}
                  >
                    {entry.risk_level}
                  </div>
                  <span
                    className="label-stamp"
                    style={{ fontSize: '0.62rem', color: 'var(--text-muted)', border: '1px solid var(--border-dim)', padding: '0.1rem 0.375rem' }}
                  >
                    {TIER_LABELS[entry.tier as ResearchTier] ?? entry.tier}
                  </span>
                </div>

                {/* Label */}
                {entry.save_label && (
                  <p
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.72rem',
                      color: 'var(--amber-primary)',
                      margin: 0,
                      fontStyle: 'italic',
                    }}
                  >
                    &ldquo;{entry.save_label}&rdquo;
                  </p>
                )}

                {/* Timestamps */}
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.68rem', color: 'var(--text-faint)', lineHeight: 1.7 }}>
                  <div>Searched: {formatDate(entry.timestamp)}</div>
                  {entry.saved_at && <div>Saved: {formatDate(entry.saved_at)}</div>}
                </div>

                {/* View link */}
                <Link
                  href={`/results/${entry.search_id}`}
                  style={{
                    marginTop: 'auto',
                    display: 'block',
                    textAlign: 'center',
                    padding: '0.5rem',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.65rem',
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    color: 'var(--amber-primary)',
                    textDecoration: 'none',
                    border: '1px solid var(--border-main)',
                    background: 'var(--bg-panel)',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--amber-primary)'; e.currentTarget.style.color = 'var(--amber-light)'; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-main)'; e.currentTarget.style.color = 'var(--amber-primary)'; }}
                >
                  View Results →
                </Link>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
