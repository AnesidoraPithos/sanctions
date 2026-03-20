/**
 * SearchForm Component
 *
 * Main search form for entity background research.
 */

'use client';

import { useState } from 'react';
import { SearchRequest, ResearchTier } from '@/lib/types';
import TierSelector from './TierSelector';

interface SearchFormProps {
  onSearch: (request: SearchRequest) => void;
  isLoading: boolean;
}

const COUNTRIES = [
  'China',
  'Russia',
  'Iran',
  'North Korea',
  'Syria',
  'Venezuela',
  'Cuba',
  'Myanmar',
  'Belarus',
  'Other',
];

export default function SearchForm({ onSearch, isLoading }: SearchFormProps) {
  const [entityName, setEntityName] = useState('');
  const [country, setCountry] = useState('');
  const [fuzzyThreshold, setFuzzyThreshold] = useState(80);
  // Phase 2: Network tier support
  const [tier, setTier] = useState<ResearchTier>('base');
  const [networkDepth, setNetworkDepth] = useState(1);
  const [ownershipThreshold, setOwnershipThreshold] = useState(0);
  const [includeSisters, setIncludeSisters] = useState(true);
  // Phase 2 enhancement: Search limits
  const [maxLevel2Searches, setMaxLevel2Searches] = useState(20);
  const [maxLevel3Searches, setMaxLevel3Searches] = useState(10);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!entityName.trim()) {
      alert('Please enter an entity name');
      return;
    }

    const request: SearchRequest = {
      entity_name: entityName.trim(),
      country: country || undefined,
      fuzzy_threshold: fuzzyThreshold,
      tier,
      // Include network parameters if network tier selected
      ...(tier === 'network' && {
        network_depth: networkDepth,
        ownership_threshold: ownershipThreshold,
        include_sisters: includeSisters,
        max_level_2_searches: maxLevel2Searches,
        max_level_3_searches: maxLevel3Searches,
      }),
    };

    onSearch(request);
  };

  // Get estimated duration based on tier
  const getEstimatedDuration = () => {
    if (tier === 'base') return '30-60 seconds';
    if (tier === 'network') {
      if (networkDepth === 1) return '2-5 minutes';
      if (networkDepth === 2) return '5-7 minutes';
      return '7-10 minutes';
    }
    return '5-15 minutes'; // deep
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Research Tier Selector */}
      <TierSelector
        selectedTier={tier}
        onTierChange={setTier}
        networkDepth={networkDepth}
        onNetworkDepthChange={setNetworkDepth}
        ownershipThreshold={ownershipThreshold}
        onOwnershipThresholdChange={setOwnershipThreshold}
        includeSisters={includeSisters}
        onIncludeSistersChange={setIncludeSisters}
        maxLevel2Searches={maxLevel2Searches}
        onMaxLevel2SearchesChange={setMaxLevel2Searches}
        maxLevel3Searches={maxLevel3Searches}
        onMaxLevel3SearchesChange={setMaxLevel3Searches}
      />

      {/* Entity Name Input */}
      <div>
        <label
          htmlFor="entity-name"
          className="block text-sm font-medium text-gray-200 mb-2"
        >
          Entity Name <span className="text-red-400">*</span>
        </label>
        <input
          id="entity-name"
          type="text"
          value={entityName}
          onChange={(e) => setEntityName(e.target.value)}
          placeholder="e.g., Huawei Technologies"
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
          required
        />
        <p className="text-xs text-gray-500 mt-1">
          Enter the company or individual name to research
        </p>
      </div>

      {/* Country Filter */}
      <div>
        <label
          htmlFor="country"
          className="block text-sm font-medium text-gray-200 mb-2"
        >
          Country (Optional)
        </label>
        <select
          id="country"
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isLoading}
        >
          <option value="">All Countries</option>
          {COUNTRIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Fuzzy Threshold Slider */}
      <div>
        <label
          htmlFor="fuzzy-threshold"
          className="block text-sm font-medium text-gray-200 mb-2"
        >
          Fuzzy Match Threshold: <span className="text-blue-400">{fuzzyThreshold}%</span>
        </label>
        <input
          id="fuzzy-threshold"
          type="range"
          min="0"
          max="100"
          step="5"
          value={fuzzyThreshold}
          onChange={(e) => setFuzzyThreshold(parseInt(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          disabled={isLoading}
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>0% (Loose)</span>
          <span>50% (Moderate)</span>
          <span>100% (Exact)</span>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Higher values = stricter matching (recommended: 70-90%)
        </p>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading || !entityName.trim()}
        className="w-full px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors duration-200 flex items-center justify-center gap-3"
      >
        {isLoading ? (
          <>
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
            <span>Searching... ({getEstimatedDuration()})</span>
          </>
        ) : (
          <>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                clipRule="evenodd"
              />
            </svg>
            <span>Start {tier.charAt(0).toUpperCase() + tier.slice(1)} Tier Research</span>
          </>
        )}
      </button>

      {/* Info Message */}
      {isLoading && (
        <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
          <p className="text-sm text-blue-300">
            <strong>{tier.charAt(0).toUpperCase() + tier.slice(1)} Tier Research:</strong>{" "}
            {tier === 'base' &&
              "Performing sanctions screening, OSINT media intelligence, and generating AI-powered intelligence report..."
            }
            {tier === 'network' &&
              `Performing base tier research, discovering corporate structure (depth ${networkDepth}), extracting financial intelligence, and building network graph...`
            }
            {tier === 'deep' &&
              "Performing comprehensive deep tier analysis including financial flows, trade data, and advanced risk assessment..."
            }
          </p>
        </div>
      )}
    </form>
  );
}
