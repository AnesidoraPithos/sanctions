/**
 * Results Page - Display Entity Background Research Results
 *
 * Shows sanctions hits, media intelligence, risk level, and AI-generated report.
 */

'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import { ResultsResponse, SanctionsHit, MediaHit, NetworkData, FinancialIntelligence } from '@/lib/types';
import { api } from '@/lib/api-client';
import RiskBadge from '@/components/RiskBadge';
import TierBadge from '@/components/TierBadge';
import LoadingSpinner from '@/components/LoadingSpinner';
import NetworkGraph from '@/components/NetworkGraph';
import { format } from 'date-fns';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function ResultsPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const searchId = resolvedParams.id;

  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  type TabType = 'sanctions' | 'media' | 'report' | 'financial' | 'network-relations';
  const [activeTab, setActiveTab] = useState<TabType>('sanctions');

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const data = await api.getResults(searchId);
        setResults(data);
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

  // Set default active tab based on tier
  useEffect(() => {
    if (results && results.tier === 'network') {
      setActiveTab('network-relations');
    }
  }, [results]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0b1121] text-white flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading results..." />
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="min-h-screen bg-[#0b1121] text-white">
        <div className="max-w-4xl mx-auto px-4 py-16">
          <div className="bg-red-900/20 border border-red-700 rounded-lg p-8 text-center">
            <h1 className="text-2xl font-bold text-red-400 mb-4">Error Loading Results</h1>
            <p className="text-red-300 mb-6">{error}</p>
            <Link
              href="/"
              className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Return to Search
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
  const allMedia = [...officialSources, ...generalMedia, ...mediaData];

  return (
    <div className="min-h-screen bg-[#0b1121] text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-[#0d1425]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold font-mono text-blue-400">
                Background Research Results
              </h1>
            </div>
            <Link
              href="/"
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              ← New Search
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Card */}
        <div className="bg-[#0d1425] border border-gray-800 rounded-xl p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <p className="text-xs text-gray-400 mb-2">Entity Name</p>
              <p className="text-lg font-semibold">{results.entity_name}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-2">Risk Level</p>
              <RiskBadge
                level={results.risk_level}
                size="lg"
                explanation={results.risk_explanation}
              />
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-2">Tier</p>
              <div className="flex items-center gap-2">
                <TierBadge tier={results.tier} />
                {results.tier === 'network' && (
                  <span className="text-xs text-blue-400">
                    {results.metadata?.network_depth ? `(${results.metadata.network_depth}L)` : ''}
                  </span>
                )}
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-2">Timestamp</p>
              <p className="text-sm">{format(new Date(results.timestamp), 'PPpp')}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-800">
            <div>
              <p className="text-2xl font-bold text-blue-400">{results.sanctions_hits}</p>
              <p className="text-xs text-gray-400">Sanctions Hits</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-purple-400">{allMedia.length}</p>
              <p className="text-xs text-gray-400">Media Hits</p>
            </div>

            {/* Show network tier stats if available */}
            {results.tier === 'network' ? (
              <>
                <div>
                  <p className="text-2xl font-bold text-green-400">
                    {results.subsidiaries?.length || 0}
                  </p>
                  <p className="text-xs text-gray-400">Subsidiaries</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-orange-400">
                    {((results.financial_intelligence as FinancialIntelligence)?.directors?.length || 0) +
                     ((results.financial_intelligence as FinancialIntelligence)?.shareholders?.length || 0)}
                  </p>
                  <p className="text-xs text-gray-400">People</p>
                </div>
              </>
            ) : (
              <>
                <div>
                  <p className="text-2xl font-bold text-green-400">{officialSources.length}</p>
                  <p className="text-xs text-gray-400">Official Sources</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-yellow-400">{generalMedia.length}</p>
                  <p className="text-xs text-gray-400">General Media</p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Network Tier Confirmation Banner */}
        {results.tier === 'network' && (
          <div className="mb-6 bg-blue-900/20 border border-blue-700 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <span className="text-blue-400 text-xl">🔬</span>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-blue-400 mb-1">
                  Network Tier Research Completed
                </h4>
                <p className="text-sm text-blue-300">
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
                  <p className="text-xs text-blue-300/70 mt-1">
                    <strong>Data sources checked:</strong>{' '}
                    {(results.metadata.data_sources_used as string[]).map((source: string) => {
                      const displayName = source === 'opencorporates_api' ? 'OpenCorporates API' :
                                          source === 'sec_edgar' ? 'SEC EDGAR' :
                                          source === 'wikipedia' ? 'Wikipedia' :
                                          source === 'duckduckgo' ? 'DuckDuckGo' : source;
                      return displayName;
                    }).join(', ')}
                  </p>
                )}
                {results.metadata?.network_depth && (results.metadata.network_depth as number) > 1 ? (
                  <p className="text-xs text-blue-300/70 mt-2">
                    <strong>Search limits:</strong>{' '}
                    {(results.metadata.network_depth as number) >= 2 && (
                      <>Top {results.metadata.max_level_2_searches || 20} subsidiaries searched for level 2</>
                    )}
                    {(results.metadata.network_depth as number) >= 3 && (
                      <>, top {results.metadata.max_level_3_searches || 10} for level 3</>
                    )}
                  </p>
                ) : null}
              </div>
            </div>
          </div>
        )}

        {/* Warnings Banner (Network Tier) */}
        {results.warnings && results.warnings.length > 0 && (
          <div className="mb-6 bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <span className="text-yellow-400 text-xl">⚠️</span>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-yellow-400 mb-2">
                  Data Source Limitations
                </h4>
                <ul className="text-sm text-yellow-300 space-y-1">
                  {results.warnings.map((warning, idx) => (
                    <li key={idx}>• {warning.message}</li>
                  ))}
                </ul>
                {results.data_sources_used && results.data_sources_used.length > 0 && (
                  <p className="text-xs text-yellow-300/70 mt-2">
                    Data sources used: {results.data_sources_used.join(', ')}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-800 mb-6">
          <nav className="flex gap-6">
            <button
              onClick={() => setActiveTab('sanctions')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'sanctions'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              Sanctions Hits ({results.sanctions_hits})
            </button>
            <button
              onClick={() => setActiveTab('media')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'media'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              Media Intelligence ({allMedia.length})
            </button>
            <button
              onClick={() => setActiveTab('report')}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'report'
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              Intelligence Report
            </button>

            {/* Network Tier Tabs */}
            {results.tier === 'network' && results.network_data && (
              <>
                <button
                  onClick={() => setActiveTab('financial')}
                  className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'financial'
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-gray-400 hover:text-white'
                  }`}
                >
                  Financial Intelligence
                </button>
                <button
                  onClick={() => setActiveTab('network-relations')}
                  className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'network-relations'
                      ? 'border-blue-500 text-blue-400'
                      : 'border-transparent text-gray-400 hover:text-white'
                  }`}
                >
                  Network Relations (
                    {(results.network_data?.parent_info ? 1 : 0) +
                     (results.subsidiaries?.length || 0) +
                     ((results.network_data as any)?.sisters?.length || 0)}
                  )
                </button>
              </>
            )}
          </nav>
        </div>

        {/* Tab Content */}
        <div>
          {/* Sanctions Tab */}
          {activeTab === 'sanctions' && (
            <div className="space-y-4">
              {results.sanctions_data.length === 0 ? (
                <div className="bg-green-900/20 border border-green-700 rounded-lg p-8 text-center">
                  <p className="text-green-400">✓ No sanctions matches found</p>
                </div>
              ) : (
                results.sanctions_data.map((hit: SanctionsHit, idx: number) => (
                  <div key={idx} className="bg-[#0d1425] border border-gray-800 rounded-lg p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold">{hit.name}</h3>
                          <span className={`text-xs px-2 py-1 rounded ${
                            hit.match_quality === 'EXACT' ? 'bg-red-600' :
                            hit.match_quality === 'HIGH' ? 'bg-orange-600' :
                            hit.match_quality === 'MEDIUM' ? 'bg-yellow-600' :
                            'bg-gray-600'
                          }`}>
                            {hit.match_quality} ({hit.combined_score.toFixed(0)}%)
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                          <div>
                            <span className="text-gray-400">List:</span>
                            <span className="ml-2 text-white">{hit.list}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Type:</span>
                            <span className="ml-2 text-white">{hit.type}</span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-400 mb-2">
                          <span className="font-medium">Address:</span> {hit.address}
                        </p>
                        <p className="text-sm text-gray-300">{hit.remark}</p>
                      </div>
                    </div>
                    {hit.link && (
                      <a
                        href={hit.link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 text-xs mt-3 inline-block"
                      >
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
            <div className="space-y-4">
              {allMedia.length === 0 ? (
                <div className="bg-gray-800/20 border border-gray-700 rounded-lg p-8 text-center">
                  <p className="text-gray-400">No media intelligence found</p>
                </div>
              ) : (
                allMedia.map((hit: MediaHit, idx: number) => (
                  <div key={idx} className="bg-[#0d1425] border border-gray-800 rounded-lg p-5">
                    <div className="flex items-start gap-3 mb-2">
                      <span className={`text-xs px-2 py-1 rounded flex-shrink-0 ${
                        hit.source_type === 'official' ? 'bg-green-600' : 'bg-blue-600'
                      }`}>
                        {hit.source_type === 'official' ? 'OFFICIAL' : 'MEDIA'}
                      </span>
                      <h3 className="text-base font-semibold flex-1">{hit.title}</h3>
                    </div>
                    <p className="text-sm text-gray-400 mb-3">{hit.snippet}</p>
                    {hit.relevance && (
                      <p className="text-xs text-green-400 mb-2">✓ {hit.relevance}</p>
                    )}
                    <a
                      href={hit.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 text-xs"
                    >
                      Read More →
                    </a>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Intelligence Report Tab */}
          {activeTab === 'report' && (
            <div className="bg-[#0d1425] border border-gray-800 rounded-lg p-6">
              {results.intelligence_report ? (
                <div
                  className="prose prose-invert max-w-none prose-headings:text-white prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg prose-p:text-gray-300 prose-a:text-blue-400 prose-strong:text-white prose-ul:text-gray-300"
                  dangerouslySetInnerHTML={{
                    __html: results.intelligence_report
                      .replace(/^# /gm, '<h1>')
                      .replace(/\n/g, '</h1>\n')
                      .replace(/^## /gm, '<h2>')
                      .replace(/^### /gm, '<h3>')
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>')
                  }}
                />
              ) : (
                <p className="text-gray-400 text-center py-8">
                  No intelligence report available
                </p>
              )}
            </div>
          )}

          {/* Financial Intelligence Tab */}
          {activeTab === 'financial' && results.financial_intelligence && (() => {
            const financialIntel = results.financial_intelligence as FinancialIntelligence;
            return (
              <div className="space-y-6">
                {/* Directors & Officers */}
                {financialIntel.directors && financialIntel.directors.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">
                      Directors & Officers ({financialIntel.directors.length})
                    </h3>
                    <div className="bg-[#0d1425] border border-gray-800 rounded-lg overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-900/50">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Name</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Title</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Nationality</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Sanctions</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-800">
                            {financialIntel.directors.map((director, idx) => (
                              <tr key={idx} className="hover:bg-gray-900/30">
                                <td className="px-4 py-3 text-white">{director.name}</td>
                                <td className="px-4 py-3 text-gray-300">{director.title || '-'}</td>
                                <td className="px-4 py-3 text-gray-300">{director.nationality || '-'}</td>
                                <td className="px-4 py-3">
                                  {director.sanctions_hits && director.sanctions_hits > 0 ? (
                                    <span className="text-xs px-2 py-1 bg-red-900/30 text-red-400 rounded">
                                      {director.sanctions_hits} hit(s)
                                    </span>
                                  ) : (
                                    <span className="text-gray-500 text-xs">None</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}

                {/* Shareholders */}
                {financialIntel.shareholders && financialIntel.shareholders.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">
                      Major Shareholders ({financialIntel.shareholders.length})
                    </h3>
                    <div className="bg-[#0d1425] border border-gray-800 rounded-lg overflow-hidden">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-900/50">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Name</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Type</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Ownership %</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Jurisdiction</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Sanctions</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-800">
                            {financialIntel.shareholders.map((shareholder, idx) => (
                              <tr key={idx} className="hover:bg-gray-900/30">
                                <td className="px-4 py-3 text-white">{shareholder.name}</td>
                                <td className="px-4 py-3 text-gray-300">{shareholder.type || '-'}</td>
                                <td className="px-4 py-3 text-gray-300">{shareholder.ownership_percentage || 0}%</td>
                                <td className="px-4 py-3 text-gray-300">{shareholder.jurisdiction || '-'}</td>
                                <td className="px-4 py-3">
                                  {shareholder.sanctions_hits && shareholder.sanctions_hits > 0 ? (
                                    <span className="text-xs px-2 py-1 bg-red-900/30 text-red-400 rounded">
                                      {shareholder.sanctions_hits} hit(s)
                                    </span>
                                  ) : (
                                    <span className="text-gray-500 text-xs">None</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                )}

                {/* Transactions */}
                {financialIntel.transactions && financialIntel.transactions.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">
                      Related Party Transactions ({financialIntel.transactions.length})
                    </h3>
                    <div className="space-y-3">
                      {financialIntel.transactions.map((transaction, idx) => (
                        <div key={idx} className="bg-[#0d1425] border border-gray-800 rounded-lg p-4">
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <span className="text-gray-400 text-xs">Type:</span>
                              <p className="text-white">{transaction.transaction_type || '-'}</p>
                            </div>
                            <div>
                              <span className="text-gray-400 text-xs">Counterparty:</span>
                              <p className="text-white">{transaction.counterparty || '-'}</p>
                            </div>
                            <div>
                              <span className="text-gray-400 text-xs">Amount:</span>
                              <p className="text-white">
                                {transaction.currency} {transaction.amount?.toLocaleString() || '-'}
                              </p>
                            </div>
                            <div>
                              <span className="text-gray-400 text-xs">Date:</span>
                              <p className="text-white">{transaction.transaction_date || '-'}</p>
                            </div>
                          </div>
                          {transaction.purpose && (
                            <p className="text-sm text-gray-400 mt-3">
                              <span className="font-medium">Purpose:</span> {transaction.purpose}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* No Financial Intelligence */}
                {(!financialIntel.directors || financialIntel.directors.length === 0) &&
                 (!financialIntel.shareholders || financialIntel.shareholders.length === 0) &&
                 (!financialIntel.transactions || financialIntel.transactions.length === 0) && (
                  <div className="bg-gray-800/20 border border-gray-700 rounded-lg p-8 text-center">
                    <p className="text-gray-400">
                      No financial intelligence data found. This is normal for private companies or non-US entities.
                    </p>
                  </div>
                )}
              </div>
            );
          })()}

          {/* Network Relations Tab (unified Network Graph + Subsidiaries) */}
          {activeTab === 'network-relations' && results.network_data && (() => {
            // Entity Card Component (reusable for subsidiaries/sisters)
            const EntityCard = ({ entity, showOwnership = false }: { entity: any; showOwnership?: boolean }) => {
              // Helper function to format source name
              const formatSourceName = (source: string) => {
                switch (source) {
                  case 'sec_edgar': return 'SEC EDGAR';
                  case 'opencorporates_api': return 'OpenCorporates';
                  case 'wikipedia': return 'Wikipedia';
                  case 'duckduckgo': return 'DuckDuckGo';
                  default: return source || 'Unknown';
                }
              };

              return (
                <div className="bg-[#0d1425] border border-gray-800 rounded-lg p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-white">{entity.name}</h3>
                        {entity.level && (
                          <span className="text-xs px-2 py-1 bg-blue-900/30 text-blue-300 rounded">
                            Level {entity.level}
                          </span>
                        )}
                        {entity.relationship === 'sister' && (
                          <span className="text-xs px-2 py-1 bg-purple-900/30 text-purple-300 rounded">
                            Sister Company
                          </span>
                        )}
                      </div>

                      {/* Data grid - removed ownership, added source */}
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm mb-3">
                        <div>
                          <span className="text-gray-400">Jurisdiction:</span>
                          <span className="ml-2 text-white">{entity.jurisdiction || '-'}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Status:</span>
                          <span className="ml-2 text-white">{entity.status || '-'}</span>
                        </div>
                        {/* Source with link */}
                        <div>
                          <span className="text-gray-400">Source:</span>
                          {entity.reference_url ? (
                            <a
                              href={entity.reference_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="ml-2 text-blue-400 hover:underline text-sm"
                            >
                              {formatSourceName(entity.source)}
                            </a>
                          ) : (
                            <span className="ml-2 text-white">
                              {formatSourceName(entity.source)}
                            </span>
                          )}
                        </div>
                        {/* Optional: Only show ownership if explicitly requested and not null */}
                        {showOwnership && entity.ownership_percentage !== undefined && entity.ownership_percentage > 0 && (
                          <div>
                            <span className="text-gray-400">Ownership:</span>
                            <span className="ml-2 text-white">{entity.ownership_percentage}%</span>
                          </div>
                        )}
                      </div>

                      {/* Sanctions warning */}
                      {entity.sanctions_hits !== undefined && entity.sanctions_hits > 0 && (
                        <div className="mt-3 p-2 bg-red-900/20 border border-red-700 rounded">
                          <span className="text-red-400 font-semibold text-sm">
                            ⚠️ {entity.sanctions_hits} sanctions hit(s)
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            };

            // Determine entity type
            const hasParent = results.network_data?.parent_info;
            const hasSubsidiaries = results.subsidiaries && results.subsidiaries.length > 0;
            const hasSisters = (results.network_data as any)?.sisters?.length > 0;
            const hasNetworkGraph = (results.network_data as NetworkData).nodes && (results.network_data as NetworkData).nodes.length > 0;

            return (
              <div className="space-y-6">
                {/* Section 1: Network Graph (always at top if available) */}
                {hasNetworkGraph && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">
                      Network Visualization
                    </h3>
                    <NetworkGraph
                      networkData={results.network_data as NetworkData}
                      height={600}
                    />
                  </div>
                )}

                {/* Section 2: Smart entity display based on type */}
                {/* Case 1: Entity is a CHILD (has parent company) */}
                {hasParent ? (
                  <>
                    {/* Display parent company first */}
                    <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-5">
                      <div className="flex items-start gap-3">
                        <span className="text-purple-400 text-2xl">⬆️</span>
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-purple-400 mb-3">
                            Parent Company Discovered
                          </h3>
                          <div className="bg-[#0d1425] border border-purple-800 rounded-lg p-4">
                            <div className="flex items-center gap-3 mb-2">
                              <h4 className="text-xl font-semibold text-white">
                                {(results.network_data.parent_info as any).name}
                              </h4>
                              <span className="text-xs px-2 py-1 bg-purple-900/30 text-purple-300 rounded">
                                Parent
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <span className="text-gray-400">Jurisdiction:</span>
                                <span className="ml-2 text-white">
                                  {(results.network_data.parent_info as any).jurisdiction || '-'}
                                </span>
                              </div>
                              <div>
                                <span className="text-gray-400">Relationship:</span>
                                <span className="ml-2 text-white capitalize">
                                  {(results.network_data.parent_info as any).relationship || 'Parent'}
                                </span>
                              </div>
                              {(results.network_data.parent_info as any).confidence && (
                                <div>
                                  <span className="text-gray-400">Confidence:</span>
                                  <span className="ml-2 text-white capitalize">
                                    {(results.network_data.parent_info as any).confidence}
                                  </span>
                                </div>
                              )}
                              {(results.network_data.parent_info as any).reference_url && (
                                <div className="col-span-2">
                                  <span className="text-gray-400">Source:</span>
                                  <a
                                    href={(results.network_data.parent_info as any).reference_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="ml-2 text-blue-400 hover:underline text-sm"
                                  >
                                    {(results.network_data.parent_info as any).source === 'sec_edgar' ? 'SEC EDGAR' :
                                     (results.network_data.parent_info as any).source === 'opencorporates_api' ? 'OpenCorporates' :
                                     (results.network_data.parent_info as any).source === 'wikipedia' ? 'Wikipedia' :
                                     (results.network_data.parent_info as any).source === 'duckduckgo' ? 'DuckDuckGo' :
                                     (results.network_data.parent_info as any).source || 'View Source'}
                                  </a>
                                </div>
                              )}
                            </div>
                            <p className="text-xs text-gray-500 mt-3">
                              This entity is owned by or is a subsidiary of the parent company shown above.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Display sister companies */}
                    {hasSisters ? (
                      <div>
                        <h3 className="text-lg font-semibold text-white mb-4">
                          Sister Companies ({(results.network_data as any).sisters.length})
                        </h3>
                        <p className="text-sm text-gray-400 mb-4">
                          Companies owned by the same parent company ({(results.network_data.parent_info as any).name})
                        </p>
                        <div className="space-y-3">
                          {(results.network_data as any).sisters.map((sister: any, idx: number) => (
                            <EntityCard key={idx} entity={sister} showOwnership={false} />
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-gray-800/20 border border-gray-700 rounded-lg p-6 text-center">
                        <p className="text-gray-400">
                          No sister companies discovered. This may be the only subsidiary of {(results.network_data.parent_info as any).name}.
                        </p>
                      </div>
                    )}
                  </>
                ) : hasSubsidiaries ? (
                  /* Case 2: Entity is a PARENT (has subsidiaries but no parent) */
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-4">
                      Subsidiaries ({results.subsidiaries!.length})
                    </h3>
                    <p className="text-sm text-gray-400 mb-4">
                      Companies owned or controlled by {results.entity_name}
                    </p>
                    <div className="space-y-3">
                      {results.subsidiaries!.map((subsidiary: any, idx: number) => (
                        <EntityCard key={idx} entity={subsidiary} showOwnership={false} />
                      ))}
                    </div>
                  </div>
                ) : (
                  /* Case 3: STANDALONE entity (no parent, no subsidiaries) */
                  <div className="bg-gray-800/20 border border-gray-700 rounded-lg p-8">
                    <div className="text-center">
                      <div className="text-4xl mb-4">🏢</div>
                      <h3 className="text-lg font-semibold text-white mb-2">
                        Standalone Entity
                      </h3>
                      <p className="text-gray-400 mb-4">
                        {results.entity_name} appears to be a standalone entity with no parent company or subsidiaries in public records.
                      </p>
                      <div className="text-sm text-gray-500 space-y-2">
                        <p><strong>Data sources checked:</strong></p>
                        <ul className="list-none text-left max-w-md mx-auto space-y-1">
                          <li>• SEC EDGAR filings (Exhibit 21.1)</li>
                          <li>• OpenCorporates database</li>
                          <li>• Wikipedia corporate structure data</li>
                          <li>• DuckDuckGo web search</li>
                        </ul>
                        <p className="mt-4 text-xs">
                          This is normal for private companies, small businesses, or individuals.
                        </p>
                      </div>
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
