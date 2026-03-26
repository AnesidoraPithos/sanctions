/**
 * Homepage - Entity Background Research
 *
 * Main search interface for sanctions screening and intelligence research.
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import SearchForm from '@/components/SearchForm';
import ProgressTracker from '@/components/ProgressTracker';
import { SearchRequest } from '@/lib/types';
import { api } from '@/lib/api-client';

export default function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSearchId, setActiveSearchId] = useState<string | null>(null);

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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold font-mono tracking-tight text-blue-400">
                Entity Background Research
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                Sanctions Screening • OSINT Intelligence • Risk Assessment
              </p>
            </div>
            <div className="text-xs text-gray-500">
              v1.0.0
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
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

        {/* Features Info */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-[#0d1425] border border-gray-800 rounded-lg p-4">
            <div className="text-blue-400 font-semibold text-sm mb-2">
              Sanctions Screening
            </div>
            <p className="text-xs text-gray-400">
              Check against 10+ global sanctions databases including OFAC, BIS Entity List, and more.
            </p>
          </div>
          <div className="bg-[#0d1425] border border-gray-800 rounded-lg p-4">
            <div className="text-blue-400 font-semibold text-sm mb-2">
              OSINT Intelligence
            </div>
            <p className="text-xs text-gray-400">
              Gather open-source intelligence from official government sources and media outlets.
            </p>
          </div>
          <div className="bg-[#0d1425] border border-gray-800 rounded-lg p-4">
            <div className="text-blue-400 font-semibold text-sm mb-2">
              AI Analysis
            </div>
            <p className="text-xs text-gray-400">
              Generate comprehensive intelligence reports with AI-powered analysis and risk assessment.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
