/**
 * Homepage - Entity Background Research
 *
 * Main search interface for sanctions screening and intelligence research.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import SearchForm from '@/components/SearchForm';
import ProgressTracker from '@/components/ProgressTracker';
import { SearchRequest, HistoryEntry, RiskLevel } from '@/lib/types';
import { api } from '@/lib/api-client';

const RISK_COLORS: Record<RiskLevel, string> = {
  SAFE: 'text-green-400',
  LOW: 'text-blue-400',
  MID: 'text-yellow-400',
  HIGH: 'text-orange-400',
  VERY_HIGH: 'text-red-400',
};

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

    // Pre-generate a UUID for network/deep searches so WebSocket can connect before response
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
    <div className="min-h-screen bg-[#0b1121] text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-[#0d1425]">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-4 lg:px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Image src="/bear-logo.png" alt="BEAR² Logo" width={160} height={160} className="rounded" />
              <div>
                <h1 className="text-3xl font-bold font-mono tracking-tight text-blue-400">
                  BEAR<sup>2</sup>
                </h1>
                <p className="text-sm text-gray-400">
                  Background Entity Assessment &amp; Risk Research
                </p>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              v1.1.0
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-screen-2xl mx-auto px-4 sm:px-4 lg:px-6 py-12">
        <div className="bg-[#0d1425] border border-gray-800 rounded-xl p-8 shadow-2xl">
          {/* Title */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-2">
              Start Background Research
            </h2>
            <p className="text-gray-400 text-sm">
              Enter an entity name to perform comprehensive sanctions screening and intelligence analysis.
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 bg-red-900/20 border border-red-700 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <div>
                  <h3 className="text-sm font-semibold text-red-400">Search Error</h3>
                  <p className="text-sm text-red-300 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Search Form */}
          <SearchForm onSearch={handleSearch} isLoading={isLoading} />

          {/* Live progress tracker (shown for network/deep tier searches) */}
          <ProgressTracker searchId={activeSearchId} />
        </div>

        {/* Recent Searches */}
        {recentSearches.length > 0 && (
          <div className="mt-6 bg-[#0d1425] border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-300">Recent Searches</h3>
              {savedCount > 0 && (
                <Link
                  href="/saved"
                  className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                >
                  View {savedCount} saved search{savedCount !== 1 ? 'es' : ''} →
                </Link>
              )}
            </div>
            <div className="divide-y divide-gray-800">
              {recentSearches.map((entry) => (
                <div key={entry.search_id} className="flex items-center justify-between py-2 gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`text-sm font-semibold flex-shrink-0 ${RISK_COLORS[entry.risk_level as RiskLevel] ?? 'text-gray-400'}`}>
                      {entry.risk_level}
                    </span>
                    <span className="text-sm text-white truncate">{entry.entity_name}</span>
                    <span className="text-sm text-gray-500 flex-shrink-0 hidden sm:inline capitalize">{entry.tier}</span>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="text-sm text-gray-500 hidden md:inline">
                      {new Date(entry.timestamp).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
                    </span>
                    <Link
                      href={`/results/${entry.search_id}`}
                      className="text-sm text-blue-400 hover:text-blue-300 transition-colors whitespace-nowrap"
                    >
                      View →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
            {savedCount === 0 && (
              <Link href="/saved" className="mt-3 block text-sm text-gray-500 hover:text-gray-400 transition-colors">
                Saved searches →
              </Link>
            )}
          </div>
        )}

        {/* Features Info */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#0d1425] border border-gray-800 rounded-lg p-4">
            <div className="text-blue-400 font-semibold text-sm mb-2">
              Sanctions Screening
            </div>
            <p className="text-sm text-gray-400">
              Check against 10+ global sanctions databases including OFAC, BIS Entity List, and more.
            </p>
          </div>
          <div className="bg-[#0d1425] border border-gray-800 rounded-lg p-4">
            <div className="text-blue-400 font-semibold text-sm mb-2">
              OSINT Intelligence
            </div>
            <p className="text-sm text-gray-400">
              Gather open-source intelligence from official government sources and media outlets.
            </p>
          </div>
          <div className="bg-[#0d1425] border border-gray-800 rounded-lg p-4">
            <div className="text-blue-400 font-semibold text-sm mb-2">
              AI Analysis
            </div>
            <p className="text-sm text-gray-400">
              Generate comprehensive intelligence reports with AI-powered analysis and risk assessment.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
