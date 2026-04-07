'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { api } from '@/lib/api-client';
import { HistoryEntry, RiskLevel, ResearchTier } from '@/lib/types';

const RISK_COLORS: Record<RiskLevel, string> = {
  SAFE: 'bg-green-900/40 text-green-400 border-green-700',
  LOW: 'bg-blue-900/40 text-blue-400 border-blue-700',
  MID: 'bg-yellow-900/40 text-yellow-400 border-yellow-700',
  HIGH: 'bg-orange-900/40 text-orange-400 border-orange-700',
  VERY_HIGH: 'bg-red-900/40 text-red-400 border-red-700',
};

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

  useEffect(() => {
    api.getSavedSearches()
      .then((data) => { setEntries(data.entries); setIsLoading(false); })
      .catch(() => { setError('Failed to load saved searches'); setIsLoading(false); });
  }, []);

  const handleUnsave = async (searchId: string) => {
    // Optimistic remove
    setEntries((prev) => prev.filter((e) => e.search_id !== searchId));
    try {
      await api.unsaveResult(searchId);
    } catch {
      // Re-fetch on failure
      api.getSavedSearches().then((data) => setEntries(data.entries)).catch(() => {});
    }
  };

  return (
    <div className="min-h-screen bg-[#0b1121] text-white">
      <header className="border-b border-gray-800 bg-[#0d1425]">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-4 lg:px-6 py-6">
          <div className="flex flex-wrap items-center justify-between gap-y-3">
            <div className="flex items-center gap-3">
              <Image src="/bear-logo.png" alt="BEAR² Logo" width={144} height={144} className="rounded" />
              <div>
                <h1 className="text-2xl font-bold font-mono tracking-tight text-blue-400">
                  BEAR<sup>2</sup>
                </h1>
                <p className="text-sm text-gray-400">Saved Searches</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              {entries.length > 0 && (
                <span className="bg-blue-900/40 border border-blue-700 text-blue-400 text-sm px-3 py-1 rounded-full">
                  {entries.length} saved
                </span>
              )}
              <Link href="/" className="text-sm text-gray-400 hover:text-white transition-colors">
                ← Back to Search
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-screen-2xl mx-auto px-4 sm:px-4 lg:px-6 py-8">
        {isLoading && (
          <div className="text-center text-gray-400 py-16">Loading saved searches...</div>
        )}

        {error && (
          <div className="text-center text-red-400 py-16">{error}</div>
        )}

        {!isLoading && !error && entries.length === 0 && (
          <div className="text-center py-20">
            <svg className="w-12 h-12 text-gray-600 mx-auto mb-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
            </svg>
            <p className="text-gray-400 text-lg">No saved searches yet.</p>
            <p className="text-gray-500 text-sm mt-1">
              Use the bookmark button on any results page to save important findings.
            </p>
            <Link href="/" className="inline-block mt-6 px-5 py-2 bg-blue-700 hover:bg-blue-600 rounded-lg text-sm transition-colors">
              Start a Search
            </Link>
          </div>
        )}

        {!isLoading && !error && entries.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {entries.map((entry) => (
              <div
                key={entry.search_id}
                className="bg-[#0d1425] border border-gray-800 rounded-xl p-5 flex flex-col gap-3 hover:border-gray-600 transition-colors"
              >
                {/* Entity name + badges */}
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-white text-sm leading-snug">{entry.entity_name}</h3>
                  <button
                    onClick={() => handleUnsave(entry.search_id)}
                    title="Remove bookmark"
                    className="text-gray-500 hover:text-red-400 transition-colors flex-shrink-0 mt-0.5"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </button>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-sm px-2 py-0.5 rounded border font-medium ${RISK_COLORS[entry.risk_level as RiskLevel] ?? 'text-gray-400 border-gray-600'}`}>
                    {entry.risk_level}
                  </span>
                  <span className="text-sm px-2 py-0.5 rounded border border-gray-600 text-gray-400">
                    {TIER_LABELS[entry.tier as ResearchTier] ?? entry.tier}
                  </span>
                </div>

                {/* Label */}
                {entry.save_label && (
                  <p className="text-sm text-blue-300 italic">"{entry.save_label}"</p>
                )}

                {/* Timestamps */}
                <div className="text-sm text-gray-500 space-y-0.5">
                  <div>Searched: {formatDate(entry.timestamp)}</div>
                  {entry.saved_at && <div>Saved: {formatDate(entry.saved_at)}</div>}
                </div>

                {/* View link */}
                <Link
                  href={`/results/${entry.search_id}`}
                  className="mt-auto inline-block text-center w-full py-2 bg-blue-900/40 hover:bg-blue-800/60 border border-blue-700 text-blue-400 text-sm rounded-lg transition-colors"
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
