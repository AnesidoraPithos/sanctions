/**
 * Results Page - Display Entity Background Research Results
 *
 * Shows sanctions hits, media intelligence, risk level, and AI-generated report.
 */

'use client';

import { use, useEffect, useState } from 'react';
import Link from 'next/link';
import { ResultsResponse, SanctionsHit, MediaHit } from '@/lib/types';
import { api } from '@/lib/api-client';
import RiskBadge from '@/components/RiskBadge';
import TierBadge from '@/components/TierBadge';
import LoadingSpinner from '@/components/LoadingSpinner';
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
  const [activeTab, setActiveTab] = useState<'sanctions' | 'media' | 'report'>('sanctions');

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
              <RiskBadge level={results.risk_level} size="lg" />
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-2">Tier</p>
              <TierBadge tier={results.tier} />
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
            <div>
              <p className="text-2xl font-bold text-green-400">{officialSources.length}</p>
              <p className="text-xs text-gray-400">Official Sources</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-400">{generalMedia.length}</p>
              <p className="text-xs text-gray-400">General Media</p>
            </div>
          </div>
        </div>

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
        </div>
      </main>
    </div>
  );
}
