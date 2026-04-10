'use client';

import React from 'react';
import { ResearchTier, TierSelectorProps } from '@/lib/types';

interface TierOption {
  tier: ResearchTier;
  label: string;
  duration: string;
  features: string[];
  disabled: boolean;
}

const TIER_OPTIONS: TierOption[] = [
  {
    tier: 'base',
    label: 'Base',
    duration: '30–60s',
    features: [
      'Sanctions screening (10+ DBs)',
      'OSINT media intelligence',
      'Risk scoring',
      'AI intelligence report',
    ],
    disabled: false,
  },
  {
    tier: 'network',
    label: 'Network',
    duration: '2–10 min',
    features: [
      'All base features',
      'Conglomerate discovery',
      'Directors & shareholders',
      'Cross-entity sanctions',
      'Network graph visualization',
    ],
    disabled: false,
  },
  {
    tier: 'deep',
    label: 'Deep',
    duration: '5–15 min',
    features: [
      'All network features',
      'Financial flow analysis',
      'Federal procurement records',
      'Director pivot analysis',
      'Beneficial ownership tracing',
    ],
    disabled: false,
  },
];

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="label-stamp"
      style={{ display: 'block', marginBottom: '0.5rem' }}
    >
      {children}
    </div>
  );
}

function ConfigSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        marginTop: '1.25rem',
        padding: '1.25rem',
        background: 'var(--bg-panel)',
        border: '1px solid var(--border-dim)',
        borderLeft: '2px solid var(--amber-deep)',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
      }}
    >
      <div className="label-stamp-bright" style={{ fontSize: '0.75rem' }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function SliderField({
  id,
  label,
  value,
  min,
  max,
  step,
  onChange,
  leftLabel,
  rightLabel,
  note,
  noteHighlight,
}: {
  id: string;
  label: React.ReactNode;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
  leftLabel: string;
  rightLabel: string;
  note?: string;
  noteHighlight?: string;
}) {
  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.5rem',
        }}
      >
        <label htmlFor={id} className="label-stamp">
          {label}
        </label>
        <span
          className="font-data"
          style={{ fontSize: '0.85rem', color: 'var(--amber-light)' }}
        >
          {value}
          {typeof value === 'number' && id.includes('threshold') ? '%' : ''}
        </span>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="amber-range"
      />
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          marginTop: '0.25rem',
          letterSpacing: '0.05em',
        }}
      >
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
      {note && (
        <p
          style={{
            marginTop: '0.375rem',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            lineHeight: 1.5,
          }}
        >
          {note}
          {noteHighlight && (
            <span style={{ color: 'var(--risk-mid-bright)' }}> {noteHighlight}</span>
          )}
        </p>
      )}
    </div>
  );
}

function ToggleField({
  id,
  checked,
  onChange,
  label,
  description,
}: {
  id: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  description: string;
}) {
  return (
    <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="amber-check"
      />
      <div>
        <label
          htmlFor={id}
          style={{
            fontSize: '0.8rem',
            color: 'var(--text-main)',
            fontFamily: 'var(--font-mono)',
            cursor: 'pointer',
            letterSpacing: '0.02em',
          }}
        >
          {label}
        </label>
        <p
          style={{
            margin: '0.2rem 0 0',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            fontFamily: 'var(--font-mono)',
            lineHeight: 1.5,
          }}
        >
          {description}
        </p>
      </div>
    </div>
  );
}

