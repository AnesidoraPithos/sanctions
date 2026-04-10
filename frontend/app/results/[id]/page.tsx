/**
 * Results Page - Display Entity Background Research Results
 *
 * Shows sanctions hits, media intelligence, risk level, and AI-generated report.
 */

'use client';

import React, { use, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ResultsResponse, SanctionsHit, MediaHit, NetworkData, FinancialIntelligence, FinancialFlow, DirectorPivot, InfrastructureHit, BeneficialOwner } from '@/lib/types';
import ManagementNetworkTab from '@/components/ManagementNetworkTab';
import InfrastructureTab from '@/components/InfrastructureTab';
import BeneficialOwnershipTab from '@/components/BeneficialOwnershipTab';
import { api } from '@/lib/api-client';
import RiskBadge from '@/components/RiskBadge';
import TierBadge from '@/components/TierBadge';
import LoadingSpinner from '@/components/LoadingSpinner';
import NetworkGraph from '@/components/NetworkGraph';
import ExportControls from '@/components/ExportControls';
import SaveButton from '@/components/SaveButton';
import { format } from 'date-fns';

interface PageProps {
  params: Promise<{ id: string }>;
}

function renderMarkdown(text: string): string {
  const lines = text.split('\n');
  let html = '';
  let inOl = false;
  let inUl = false;

  const closeList = () => {
    if (inOl) { html += '</ol>'; inOl = false; }
    if (inUl) { html += '</ul>'; inUl = false; }
  };

  const processInline = (s: string): string => {
    // [Source: https://...] → compact citation link
    s = s.replace(/\[Source:\s*(https?:\/\/[^\]]+)\]/g, '<a href="$1" target="_blank">[Source]</a>');
    // [text](url) → hyperlink
    s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    // **text** → bold
    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    // bare URLs (not already inside href="...")
    s = s.replace(/(?<!['"=])(https?:\/\/[^\s<"]+)/g, '<a href="$1" target="_blank">$1</a>');
    return s;
  };

  for (const line of lines) {
    if (line.startsWith('### ')) {
      closeList();
      html += `<h3>${processInline(line.slice(4))}</h3>\n`;
    } else if (line.startsWith('## ')) {
      closeList();
      html += `<h2>${processInline(line.slice(3))}</h2>\n`;
    } else if (line.startsWith('# ')) {
      closeList();
      html += `<h1>${processInline(line.slice(2))}</h1>\n`;
    } else if (/^\d+\.\s/.test(line)) {
      if (inUl) { html += '</ul>'; inUl = false; }
      if (!inOl) { html += '<ol>'; inOl = true; }
      html += `<li>${processInline(line.replace(/^\d+\.\s/, ''))}</li>\n`;
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      if (inOl) { html += '</ol>'; inOl = false; }
      if (!inUl) { html += '<ul>'; inUl = true; }
      html += `<li>${processInline(line.slice(2))}</li>\n`;
    } else if (line.trim() === '') {
      closeList();
      html += '<br/>\n';
    } else if (line.startsWith('Risk Level:')) {
      closeList();
      const parts = line.split('|');
      const riskHeader = parts[0].trim();
      const scoreComponents = parts.slice(1);
      html += `<div style="background:var(--bg-raised);border-left:3px solid var(--amber-primary);padding:12px 16px;margin:12px 0">`;
      html += `<div style="color:var(--amber-light);font-weight:bold;margin-bottom:8px;font-family:var(--font-mono);font-size:0.78rem;letter-spacing:0.06em">${processInline(riskHeader)}</div>`;
      for (const comp of scoreComponents) {
        if (comp.trim()) {
          html += `<div style="color:var(--text-secondary);margin:2px 0;font-family:var(--font-mono);font-size:0.75rem">&bull; ${processInline(comp.trim())}</div>`;
        }
      }
      html += `</div>\n`;
    } else {
      closeList();
      html += `<p>${processInline(line)}</p>\n`;
    }
  }

  closeList();
  return html;
}

export default function ResultsPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const searchId = resolvedParams.id;

  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  type TabType = 'sanctions' | 'media' | 'report' | 'financial' | 'network-relations' | 'financial-flows' | 'management-network' | 'infrastructure' | 'beneficial-ownership';
  const [activeTab, setActiveTab] = useState<TabType | null>(null);
  const tabsRef = useRef<HTMLDivElement>(null);
  const [tabsCanScrollRight, setTabsCanScrollRight] = useState(false);

  useEffect(() => {
    const el = tabsRef.current;
    if (!el) return;
    const check = () => setTabsCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 1);
    check();
    el.addEventListener('scroll', check);
    window.addEventListener('resize', check);
    return () => {
      el.removeEventListener('scroll', check);
      window.removeEventListener('resize', check);
    };
  }, [results]);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const data = await api.getResults(searchId);
        setResults(data);
        setActiveTab(data.tier === 'network' || data.tier === 'deep' ? 'network-relations' : 'sanctions');
        setIsLoading(false);
      } catch (err: unknown) {
        console.error('Error fetching results:', err);
        const errorMessage =
          (err as { data?: { message?: string } })?.data?.message ||
          'Failed to load results';
        setError(errorMessage);
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [searchId]);

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg-void)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LoadingSpinner size="lg" message="Loading results..." />
      </div>
    );
  }

  if (error || !results) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg-void)', color: 'var(--text-main)' }}>
        <div style={{ maxWidth: '720px', margin: '0 auto', padding: '4rem 1.5rem' }}>
          <div
            style={{
              background: 'var(--risk-critical-bg)',
              border: '1px solid var(--risk-critical)',
              padding: '2rem',
              textAlign: 'center',
            }}
          >
            <div className="label-stamp" style={{ color: 'var(--risk-critical-bright)', marginBottom: '1rem', fontSize: '0.8rem' }}>
              Error Loading Results
            </div>
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--risk-critical-bright)', opacity: 0.8, marginBottom: '1.5rem' }}>
              {error}
            </p>
            <Link href="/" className="btn-secondary" style={{ display: 'inline-block', textDecoration: 'none' }}>
              ← Return to Search
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Extract media data
  const mediaData: MediaHit[] = results.research_data.media_data || [];
  const officialSources = results.research_data.media_intelligence?.official_sources || [];
  const generalMedia = results.research_data.media_intelligence?.general_media || [];
  const allMedia = [...officialSources, ...generalMedia, ...mediaData].filter(
    (hit: MediaHit) => !hit.relevance || !/not explicitly mention/i.test(hit.relevance)
  );

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-void)', color: 'var(--text-main)' }}>
      {/* Header */}
      <header style={{ borderBottom: '1px solid var(--border-dim)', background: 'var(--bg-deep)', position: 'relative', zIndex: 10 }}>
        <div style={{ height: '2px', background: 'linear-gradient(90deg, transparent, var(--amber-primary), transparent)' }} />
        <div style={{ maxWidth: '1600px', margin: '0 auto', padding: '1rem 1.5rem', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
          <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.875rem', textDecoration: 'none' }}>
            <Image src="/bear-logo.png" alt="BEAR²" width={36} height={36} style={{ display: 'block', opacity: 0.9 }} />
            <div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                <span className="font-display" style={{ fontSize: '1.7rem', lineHeight: 1, color: 'var(--amber-light)', letterSpacing: '0.08em' }}>BEAR</span>
                <span className="font-display" style={{ fontSize: '0.9rem', color: 'var(--amber-primary)', verticalAlign: 'super' }}>2</span>
              </div>
              <div className="label-stamp" style={{ fontSize: '0.5rem', marginTop: '0.1rem', color: 'var(--text-faint)' }}>
                Intelligence Dossier
              </div>
            </div>
          </Link>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.625rem' }}>
            <SaveButton
              searchId={searchId}
              initialSaved={results.is_saved ?? false}
              initialLabel={results.save_label}
            />
            <ExportControls searchId={searchId} />
            <Link
              href="/"
              className="btn-secondary"
              style={{ fontSize: '0.65rem', textDecoration: 'none', whiteSpace: 'nowrap' }}
            >
              ← New Search
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: '1600px', margin: '0 auto', padding: '2rem 1.5rem 4rem' }}>
        {/* Summary Card */}
        <div
          className="bracket-corners bracket-corners-active animate-fadeInUp"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-main)',
            marginBottom: '1.5rem',
          }}
        >
          {/* Panel label */}
          <div style={{ borderBottom: '1px solid var(--border-dim)', padding: '0.75rem 1.25rem', background: 'var(--bg-panel)', display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <div style={{ width: '6px', height: '6px', background: 'var(--amber-main)', boxShadow: '0 0 6px var(--amber-primary)' }} />
            <span className="label-stamp-bright" style={{ fontSize: '0.6rem' }}>Entity Intelligence Dossier</span>
          </div>

          {/* Top metadata */}
          <div style={{ padding: '1.25rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1.25rem' }}>
            <div>
              <div className="label-stamp" style={{ marginBottom: '0.375rem' }}>Target Entity</div>
              <p className="font-editorial" style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-bright)', margin: 0, lineHeight: 1.3 }}>
                {results.entity_name}
              </p>
            </div>
            <div>
              <div className="label-stamp" style={{ marginBottom: '0.375rem' }}>Risk Classification</div>
              <RiskBadge level={results.risk_level} size="lg" explanation={results.risk_explanation} />
            </div>
            <div>
              <div className="label-stamp" style={{ marginBottom: '0.375rem' }}>Research Tier</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                <TierBadge tier={results.tier} />
                {(results.tier === 'network' || results.tier === 'deep') && results.metadata?.network_depth != null && (
                  <span className="font-data" style={{ fontSize: '0.72rem', color: 'var(--cyan-main)' }}>
                    depth-{String(results.metadata.network_depth)}
                  </span>
                )}
              </div>
            </div>
            <div>
              <div className="label-stamp" style={{ marginBottom: '0.375rem' }}>Timestamp</div>
              <span className="font-data" style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                {format(new Date(results.timestamp), 'PPpp')}
              </span>
            </div>
          </div>

          {/* Stats row */}
          <div style={{ borderTop: '1px solid var(--border-dim)', padding: '1rem 1.25rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem' }}>
            {[
              { value: results.sanctions_hits, label: 'Sanctions Hits', color: results.sanctions_hits > 0 ? 'var(--risk-critical-bright)' : 'var(--risk-safe-bright)' },
              { value: allMedia.length, label: 'Media Hits', color: 'var(--amber-light)' },
              ...(results.tier === 'network' || results.tier === 'deep' ? [
                { value: results.subsidiaries?.length || 0, label: 'Subsidiaries', color: 'var(--cyan-bright)' },
                results.tier === 'deep'
                  ? { value: results.financial_flows?.length || 0, label: 'Financial Flows', color: 'var(--risk-mid-bright)' }
                  : { value: ((results.financial_intelligence as FinancialIntelligence)?.directors?.length || 0) + ((results.financial_intelligence as FinancialIntelligence)?.shareholders?.length || 0), label: 'People', color: 'var(--risk-mid-bright)' },
              ] : [
                { value: officialSources.length, label: 'Official Sources', color: 'var(--risk-safe-bright)' },
                { value: generalMedia.length, label: 'General Media', color: 'var(--text-secondary)' },
              ]),
            ].map((stat) => (
              <div key={stat.label}>
                <div className="font-display" style={{ fontSize: '2rem', lineHeight: 1, color: stat.color, letterSpacing: '0.04em' }}>
                  {stat.value}
                </div>
                <div className="label-stamp" style={{ marginTop: '0.25rem', color: 'var(--text-muted)' }}>{stat.label}</div>
              </div>
            ))}
          </div>

          {/* Phase 4 stats row — deep tier only */}
          {results.tier === 'deep' && (results.director_pivots?.length || results.infrastructure?.length || results.beneficial_owners?.length) ? (
            <div style={{ borderTop: '1px solid var(--border-void)', padding: '0.875rem 1.25rem', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', background: 'var(--bg-panel)' }}>
              {[
                { value: (results.director_pivots || []).reduce((s, p) => s + ((p as DirectorPivot).companies?.length || 0), 0), label: 'Interlocked Companies', color: 'var(--cyan-main)' },
                { value: results.infrastructure?.length || 0, label: 'Domains Analysed', color: 'var(--cyan-main)' },
                { value: results.beneficial_owners?.length || 0, label: 'UBOs Found', color: 'var(--risk-safe-bright)' },
              ].map((stat) => (
                <div key={stat.label}>
                  <div className="font-display" style={{ fontSize: '1.6rem', lineHeight: 1, color: stat.color, letterSpacing: '0.04em' }}>{stat.value}</div>
                  <div className="label-stamp" style={{ marginTop: '0.2rem', color: 'var(--text-muted)' }}>{stat.label}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        {/* Network / Deep Tier Confirmation Banner */}
        {(results.tier === 'network' || results.tier === 'deep') && (
          <div style={{ marginBottom: '1.25rem', background: 'var(--bg-panel)', border: '1px solid var(--border-main)', borderLeft: '2px solid var(--cyan-main)', padding: '1rem 1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <span style={{ color: 'var(--cyan-bright)', flexShrink: 0 }}>◈</span>
              <div style={{ flex: 1 }}>
                <div className="label-stamp-bright" style={{ marginBottom: '0.375rem' }}>
                  {results.tier === 'deep' ? 'Deep Tier Research Completed' : 'Network Tier Research Completed'}
                </div>
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--cyan-bright)', margin: 0, lineHeight: 1.6 }}>
                  {results.metadata?.network_depth && (results.metadata.network_depth as number) > 1
                    ? `Multi-level corporate structure analysis performed (${results.metadata.network_depth} levels deep).`
                    : 'Corporate structure analysis performed.'
                  }
                  {' '}
                  {results.subsidiaries && results.subsidiaries.length > 0 ? (
                    <>
                      Discovered {results.subsidiaries.length} {results.subsidiaries.length === 1 ? 'entity' : 'entities'}
                      {results.network_data && (results.network_data as NetworkData).statistics && (() => {
                        const stats = (results.network_data as NetworkData).statistics;
                        const depth = results.metadata?.network_depth as number || 1;
                        const parts = [];

                        if (stats.level_1_count !== undefined && stats.level_1_count > 0) {
                          parts.push(`${stats.level_1_count} level 1`);
                        }
                        if (depth >= 2 && stats.level_2_count !== undefined) {
                          if (stats.level_2_count > 0) {
                            parts.push(`${stats.level_2_count} level 2`);
                          } else {
                            parts.push(`0 level 2`);
                          }
                        }
                        if (depth >= 3 && stats.level_3_count !== undefined) {
                          if (stats.level_3_count > 0) {
                            parts.push(`${stats.level_3_count} level 3`);
                          } else {
                            parts.push(`0 level 3`);
                          }
                        }

                        return parts.length > 0 ? ` (${parts.join(', ')})` : '';
                      })()}.
                    </>
                  ) : (
                    <>
                      No subsidiaries discovered for this entity.
                      {results.metadata?.network_depth && (results.metadata.network_depth as number) > 1 && (
                        <> Searched {results.metadata.network_depth} level(s) deep.</>
                      )}
                    </>
                  )}
                  {' '}
                  {(results.financial_intelligence as FinancialIntelligence)?.directors && (results.financial_intelligence as FinancialIntelligence).directors.length > 0
                    ? `Found ${(results.financial_intelligence as FinancialIntelligence).directors.length} director(s) and ${(results.financial_intelligence as FinancialIntelligence)?.shareholders?.length || 0} shareholder(s).`
                    : ''
                  }
                </p>
                {Array.isArray(results.metadata?.data_sources_used) && (
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.375rem' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Sources: </span>
                    {(results.metadata.data_sources_used as string[]).map((source: string) => {
                      const displayName = source === 'opencorporates_api' ? 'OpenCorporates API' :
                                          source === 'sec_edgar' ? 'SEC EDGAR' :
                                          source === 'wikipedia' ? 'Wikipedia' :
                                          source === 'duckduckgo' ? 'DuckDuckGo' : source;
                      return displayName;
                    }).join(', ')}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Warnings Banner */}
        {results.warnings && results.warnings.length > 0 && (
          <div style={{ marginBottom: '1.25rem', background: 'var(--risk-mid-bg)', border: '1px solid var(--risk-mid)', borderLeft: '2px solid var(--risk-mid-bright)', padding: '1rem 1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <span style={{ color: 'var(--risk-mid-bright)', flexShrink: 0 }}>⚠</span>
              <div>
                <div className="label-stamp" style={{ color: 'var(--risk-mid-bright)', marginBottom: '0.5rem' }}>
                  Data Source Limitations
                </div>
                <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {results.warnings.map((warning, idx) => (
                    <li key={idx} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--risk-mid-bright)', opacity: 0.85 }}>
                      · {warning.message}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div style={{ position: 'relative', marginBottom: '1.5rem' }}>
          <div
            ref={tabsRef}
            style={{ borderBottom: '1px solid var(--border-dim)', overflowX: 'auto', scrollbarWidth: 'none' }}
          >
          <nav style={{ display: 'flex', gap: 0, minWidth: 'max-content' }}>
            {([
              { key: 'sanctions', label: `Sanctions (${results.sanctions_hits})`, always: true },
              { key: 'media', label: `Media (${allMedia.length})`, always: true },
              { key: 'report', label: 'Intel Report', always: true },
              ...(results.tier === 'network' || results.tier === 'deep') && results.network_data ? [
                { key: 'network-relations', label: `Network (${(results.network_data?.parent_info ? 1 : 0) + (results.subsidiaries?.length || 0) + ((results.network_data as any)?.sisters?.length || 0)})`, always: false },
                { key: 'financial', label: 'Financial Intel', always: false },
                ...(results.tier === 'deep' ? [
                  { key: 'financial-flows', label: `Flows (${results.financial_flows?.length || 0})`, always: false },
                  ...(results.director_pivots ? [{ key: 'management-network', label: `Directors (${results.director_pivots.length})`, always: false }] : []),
                  ...(results.infrastructure ? [{ key: 'infrastructure', label: `Infra (${results.infrastructure.length})`, always: false }] : []),
                  ...(results.beneficial_owners ? [{ key: 'beneficial-ownership', label: `UBOs (${results.beneficial_owners.length})`, always: false }] : []),
                ] : []),
              ] : [],
            ] as { key: TabType; label: string; always: boolean }[]).map((tab) => {
              const isActive = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.7rem',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    padding: '0.75rem 1rem',
                    background: 'transparent',
                    border: 'none',
                    borderBottom: isActive ? '2px solid var(--amber-main)' : '2px solid transparent',
                    color: isActive ? 'var(--amber-light)' : 'var(--text-muted)',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    transition: 'color 0.15s, border-color 0.15s',
                    marginBottom: '-1px',
                  }}
                  onMouseEnter={e => { if (!isActive) e.currentTarget.style.color = 'var(--text-main)'; }}
                  onMouseLeave={e => { if (!isActive) e.currentTarget.style.color = 'var(--text-muted)'; }}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>
          </div>
          {/* Right-fade scroll indicator */}
          {tabsCanScrollRight && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                right: 0,
                bottom: '1px',
                width: '48px',
                background: 'linear-gradient(to right, transparent, var(--bg-void))',
                pointerEvents: 'none',
              }}
            />
          )}
        </div>

        {/* Tab Content */}
        <div>
          {/* Sanctions Tab */}
          {activeTab === 'sanctions' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {results.sanctions_data.length === 0 ? (
                <div style={{ background: 'var(--risk-safe-bg)', border: '1px solid var(--risk-safe)', padding: '2.5rem', textAlign: 'center' }}>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--risk-safe-bright)', letterSpacing: '0.08em' }}>
                    ✓ No sanctions matches found
                  </p>
                </div>
              ) : (
                results.sanctions_data.map((hit: SanctionsHit, idx: number) => (
                  <div key={idx} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-main)', padding: '1.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.875rem' }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '0.625rem' }}>
                          <span className="font-editorial" style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-bright)' }}>{hit.name}</span>
                          <span style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '0.62rem',
                            letterSpacing: '0.12em',
                            padding: '0.15rem 0.5rem',
                            background: hit.match_quality === 'EXACT' ? 'var(--risk-critical-bg)' : hit.match_quality === 'HIGH' ? 'var(--risk-high-bg)' : 'var(--risk-mid-bg)',
                            color: hit.match_quality === 'EXACT' ? 'var(--risk-critical-bright)' : hit.match_quality === 'HIGH' ? 'var(--risk-high-bright)' : 'var(--risk-mid-bright)',
                            border: `1px solid ${hit.match_quality === 'EXACT' ? 'var(--risk-critical)' : hit.match_quality === 'HIGH' ? 'var(--risk-high)' : 'var(--risk-mid)'}`,
                          }}>
                            {hit.match_quality} — {hit.combined_score.toFixed(0)}%
                          </span>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem', marginBottom: '0.625rem' }}>
                          <div><span className="label-stamp">List: </span><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-main)' }}>{hit.list}</span></div>
                          <div><span className="label-stamp">Type: </span><span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-main)' }}>{hit.type}</span></div>
                        </div>
                        {hit.address && <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-secondary)', margin: '0 0 0.375rem' }}><span style={{ color: 'var(--text-muted)' }}>Address: </span>{hit.address}</p>}
                        {hit.remark && <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-secondary)', margin: 0 }}>{hit.remark}</p>}
                      </div>
                    </div>
                    {hit.link && (
                      <a href={hit.link} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', letterSpacing: '0.08em', color: 'var(--amber-primary)', textDecoration: 'none', display: 'inline-block' }}>
                        View Source →
                      </a>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Media Tab */}
          {activeTab === 'media' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {allMedia.length === 0 ? (
                <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-dim)', padding: '2.5rem', textAlign: 'center' }}>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>No media intelligence found</p>
                </div>
              ) : (
                allMedia.map((hit: MediaHit, idx: number) => (
                  <div key={idx} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', padding: '1rem 1.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '0.5rem' }}>
                      <span style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '0.58rem',
                        letterSpacing: '0.15em',
                        padding: '0.15rem 0.5rem',
                        flexShrink: 0,
                        background: hit.source_type === 'official' ? 'var(--risk-safe-bg)' : 'var(--bg-panel)',
                        color: hit.source_type === 'official' ? 'var(--risk-safe-bright)' : 'var(--text-secondary)',
                        border: `1px solid ${hit.source_type === 'official' ? 'var(--risk-safe)' : 'var(--border-dim)'}`,
                      }}>
                        {hit.source_type === 'official' ? 'OFFICIAL' : 'MEDIA'}
                      </span>
                      <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-bright)', margin: 0, lineHeight: 1.4 }}>{hit.title}</h3>
                    </div>
                    {hit.snippet && <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', lineHeight: 1.6 }}>{hit.snippet}</p>}
                    {hit.relevance && <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--risk-safe-bright)', marginBottom: '0.5rem' }}>✓ {hit.relevance}</p>}
                    <a href={hit.url} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', letterSpacing: '0.08em', color: 'var(--amber-primary)', textDecoration: 'none' }}>
                      Read More →
                    </a>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Intelligence Report Tab */}
          {activeTab === 'report' && (
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', padding: '1.5rem' }}>
              {results.intelligence_report ? (
                <div
                  className="prose-intel"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(results.intelligence_report) }}
                />
              ) : (
                <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)', textAlign: 'center', padding: '2.5rem 0' }}>
                  No intelligence report available
                </p>
              )}
            </div>
          )}

          {/* Financial Intelligence Tab */}
          {activeTab === 'financial' && results.financial_intelligence && (() => {
            const financialIntel = results.financial_intelligence as FinancialIntelligence;
            const tableHeadStyle: React.CSSProperties = {
              fontFamily: 'var(--font-mono)',
              fontSize: '0.62rem',
              letterSpacing: '0.12em',
              textTransform: 'uppercase' as const,
              color: 'var(--text-muted)',
              padding: '0.625rem 1rem',
              textAlign: 'left' as const,
              background: 'var(--bg-panel)',
              borderBottom: '1px solid var(--border-dim)',
              whiteSpace: 'nowrap' as const,
            };
            const tableCellStyle: React.CSSProperties = {
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--text-main)',
              padding: '0.625rem 1rem',
              borderBottom: '1px solid var(--border-void)',
            };
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {/* Directors & Officers */}
                {financialIntel.directors && financialIntel.directors.length > 0 && (
                  <div>
                    <div className="label-stamp-bright" style={{ marginBottom: '0.75rem' }}>
                      Directors &amp; Officers ({financialIntel.directors.length})
                    </div>
                    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                          <tr>
                            {['Name', 'Title', 'Nationality', 'Sanctions'].map(h => (
                              <th key={h} style={tableHeadStyle}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {financialIntel.directors.map((director, idx) => (
                            <tr key={idx} style={{ background: idx % 2 === 1 ? 'var(--bg-panel)' : 'transparent' }}>
                              <td style={{ ...tableCellStyle, color: 'var(--text-bright)', fontWeight: 500 }}>{director.name}</td>
                              <td style={tableCellStyle}>{director.title || '—'}</td>
                              <td style={tableCellStyle}>{director.nationality || '—'}</td>
                              <td style={tableCellStyle}>
                                {director.sanctions_hits && director.sanctions_hits > 0 ? (
                                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', padding: '0.15rem 0.5rem', background: 'var(--risk-critical-bg)', color: 'var(--risk-critical-bright)', border: '1px solid var(--risk-critical)' }}>
                                    {director.sanctions_hits} hit(s)
                                  </span>
                                ) : (
                                  <span style={{ color: 'var(--text-faint)', fontSize: '0.72rem' }}>None</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Shareholders */}
                {financialIntel.shareholders && financialIntel.shareholders.length > 0 && (
                  <div>
                    <div className="label-stamp-bright" style={{ marginBottom: '0.75rem' }}>
                      Major Shareholders ({financialIntel.shareholders.length})
                    </div>
                    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', overflowX: 'auto' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                        <thead>
                          <tr>
                            {['Name', 'Type', 'Ownership %', 'Jurisdiction', 'Sanctions'].map(h => (
                              <th key={h} style={tableHeadStyle}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {financialIntel.shareholders.map((shareholder, idx) => (
                            <tr key={idx} style={{ background: idx % 2 === 1 ? 'var(--bg-panel)' : 'transparent' }}>
                              <td style={{ ...tableCellStyle, color: 'var(--text-bright)', fontWeight: 500 }}>{shareholder.name}</td>
                              <td style={tableCellStyle}>{shareholder.type || '—'}</td>
                              <td style={{ ...tableCellStyle, color: 'var(--amber-light)' }}>{shareholder.ownership_percentage || 0}%</td>
                              <td style={tableCellStyle}>{shareholder.jurisdiction || '—'}</td>
                              <td style={tableCellStyle}>
                                {shareholder.sanctions_hits && shareholder.sanctions_hits > 0 ? (
                                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', padding: '0.15rem 0.5rem', background: 'var(--risk-critical-bg)', color: 'var(--risk-critical-bright)', border: '1px solid var(--risk-critical)' }}>
                                    {shareholder.sanctions_hits} hit(s)
                                  </span>
                                ) : (
                                  <span style={{ color: 'var(--text-faint)', fontSize: '0.72rem' }}>None</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Transactions */}
                {financialIntel.transactions && financialIntel.transactions.length > 0 && (
                  <div>
                    <div className="label-stamp-bright" style={{ marginBottom: '0.75rem' }}>
                      Related Party Transactions ({financialIntel.transactions.length})
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {financialIntel.transactions.map((transaction, idx) => (
                        <div key={idx} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', padding: '1rem 1.25rem' }}>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.75rem' }}>
                            {[
                              { label: 'Type', value: transaction.transaction_type || '—' },
                              { label: 'Counterparty', value: transaction.counterparty || '—' },
                              { label: 'Amount', value: transaction.amount != null ? `${transaction.currency || ''} ${Number(transaction.amount).toLocaleString()}` : '—' },
                              { label: 'Date', value: transaction.transaction_date || '—' },
                            ].map(({ label, value }) => (
                              <div key={label}>
                                <div className="label-stamp" style={{ marginBottom: '0.2rem' }}>{label}</div>
                                <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-main)', margin: 0 }}>{value}</p>
                              </div>
                            ))}
                          </div>
                          {transaction.purpose && (
                            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '0.75rem', marginBottom: 0, borderTop: '1px solid var(--border-void)', paddingTop: '0.625rem' }}>
                              <span style={{ color: 'var(--text-muted)' }}>Purpose: </span>{transaction.purpose}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Empty */}
                {(!financialIntel.directors || financialIntel.directors.length === 0) &&
                 (!financialIntel.shareholders || financialIntel.shareholders.length === 0) &&
                 (!financialIntel.transactions || financialIntel.transactions.length === 0) && (
                  <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-dim)', padding: '2.5rem', textAlign: 'center' }}>
                    <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-muted)', margin: 0 }}>
                      No financial intelligence data found. This is normal for private or non-US entities.
                    </p>
                  </div>
                )}
              </div>
            );
          })()}

          {/* Financial Flows Tab (deep tier only) */}
          {activeTab === 'financial-flows' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {results.financial_flows && results.financial_flows.length > 0 ? (
                <>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', margin: 0 }}>
                    {results.financial_flows.length} flow{results.financial_flows.length !== 1 ? 's' : ''} identified from federal procurement records and related-party transactions.
                  </p>
                  <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr>
                          {['Source', 'Target', 'Type', 'Amount', 'Date'].map((h, i) => (
                            <th key={h} style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '0.62rem',
                              letterSpacing: '0.12em',
                              textTransform: 'uppercase',
                              color: 'var(--text-muted)',
                              padding: '0.625rem 1rem',
                              textAlign: i === 3 ? 'right' : 'left',
                              background: 'var(--bg-panel)',
                              borderBottom: '1px solid var(--border-dim)',
                              whiteSpace: 'nowrap',
                            }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(results.financial_flows as FinancialFlow[]).map((flow, idx) => (
                          <tr key={idx} style={{ background: idx % 2 === 1 ? 'var(--bg-panel)' : 'transparent' }}>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-bright)', padding: '0.625rem 1rem', borderBottom: '1px solid var(--border-void)', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={flow.source}>{flow.source}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-secondary)', padding: '0.625rem 1rem', borderBottom: '1px solid var(--border-void)', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={flow.target}>{flow.target}</td>
                            <td style={{ padding: '0.625rem 1rem', borderBottom: '1px solid var(--border-void)' }}>
                              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', letterSpacing: '0.08em', padding: '0.15rem 0.5rem', background: 'var(--bg-raised)', color: 'var(--cyan-bright)', border: '1px solid var(--cyan-dim)', textTransform: 'capitalize' }}>
                                {flow.type.replace(/_/g, ' ')}
                              </span>
                            </td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--amber-light)', padding: '0.625rem 1rem', borderBottom: '1px solid var(--border-void)', textAlign: 'right', whiteSpace: 'nowrap' }}>
                              {flow.amount != null ? `${flow.currency || 'USD'} ${Number(flow.amount).toLocaleString()}` : '—'}
                            </td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', padding: '0.625rem 1rem', borderBottom: '1px solid var(--border-void)', whiteSpace: 'nowrap' }}>{flow.date || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-dim)', padding: '2.5rem', textAlign: 'center' }}>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--text-muted)', margin: '0 0 0.375rem' }}>
                    No financial flows found. This may be normal for private or non-US entities.
                  </p>
                  <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-faint)', margin: 0 }}>
                    Sources: USAspending.gov and SEC EDGAR related-party transactions.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Management Network Tab (Phase 4) */}
          {activeTab === 'management-network' && (
            <ManagementNetworkTab
              directorPivots={(results.director_pivots || []) as DirectorPivot[]}
            />
          )}

          {/* Infrastructure Tab (Phase 4) */}
          {activeTab === 'infrastructure' && (
            <InfrastructureTab
              infrastructure={(results.infrastructure || []) as InfrastructureHit[]}
            />
          )}

          {/* Beneficial Ownership Tab (Phase 4) */}
          {activeTab === 'beneficial-ownership' && (
            <BeneficialOwnershipTab
              beneficialOwners={(results.beneficial_owners || []) as BeneficialOwner[]}
            />
          )}

          {/* Network Relations Tab (unified Network Graph + Subsidiaries) */}
          {activeTab === 'network-relations' && results.network_data && (() => {
            const formatSourceName = (source: string) => {
              switch (source) {
                case 'sec_edgar': return 'SEC EDGAR';
                case 'opencorporates_api': return 'OpenCorporates';
                case 'wikipedia': return 'Wikipedia';
                case 'duckduckgo': return 'DuckDuckGo';
                case 'google': return 'Google';
                default: return source || 'Unknown';
              }
            };

            // Entity Card Component (reusable for subsidiaries/sisters)
            const EntityCard = ({ entity, showOwnership = false }: { entity: any; showOwnership?: boolean }) => {

              return (
                <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-dim)', padding: '1rem 1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '0.625rem', flexWrap: 'wrap' }}>
                    <span className="font-editorial" style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-bright)' }}>
                      {entity.name}
                    </span>
                    {entity.level && (
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', letterSpacing: '0.1em', padding: '0.15rem 0.5rem', background: 'var(--bg-raised)', color: 'var(--cyan-bright)', border: '1px solid var(--cyan-dim)' }}>
                        Level {entity.level}
                      </span>
                    )}
                    {entity.relationship === 'sister' && (
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', letterSpacing: '0.1em', padding: '0.15rem 0.5rem', background: 'var(--bg-raised)', color: 'var(--amber-primary)', border: '1px solid var(--border-main)' }}>
                        Sister
                      </span>
                    )}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.625rem' }}>
                    {[
                      { label: 'Jurisdiction', value: entity.jurisdiction || '—' },
                      { label: 'Status', value: entity.status || '—' },
                      ...(showOwnership && entity.ownership_percentage > 0 ? [{ label: 'Ownership', value: `${entity.ownership_percentage}%` }] : []),
                    ].map(({ label, value }) => (
                      <div key={label}>
                        <div className="label-stamp" style={{ marginBottom: '0.2rem' }}>{label}</div>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-main)' }}>{value}</span>
                      </div>
                    ))}
                    <div>
                      <div className="label-stamp" style={{ marginBottom: '0.2rem' }}>Source</div>
                      {entity.reference_url ? (
                        <a href={entity.reference_url} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--amber-primary)', textDecoration: 'none', letterSpacing: '0.04em' }}>
                          {formatSourceName(entity.source)} →
                        </a>
                      ) : (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-main)' }}>
                          {formatSourceName(entity.source)}
                        </span>
                      )}
                    </div>
                  </div>

                  {entity.sanctions_hits !== undefined && entity.sanctions_hits > 0 && (
                    <div style={{ marginTop: '0.625rem', padding: '0.375rem 0.75rem', background: 'var(--risk-critical-bg)', border: '1px solid var(--risk-critical)' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--risk-critical-bright)', letterSpacing: '0.04em' }}>
                        ⚠ {entity.sanctions_hits} sanctions hit(s)
                      </span>
                    </div>
                  )}
                </div>
              );
            };

            // Determine entity type
            const hasParent = results.network_data?.parent_info;
            const hasSubsidiaries = results.subsidiaries && results.subsidiaries.length > 0;
            const hasSisters = (results.network_data as any)?.sisters?.length > 0;
            const hasNetworkGraph = (results.network_data as NetworkData).nodes && (results.network_data as NetworkData).nodes.length > 0;

            const sectionLabel = (text: string) => (
              <div className="label-stamp-bright" style={{ marginBottom: '0.75rem' }}>{text}</div>
            );
            const sectionNote = (text: string) => (
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.75rem', marginTop: 0 }}>{text}</p>
            );
            const cardStack = (children: React.ReactNode) => (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>{children}</div>
            );

            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {/* Network Graph */}
                {hasNetworkGraph && (
                  <div>
                    {sectionLabel('Network Visualization')}
                    <NetworkGraph networkData={results.network_data as NetworkData} height={600} />
                  </div>
                )}

                {/* Case 1: Entity is a CHILD (has parent company) */}
                {hasParent ? (
                  <>
                    {/* Parent company */}
                    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-main)', borderLeft: '2px solid var(--amber-primary)', padding: '1.25rem' }}>
                      <div className="label-stamp-bright" style={{ marginBottom: '0.875rem', color: 'var(--amber-light)' }}>
                        Parent Company Discovered
                      </div>
                      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-dim)', padding: '1rem 1.25rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                          <span className="font-editorial" style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-bright)' }}>
                            {(results.network_data.parent_info as any).name}
                          </span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', letterSpacing: '0.1em', padding: '0.15rem 0.5rem', background: 'var(--amber-pale)', color: 'var(--amber-deep)', border: '1px solid var(--amber-primary)' }}>
                            Parent
                          </span>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.625rem' }}>
                          {[
                            { label: 'Jurisdiction', value: (results.network_data.parent_info as any).jurisdiction || '—' },
                            { label: 'Relationship', value: (results.network_data.parent_info as any).relationship || 'Parent' },
                            ...(results.network_data.parent_info as any).confidence ? [{ label: 'Confidence', value: (results.network_data.parent_info as any).confidence }] : [],
                          ].map(({ label, value }) => (
                            <div key={label}>
                              <div className="label-stamp" style={{ marginBottom: '0.2rem' }}>{label}</div>
                              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-main)', textTransform: 'capitalize' }}>{value}</span>
                            </div>
                          ))}
                          {((results.network_data.parent_info as any).reference_url || (results.network_data.parent_info as any).source) && (
                            <div>
                              <div className="label-stamp" style={{ marginBottom: '0.2rem' }}>Source</div>
                              {(results.network_data.parent_info as any).reference_url ? (
                                <a href={(results.network_data.parent_info as any).reference_url} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--amber-primary)', textDecoration: 'none' }}>
                                  {formatSourceName((results.network_data.parent_info as any).source)} →
                                </a>
                              ) : (
                                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-main)' }}>
                                  {(results.network_data.parent_info as any).source === 'intelligence_report' ? 'Intelligence Report' : (results.network_data.parent_info as any).source}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Sister companies */}
                    {hasSisters ? (
                      <div>
                        {sectionLabel(`Sister Companies (${(results.network_data as any).sisters.length})`)}
                        {sectionNote(`Companies owned by the same parent (${(results.network_data.parent_info as any).name})`)}
                        {cardStack((results.network_data as any).sisters.map((sister: any, idx: number) => (
                          <EntityCard key={idx} entity={sister} showOwnership={false} />
                        )))}
                      </div>
                    ) : (
                      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-dim)', padding: '1.5rem', textAlign: 'center' }}>
                        <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>
                          No sister companies discovered — this may be the sole subsidiary of {(results.network_data.parent_info as any).name}.
                        </p>
                      </div>
                    )}

                    {/* Subsidiaries of this entity */}
                    {hasSubsidiaries && (
                      <div>
                        {sectionLabel(`Subsidiaries (${results.subsidiaries!.length})`)}
                        {sectionNote(`Companies owned or controlled by ${results.entity_name}`)}
                        {cardStack(results.subsidiaries!.map((subsidiary: any, idx: number) => (
                          <EntityCard key={idx} entity={subsidiary} showOwnership={false} />
                        )))}
                      </div>
                    )}
                  </>
                ) : hasSubsidiaries ? (
                  /* Case 2: Entity is a PARENT */
                  <div>
                    {sectionLabel(`Subsidiaries (${results.subsidiaries!.length})`)}
                    {sectionNote(`Companies owned or controlled by ${results.entity_name}`)}
                    {cardStack(results.subsidiaries!.map((subsidiary: any, idx: number) => (
                      <EntityCard key={idx} entity={subsidiary} showOwnership={false} />
                    )))}
                  </div>
                ) : (
                  /* Case 3: No corporate structure found */
                  <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border-dim)', padding: '2.5rem', textAlign: 'center' }}>
                    <div className="label-stamp-bright" style={{ marginBottom: '0.75rem' }}>No Corporate Structure Discovered</div>
                    <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: hasNetworkGraph ? '0.5rem' : '1rem', lineHeight: 1.6 }}>
                      No parent companies or subsidiaries were found for {results.entity_name} in public records.
                    </p>
                    {hasNetworkGraph && (
                      <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--text-faint)', marginBottom: '1rem', lineHeight: 1.6 }}>
                        Director and shareholder connections are shown in the network graph above.
                      </p>
                    )}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-faint)', alignItems: 'center' }}>
                      <span>Sources: SEC EDGAR · OpenCorporates · Wikipedia · DuckDuckGo</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      </main>
    </div>
  );
}
