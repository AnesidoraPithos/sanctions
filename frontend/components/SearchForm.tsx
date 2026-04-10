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
  const [tier, setTier] = useState<ResearchTier>('base');
  const [networkDepth, setNetworkDepth] = useState(1);
  const [ownershipThreshold, setOwnershipThreshold] = useState(0);
  const [includeSisters, setIncludeSisters] = useState(true);
  const [maxLevel2Searches, setMaxLevel2Searches] = useState(20);
  const [maxLevel3Searches, setMaxLevel3Searches] = useState(10);
  const [includeFinancialFlows, setIncludeFinancialFlows] = useState(true);
  const [includeDirectorPivot, setIncludeDirectorPivot] = useState(true);
  const [includeInfrastructure, setIncludeInfrastructure] = useState(true);
  const [includeBeneficialOwnership, setIncludeBeneficialOwnership] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!entityName.trim()) return;
    const request: SearchRequest = {
      entity_name: entityName.trim(),
      country: country || undefined,
      fuzzy_threshold: fuzzyThreshold,
      tier,
      ...((tier === 'network' || tier === 'deep') && {
        network_depth: networkDepth,
        ownership_threshold: ownershipThreshold,
        include_sisters: includeSisters,
        max_level_2_searches: maxLevel2Searches,
        max_level_3_searches: maxLevel3Searches,
      }),
      ...(tier === 'deep' && {
        include_director_pivot: includeDirectorPivot,
        include_infrastructure: includeInfrastructure,
        include_beneficial_ownership: includeBeneficialOwnership,
      }),
    };
    onSearch(request);
  };

  const getEstimatedDuration = () => {
    if (tier === 'base') return '30–60s';
    if (tier === 'network') {
      if (networkDepth === 1) return '2–5 min';
      if (networkDepth === 2) return '5–7 min';
      return '7–10 min';
    }
    return '5–15 min';
  };

  const tierDescriptions: Record<ResearchTier, string> = {
    base: 'Performing sanctions screening, OSINT media intelligence, and generating AI-powered intelligence report...',
    network: `Performing base tier research, discovering corporate structure (depth ${networkDepth}), extracting financial intelligence, and building network graph...`,
    deep: 'Performing comprehensive deep tier analysis including financial flows, trade data, and advanced risk assessment...',
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Tier Selector */}
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
        includeFinancialFlows={includeFinancialFlows}
        onIncludeFinancialFlowsChange={setIncludeFinancialFlows}
        includeDirectorPivot={includeDirectorPivot}
        onIncludeDirectorPivotChange={setIncludeDirectorPivot}
        includeInfrastructure={includeInfrastructure}
        onIncludeInfrastructureChange={setIncludeInfrastructure}
        includeBeneficialOwnership={includeBeneficialOwnership}
        onIncludeBeneficialOwnershipChange={setIncludeBeneficialOwnership}
      />

      {/* ── Entity Name ────────────────────────────────────── */}
      <div>
        <label
          htmlFor="entity-name"
          className="label-stamp"
          style={{ display: 'block', marginBottom: '0.5rem' }}
        >
          Target Entity Designation{' '}
          <span style={{ color: 'var(--risk-critical)' }}>*</span>
        </label>
        <input
          id="entity-name"
          type="text"
          value={entityName}
          onChange={(e) => setEntityName(e.target.value)}
          placeholder="e.g., Huawei Technologies Co., Ltd."
          className="intel-input"
          disabled={isLoading}
          required
          autoComplete="off"
          spellCheck={false}
        />
        <div
          style={{
            fontSize: '0.7rem',
            color: 'var(--text-faint)',
            fontFamily: 'var(--font-mono)',
            marginTop: '0.375rem',
            letterSpacing: '0.03em',
          }}
        >
          Enter the company name, individual, or entity to investigate
        </div>
      </div>

      {/* ── Country Filter ─────────────────────────────────── */}
      <div>
        <label
          htmlFor="country"
          className="label-stamp"
          style={{ display: 'block', marginBottom: '0.5rem' }}
        >
          Country Filter{' '}
          <span style={{ color: 'var(--text-faint)' }}>(optional)</span>
        </label>
        <select
          id="country"
          value={country}
          onChange={(e) => setCountry(e.target.value)}
          className="intel-select"
          disabled={isLoading}
        >
          <option value="">— All jurisdictions</option>
          {COUNTRIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* ── Fuzzy Threshold ────────────────────────────────── */}
      <div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '0.5rem',
          }}
        >
          <label
            htmlFor="fuzzy-threshold"
            className="label-stamp"
            style={{ display: 'block' }}
          >
            Name Match Sensitivity
          </label>
          <span
            className="font-data"
            style={{
              fontSize: '0.9rem',
              color: 'var(--amber-light)',
              minWidth: '3ch',
              textAlign: 'right',
            }}
          >
            {fuzzyThreshold}
            <span style={{ fontSize: '0.65rem', color: 'var(--amber-primary)', marginLeft: '1px' }}>%</span>
          </span>
        </div>
        <input
          id="fuzzy-threshold"
          type="range"
          min="0"
          max="100"
          step="5"
          value={fuzzyThreshold}
          onChange={(e) => setFuzzyThreshold(parseInt(e.target.value))}
          className="amber-range"
          disabled={isLoading}
        />
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.62rem',
            color: 'var(--text-faint)',
            letterSpacing: '0.08em',
            marginTop: '0.25rem',
          }}
        >
          <span>Loose (0%)</span>
          <span>Recommended: 70–90%</span>
          <span>Exact (100%)</span>
        </div>
        <p
          style={{
            marginTop: '0.375rem',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.68rem',
            color: 'var(--text-muted)',
            lineHeight: 1.55,
          }}
        >
          {fuzzyThreshold < 60
            ? <span style={{ color: 'var(--risk-mid-bright)' }}>⚠ Low threshold — expect many false positives from partial name matches.</span>
            : fuzzyThreshold > 95
            ? <span style={{ color: 'var(--risk-mid-bright)' }}>⚠ High threshold — may miss genuine hits with transliterated or abbreviated names.</span>
            : <span>Matches names within {100 - fuzzyThreshold}% character variation. Handles common transliterations and abbreviations.</span>
          }
        </p>
      </div>

      {/* ── Submit ─────────────────────────────────────────── */}
      <div>
        <button
          type="submit"
          disabled={isLoading || !entityName.trim()}
          className="btn-primary"
          style={{ fontSize: '0.75rem' }}
        >
          {isLoading ? (
            <>
              <div
                style={{
                  width: '14px',
                  height: '14px',
                  border: '1.5px solid var(--bg-void)',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 0.8s linear infinite',
                  flexShrink: 0,
                }}
              />
              <span>
                Query Active — {tier.toUpperCase()} TIER — Est. {getEstimatedDuration()}
              </span>
            </>
          ) : (
            <>
              <svg
                width="14"
                height="14"
                viewBox="0 0 20 20"
                fill="currentColor"
                style={{ flexShrink: 0 }}
              >
                <path
                  fillRule="evenodd"
                  d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                  clipRule="evenodd"
                />
              </svg>
              <span>
                Initiate {tier.charAt(0).toUpperCase() + tier.slice(1)} Tier Research
              </span>
              <span
                style={{
                  marginLeft: 'auto',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.62rem',
                  opacity: 0.7,
                  letterSpacing: '0.1em',
                }}
              >
                Est. {getEstimatedDuration()}
              </span>
            </>
          )}
        </button>

        {/* Active query notice */}
        {isLoading && (
          <div
            style={{
              marginTop: '1rem',
              padding: '0.875rem 1rem',
              background: 'var(--bg-panel)',
              border: '1px solid var(--border-main)',
              borderLeft: '2px solid var(--amber-primary)',
              display: 'flex',
              gap: '0.75rem',
              alignItems: 'flex-start',
            }}
          >
            <div
              style={{
                width: '6px',
                height: '6px',
                background: 'var(--amber-main)',
                flexShrink: 0,
                marginTop: '0.35rem',
                animation: 'data-pulse 1.5s ease-in-out infinite',
                boxShadow: '0 0 6px var(--amber-primary)',
              }}
            />
            <p
              style={{
                margin: 0,
                fontSize: '0.75rem',
                color: 'var(--text-secondary)',
                fontFamily: 'var(--font-mono)',
                lineHeight: 1.6,
                letterSpacing: '0.02em',
              }}
            >
              <span style={{ color: 'var(--amber-light)', fontWeight: 600 }}>
                {tier.toUpperCase()} TIER:
              </span>{' '}
              {tierDescriptions[tier]}
            </p>
          </div>
        )}
      </div>
    </form>
  );
}