export default function TierSelector({
  selectedTier,
  onTierChange,
  networkDepth = 1,
  onNetworkDepthChange,
  ownershipThreshold = 0,
  onOwnershipThresholdChange,
  includeSisters = true,
  onIncludeSistersChange,
  maxLevel2Searches = 20,
  onMaxLevel2SearchesChange,
  maxLevel3Searches = 10,
  onMaxLevel3SearchesChange,
  includeFinancialFlows = true,
  onIncludeFinancialFlowsChange,
  includeDirectorPivot = true,
  onIncludeDirectorPivotChange,
  includeInfrastructure = true,
  onIncludeInfrastructureChange,
  includeBeneficialOwnership = true,
  onIncludeBeneficialOwnershipChange,
}: TierSelectorProps) {
  return (
    <div>
      <FieldLabel>Research Tier</FieldLabel>

      {/* Tier cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '1px',
          background: 'var(--border-void)',
        }}
      >
        {TIER_OPTIONS.map((option, idx) => {
          const isActive = selectedTier === option.tier;
          return (
            <button
              key={option.tier}
              type="button"
              disabled={option.disabled}
              onClick={() => !option.disabled && onTierChange(option.tier)}
              className={`tier-card ${isActive ? 'tier-card-active bracket-corners bracket-corners-active' : 'bracket-corners'}`}
              style={{
                position: 'relative',
                opacity: option.disabled ? 0.4 : 1,
                cursor: option.disabled ? 'not-allowed' : 'pointer',
              }}
            >
              {/* Tier number */}
              <div
                className="font-data"
                style={{
                  fontSize: '0.75rem',
                  color: isActive ? 'var(--amber-primary)' : 'var(--text-muted)',
                  letterSpacing: '0.12em',
                  marginBottom: '0.4rem',
                }}
              >
                [{String(idx + 1).padStart(2, '0')}]
              </div>

              {/* Label + duration */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  justifyContent: 'space-between',
                  marginBottom: '0.75rem',
                  flexWrap: 'wrap',
                  gap: '0.25rem',
                }}
              >
                <span
                  className="font-display"
                  style={{
                    fontSize: '1.15rem',
                    color: isActive ? 'var(--amber-light)' : 'var(--text-bright)',
                    letterSpacing: '0.08em',
                  }}
                >
                  {option.label}
                </span>
                <span
                  className="font-data"
                  style={{
                    fontSize: '0.75rem',
                    color: isActive ? 'var(--amber-primary)' : 'var(--text-muted)',
                  }}
                >
                  {option.duration}
                </span>
              </div>

              {/* Feature list */}
              <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                {option.features.map((feature, fIdx) => (
                  <li
                    key={fIdx}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.4rem',
                      fontSize: '0.75rem',
                      color: isActive ? 'var(--text-main)' : 'var(--text-muted)',
                      fontFamily: 'var(--font-mono)',
                      lineHeight: 1.4,
                    }}
                  >
                    <span style={{ color: isActive ? 'var(--amber-primary)' : 'var(--text-muted)', flexShrink: 0 }}>
                      {isActive ? '▸' : '·'}
                    </span>
                    {feature}
                  </li>
                ))}
              </ul>

              {/* Active indicator bar */}
              {isActive && (
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '2px',
                    background: 'var(--amber-primary)',
                    boxShadow: '0 0 8px var(--amber-primary)',
                  }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* ── Network Config ──────────────────────────────────────── */}
      {selectedTier === 'network' && (
        <ConfigSection title="Network Tier Configuration">
          <SliderField
            id="network-depth"
            label="Search Depth"
            value={networkDepth}
            min={1}
            max={3}
            step={1}
            onChange={(v) => onNetworkDepthChange?.(v)}
            leftLabel="Level 1 — fastest"
            rightLabel="Level 3 — comprehensive"
          />
          <SliderField
            id="ownership-threshold"
            label="Ownership Threshold"
            value={ownershipThreshold}
            min={0}
            max={100}
            step={10}
            onChange={(v) => onOwnershipThresholdChange?.(v)}
            leftLabel="0% (all)"
            rightLabel="100% (wholly-owned)"
            note="Minimum ownership % to include subsidiaries"
          />
          <ToggleField
            id="include-sisters"
            checked={includeSisters}
            onChange={(v) => onIncludeSistersChange?.(v)}
            label="Include sister companies"
            description="Entities sharing the same parent company"
          />
          {networkDepth >= 2 && (
            <SliderField
              id="max-level-2"
              label="Max Level 2 Searches"
              value={maxLevel2Searches}
              min={5}
              max={50}
              step={5}
              onChange={(v) => onMaxLevel2SearchesChange?.(v)}
              leftLabel="5 — fast"
              rightLabel="50 — comprehensive"
              note="Top N subsidiaries searched by ownership %. Higher values may timeout."
              noteHighlight="Caution with large conglomerates."
            />
          )}
          {networkDepth >= 3 && (
            <SliderField
              id="max-level-3"
              label="Max Level 3 Searches"
              value={maxLevel3Searches}
              min={5}
              max={30}
              step={5}
              onChange={(v) => onMaxLevel3SearchesChange?.(v)}
              leftLabel="5 — fast"
              rightLabel="30 — comprehensive"
              note="Significantly increases search time at depth 3."
              noteHighlight="Plan for extended duration."
            />
          )}
        </ConfigSection>
      )}

      {/* ── Deep Config ─────────────────────────────────────────── */}
      {selectedTier === 'deep' && (
        <ConfigSection title="Deep Tier Configuration">
          <SliderField
            id="deep-network-depth"
            label="Network Search Depth"
            value={networkDepth}
            min={1}
            max={3}
            step={1}
            onChange={(v) => onNetworkDepthChange?.(v)}
            leftLabel="Level 1 — fastest"
            rightLabel="Level 3 — comprehensive"
          />
          <ToggleField
            id="include-financial-flows"
            checked={includeFinancialFlows}
            onChange={(v) => onIncludeFinancialFlowsChange?.(v)}
            label="Financial flow analysis"
            description="USAspending.gov federal procurement records and related-party transactions"
          />
          <div>
            <div className="label-stamp-bright" style={{ fontSize: '0.75rem', marginBottom: '0.75rem', paddingTop: '0.25rem' }}>
              Phase 4 — Advanced Intelligence Modules
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
              <ToggleField
                id="include-director-pivot"
                checked={includeDirectorPivot}
                onChange={(v) => onIncludeDirectorPivotChange?.(v)}
                label="Director pivot analysis"
                description="Interlocking directorates via SEC EDGAR full-text search"
              />
              <ToggleField
                id="include-infrastructure"
                checked={includeInfrastructure}
                onChange={(v) => onIncludeInfrastructureChange?.(v)}
                label="Infrastructure correlation"
                description="WHOIS lookups on media-extracted domains, shared registrant detection"
              />
              <ToggleField
                id="include-beneficial-ownership"
                checked={includeBeneficialOwnership}
                onChange={(v) => onIncludeBeneficialOwnershipChange?.(v)}
                label="Beneficial ownership tracing"
                description="UBO identification via OCCRP Aleph and Open Ownership Register"
              />
            </div>
          </div>
          <div
            style={{
              padding: '0.625rem 0.875rem',
              background: 'var(--risk-mid-bg)',
              border: '1px solid var(--risk-mid)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--risk-mid-bright)',
              lineHeight: 1.5,
            }}
          >
            ⚠ Deep Tier runs all Network Tier steps plus advanced intelligence modules.
            Expect 5–15 minutes for large conglomerates.
          </div>
        </ConfigSection>
      )}
    </div>
  );
}
