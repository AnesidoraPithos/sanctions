'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import SearchForm from '@/components/SearchForm';
import ProgressTracker from '@/components/ProgressTracker';
import { SearchRequest, HistoryEntry, RiskLevel } from '@/lib/types';
import { api } from '@/lib/api-client';

export default function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSearchId, setActiveSearchId] = useState<string | null>(null);
  const [recentSearches, setRecentSearches] = useState<HistoryEntry[]>([]);
  const [savedCount, setSavedCount] = useState(0);

  useEffect(() => {
    api.getHistory(5).then((data) => setRecentSearches(data.entries)).catch(() => {});
    api.getSavedSearches(100).then((data) => setSavedCount(data.total)).catch(() => {});
  }, []);

  const handleSearch = async (request: SearchRequest) => {
    setIsLoading(true);
    setError(null);

    let enrichedRequest = request;
    if (request.tier === 'network' || request.tier === 'deep') {
      const clientId = crypto.randomUUID();
      enrichedRequest = { ...request, client_search_id: clientId };
      setActiveSearchId(clientId);
    }

    try {
      let response;
      switch (enrichedRequest.tier) {
        case 'network':
          response = await api.searchNetwork(enrichedRequest);
          break;
        case 'deep':
          response = await api.searchDeep(enrichedRequest);
          break;
        case 'base':
        default:
          response = await api.searchBase(enrichedRequest);
          break;
      }
      setActiveSearchId(null);
      router.push(`/results/${response.search_id}`);
    } catch (err: unknown) {
      console.error('Search error:', err);
      setActiveSearchId(null);
      const errorObj = err as { message?: string; data?: { message?: string }; code?: string };
      const errorMessage = errorObj.message || 'Failed to perform search. Please try again.';
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen bg-grid-subtle"
      style={{ background: 'var(--bg-void)' }}
    >
      {/* Ambient radial glow — centre of gravity */}
      <div
        style={{
          position: 'fixed',
          top: '30%',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '800px',
          height: '500px',
          background: 'radial-gradient(ellipse at center, rgba(168,112,8,0.04) 0%, transparent 70%)',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      {/* ── Header ──────────────────────────────────────────────────── */}
      <header
        style={{
          borderBottom: '1px solid var(--border-dim)',
          background: 'var(--bg-deep)',
          position: 'relative',
          zIndex: 10,
        }}
      >
        {/* Amber accent line at very top */}
        <div style={{ height: '2px', background: 'linear-gradient(90deg, transparent, var(--amber-primary), transparent)' }} />

        <div
          style={{
            maxWidth: '1400px',
            margin: '0 auto',
            padding: '1.25rem 1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* Wordmark */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ flexShrink: 0 }}>
              <Image src="/bear-logo.png" alt="BEAR²" width={44} height={44} style={{ display: 'block', opacity: 0.9 }} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
                <span
                  className="font-display animate-fadeInUp"
                  style={{ fontSize: '2.2rem', lineHeight: 1, color: 'var(--amber-light)', letterSpacing: '0.08em' }}
                >
                  BEAR
                </span>
                <span
                  className="font-display animate-fadeInUp delay-50"
                  style={{ fontSize: '1.2rem', lineHeight: 1, color: 'var(--amber-primary)', verticalAlign: 'super' }}
                >
                  2
                </span>
              </div>
              <div
                className="label-stamp animate-fadeInUp delay-100"
                style={{ fontSize: '0.55rem', marginTop: '0.15rem', color: 'var(--text-muted)' }}
              >
                Background Entity Assessment &amp; Risk Research
              </div>
            </div>
          </div>

          {/* Nav */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            {savedCount > 0 && (
              <Link
                href="/saved"
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.7rem',
                  letterSpacing: '0.12em',
                  textTransform: 'uppercase',
                  color: 'var(--text-muted)',
                  textDecoration: 'none',
                  transition: 'color 0.2s',
                }}
                onMouseEnter={e => (e.currentTarget.style.color = 'var(--amber-light)')}
                onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
              >
                Saved ({savedCount})
              </Link>
            )}
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.65rem',
                letterSpacing: '0.12em',
                color: 'var(--text-faint)',
                border: '1px solid var(--border-dim)',
                padding: '0.2rem 0.5rem',
              }}
            >
              v1.1.0
            </div>
          </div>
        </div>
      </header>

      {/* ── Main ────────────────────────────────────────────────────── */}
      <main
        style={{
          maxWidth: '1400px',
          margin: '0 auto',
          padding: '3rem 1.5rem 4rem',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* Hero text */}
        <div className="animate-fadeInUp" style={{ marginBottom: '2.5rem' }}>
          <div className="label-stamp" style={{ marginBottom: '0.75rem' }}>
            // Intelligence Terminal — Clearance Required
          </div>
          <h1
            className="font-editorial animate-fadeInUp delay-100"
            style={{
              fontSize: 'clamp(1.8rem, 4vw, 2.8rem)',
              fontWeight: 700,
              color: 'var(--text-bright)',
              lineHeight: 1.2,
              marginBottom: '0.75rem',
              letterSpacing: '-0.01em',
            }}
          >
            Entity Background Research
          </h1>
          <p
            className="animate-fadeInUp delay-150"
            style={{
              fontSize: '0.875rem',
              color: 'var(--text-secondary)',
              maxWidth: '560px',
              lineHeight: 1.6,
            }}
          >
            Sanctions screening across 10+ global databases. OSINT intelligence gathering.
            Corporate network mapping. AI-powered risk assessment.
          </p>
        </div>

        {/* ── Search Panel ────────────────────────────────────────── */}
        <div
          className="bracket-corners bracket-corners-active animate-fadeInUp delay-200"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-main)',
            marginBottom: '1.5rem',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Panel header */}
          <div
            style={{
              borderBottom: '1px solid var(--border-dim)',
              padding: '0.875rem 1.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'var(--bg-panel)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div
                style={{
                  width: '6px',
                  height: '6px',
                  background: 'var(--amber-main)',
                  boxShadow: '0 0 6px var(--amber-primary)',
                }}
              />
              <span
                className="label-stamp-bright"
                style={{ fontSize: '0.65rem' }}
              >
                Intelligence Query Initiation
              </span>
            </div>
            {isLoading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div
                  style={{
                    width: '6px',
                    height: '6px',
                    background: 'var(--cyan-bright)',
                    animation: 'data-pulse 1s ease-in-out infinite',
                    boxShadow: '0 0 6px var(--cyan-main)',
                  }}
                />
                <span
                  className="label-stamp"
                  style={{ color: 'var(--cyan-main)' }}
                >
                  Query Active
                </span>
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div
              style={{
                margin: '1.5rem',
                padding: '1rem 1.25rem',
                background: 'var(--risk-critical-bg)',
                border: '1px solid var(--risk-critical)',
                display: 'flex',
                gap: '0.75rem',
                alignItems: 'flex-start',
              }}
            >
              <span style={{ color: 'var(--risk-critical-bright)', flexShrink: 0 }}>⚠</span>
              <div>
                <div
                  className="label-stamp"
                  style={{ color: 'var(--risk-critical-bright)', marginBottom: '0.25rem' }}
                >
                  Search Error
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--risk-critical-bright)', margin: 0, opacity: 0.85 }}>
                  {error}
                </p>
              </div>
            </div>
          )}

          {/* Form */}
          <div style={{ padding: '1.5rem' }}>
            <SearchForm onSearch={handleSearch} isLoading={isLoading} />
          </div>

          {/* Progress tracker */}
          <ProgressTracker searchId={activeSearchId} />
        </div>

        {/* ── Recent Briefs ────────────────────────────────────────── */}
        {recentSearches.length > 0 && (
          <div
            className="animate-fadeInUp delay-300"
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-dim)',
              marginBottom: '1.5rem',
            }}
          >
            <div
              style={{
                borderBottom: '1px solid var(--border-dim)',
                padding: '0.75rem 1.25rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'var(--bg-panel)',
              }}
            >
              <span className="label-stamp-bright" style={{ fontSize: '0.6rem' }}>
                Recent Intelligence Briefs
              </span>
              {savedCount > 0 && (
                <Link
                  href="/saved"
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.65rem',
                    letterSpacing: '0.1em',
                    color: 'var(--amber-primary)',
                    textDecoration: 'none',
                    textTransform: 'uppercase',
                    transition: 'color 0.2s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.color = 'var(--amber-light)')}
                  onMouseLeave={e => (e.currentTarget.style.color = 'var(--amber-primary)')}
                >
                  View {savedCount} saved →
                </Link>
              )}
            </div>

            <div>
              {recentSearches.map((entry, i) => (
                <div
                  key={entry.search_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    padding: '0.625rem 1.25rem',
                    borderBottom: i < recentSearches.length - 1 ? '1px solid var(--border-void)' : 'none',
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-panel)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  {/* Risk indicator */}
                  <div
                    className={`risk-badge risk-badge-${entry.risk_level as RiskLevel}`}
                    style={{ flexShrink: 0, fontSize: '0.58rem' }}
                  >
                    {entry.risk_level}
                  </div>

                  {/* Entity name */}
                  <span
                    style={{
                      flex: 1,
                      fontSize: '0.8rem',
                      color: 'var(--text-bright)',
                      fontFamily: 'var(--font-mono)',
                      letterSpacing: '0.02em',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {entry.entity_name}
                  </span>

                  {/* Tier */}
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.62rem',
                      letterSpacing: '0.12em',
                      textTransform: 'uppercase',
                      color: 'var(--text-muted)',
                      flexShrink: 0,
                    }}
                  >
                    {entry.tier}
                  </span>

                  {/* Date */}
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.62rem',
                      color: 'var(--text-faint)',
                      flexShrink: 0,
                      minWidth: '52px',
                      textAlign: 'right',
                    }}
                  >
                    {new Date(entry.timestamp).toLocaleDateString('en-GB', {
                      day: 'numeric',
                      month: 'short',
                    })}
                  </span>

                  {/* Link */}
                  <Link
                    href={`/results/${entry.search_id}`}
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.62rem',
                      letterSpacing: '0.1em',
                      color: 'var(--amber-primary)',
                      textDecoration: 'none',
                      textTransform: 'uppercase',
                      flexShrink: 0,
                      transition: 'color 0.2s',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.color = 'var(--amber-light)')}
                    onMouseLeave={e => (e.currentTarget.style.color = 'var(--amber-primary)')}
                  >
                    Open →
                  </Link>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Capabilities ─────────────────────────────────────────── */}
        <div className="animate-fadeInUp delay-400">
          <div className="label-stamp" style={{ marginBottom: '1rem' }}>
            — System Capabilities
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
              gap: '1px',
              background: 'var(--border-void)',
              border: '1px solid var(--border-void)',
            }}
          >
            {[
              {
                label: 'Sanctions Screening',
                code: '01',
                desc: 'Cross-reference against OFAC, BIS Entity List, State Dept, and 7+ additional global sanctions databases with fuzzy name matching.',
              },
              {
                label: 'OSINT Intelligence',
                code: '02',
                desc: 'Gather open-source intelligence distinguishing official government sources from general media. Weighted scoring by source authority.',
              },
              {
                label: 'AI Risk Assessment',
                code: '03',
                desc: 'LLM-powered intelligence reports with 100-point risk methodology covering regulatory, severity, media signal, and temporal factors.',
              },
            ].map((cap) => (
              <div
                key={cap.code}
                style={{
                  background: 'var(--bg-surface)',
                  padding: '1.25rem',
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '0.75rem',
                  }}
                >
                  <span
                    style={{
                      fontSize: '0.8rem',
                      fontWeight: 600,
                      color: 'var(--text-bright)',
                      fontFamily: 'var(--font-dm-sans)',
                    }}
                  >
                    {cap.label}
                  </span>
                  <span
                    className="font-data"
                    style={{ fontSize: '0.65rem', color: 'var(--amber-deep)', letterSpacing: '0.1em' }}
                  >
                    [{cap.code}]
                  </span>
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.6, margin: 0 }}>
                  {cap.desc}
                </p>
                <div
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: '1px',
                    background: 'linear-gradient(90deg, var(--amber-deep), transparent)',
                    opacity: 0.4,
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
