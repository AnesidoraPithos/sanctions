"use client";

import React, { useState } from "react";
import { ResearchTier, TierSelectorProps } from "@/lib/types";

/**
 * TierSelector Component
 *
 * Allows users to select research tier (base/network/deep) and configure
 * tier-specific parameters (network depth, ownership threshold, etc.)
 */

interface TierOption {
  tier: ResearchTier;
  label: string;
  duration: string;
  features: string[];
  disabled: boolean;
}

const TIER_OPTIONS: TierOption[] = [
  {
    tier: "base",
    label: "Base Tier",
    duration: "30-60 seconds",
    features: [
      "Sanctions screening (10+ databases)",
      "OSINT media intelligence",
      "Risk scoring",
      "AI-powered intelligence report",
    ],
    disabled: false,
  },
  {
    tier: "network",
    label: "Network Tier",
    duration: "2-10 minutes",
    features: [
      "All base tier features",
      "Conglomerate discovery (multi-source)",
      "Directors & shareholders extraction",
      "Cross-entity sanctions screening",
      "Interactive network graph visualization",
    ],
    disabled: false,
  },
  {
    tier: "deep",
    label: "Deep Tier",
    duration: "5-15 minutes",
    features: [
      "All network tier features",
      "Financial flow analysis (USAspending + transactions)",
      "Federal procurement records",
      "Enhanced AI intelligence report",
      "Advanced risk scoring",
    ],
    disabled: false,
  },
];

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
    <div className="space-y-6">
      {/* Tier Selection Cards */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-3">
          Research Tier
        </label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {TIER_OPTIONS.map((option) => (
            <button
              key={option.tier}
              type="button"
              disabled={option.disabled}
              onClick={() => !option.disabled && onTierChange(option.tier)}
              className={`
                relative p-4 rounded-lg border-2 text-left transition-all
                ${
                  selectedTier === option.tier
                    ? "border-blue-500 bg-blue-950/30"
                    : "border-gray-700 bg-gray-900/50 hover:border-gray-600"
                }
                ${option.disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
              `}
            >
              {/* Tier Label */}
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-white">
                  {option.label}
                </span>
                {option.disabled && (
                  <span className="text-sm text-gray-500 bg-gray-800 px-2 py-1 rounded">
                    Phase 3
                  </span>
                )}
              </div>

              {/* Duration */}
              <div className="text-sm text-gray-400 mb-3">{option.duration}</div>

              {/* Features */}
              <ul className="space-y-1">
                {option.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start text-sm text-gray-400">
                    <span className="text-blue-400 mr-2">•</span>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              {/* Selected Indicator */}
              {selectedTier === option.tier && (
                <div className="absolute top-2 right-2">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Network Tier Configuration */}
      {selectedTier === "network" && (
        <div className="space-y-4 p-4 bg-gray-900/50 border border-gray-700 rounded-lg">
          <div className="text-sm font-medium text-gray-300 mb-3">
            Network Tier Configuration
          </div>

          {/* Search Depth Slider */}
          <div>
            <label
              htmlFor="network-depth"
              className="block text-sm text-gray-400 mb-2"
            >
              Search Depth: <span className="text-blue-400 font-semibold">{networkDepth}</span>{" "}
              {networkDepth === 1 ? "level" : "levels"}
            </label>
            <input
              id="network-depth"
              type="range"
              min="1"
              max="3"
              step="1"
              value={networkDepth}
              onChange={(e) =>
                onNetworkDepthChange?.(parseInt(e.target.value))
              }
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
            <div className="flex justify-between text-sm text-gray-500 mt-1">
              <span>Level 1 (fastest)</span>
              <span>Level 2</span>
              <span>Level 3 (most comprehensive)</span>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Higher depth discovers more subsidiaries but takes longer
            </p>
          </div>

          {/* Ownership Threshold Slider */}
          <div>
            <label
              htmlFor="ownership-threshold"
              className="block text-sm text-gray-400 mb-2"
            >
              Ownership Threshold:{" "}
              <span className="text-blue-400 font-semibold">{ownershipThreshold}%</span>
            </label>
            <input
              id="ownership-threshold"
              type="range"
              min="0"
              max="100"
              step="10"
              value={ownershipThreshold}
              onChange={(e) =>
                onOwnershipThresholdChange?.(parseInt(e.target.value))
              }
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
            <div className="flex justify-between text-sm text-gray-500 mt-1">
              <span>0% (all)</span>
              <span>50%</span>
              <span>100% (wholly-owned)</span>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              Minimum ownership percentage to include subsidiaries
            </p>
          </div>

          {/* Include Sisters Checkbox */}
          <div className="flex items-start space-x-3">
            <input
              id="include-sisters"
              type="checkbox"
              checked={includeSisters}
              onChange={(e) =>
                onIncludeSistersChange?.(e.target.checked)
              }
              className="mt-1 h-4 w-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-offset-gray-900"
            />
            <div>
              <label
                htmlFor="include-sisters"
                className="text-sm text-gray-400 cursor-pointer"
              >
                Include sister companies
              </label>
              <p className="text-sm text-gray-500 mt-1">
                Include entities with the same parent company
              </p>
            </div>
          </div>

          {/* Max Level 2 Searches Slider */}
          {networkDepth >= 2 && (
            <div>
              <label
                htmlFor="max-level-2"
                className="block text-sm text-gray-400 mb-2"
              >
                Max Level 2 Searches:{" "}
                <span className="text-blue-400 font-semibold">{maxLevel2Searches}</span>
              </label>
              <input
                id="max-level-2"
                type="range"
                min="5"
                max="50"
                step="5"
                value={maxLevel2Searches}
                onChange={(e) =>
                  onMaxLevel2SearchesChange?.(parseInt(e.target.value))
                }
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>5 (fastest)</span>
                <span>25 (balanced)</span>
                <span>50 (comprehensive)</span>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                To prevent timeouts, only the top N subsidiaries by ownership % will be searched for level 2.
                <span className="text-yellow-400"> Higher values may timeout for large companies.</span>
              </p>
            </div>
          )}

          {/* Max Level 3 Searches Slider */}
          {networkDepth >= 3 && (
            <div>
              <label
                htmlFor="max-level-3"
                className="block text-sm text-gray-400 mb-2"
              >
                Max Level 3 Searches:{" "}
                <span className="text-blue-400 font-semibold">{maxLevel3Searches}</span>
              </label>
              <input
                id="max-level-3"
                type="range"
                min="5"
                max="30"
                step="5"
                value={maxLevel3Searches}
                onChange={(e) =>
                  onMaxLevel3SearchesChange?.(parseInt(e.target.value))
                }
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>5 (fastest)</span>
                <span>15 (balanced)</span>
                <span>30 (comprehensive)</span>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                To prevent timeouts, only the top N level 2 subsidiaries will be searched for level 3.
                <span className="text-yellow-400"> Higher values significantly increase search time.</span>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Deep Tier Configuration */}
      {selectedTier === "deep" && (
        <div className="space-y-4 p-4 bg-gray-900/50 border border-gray-700 rounded-lg">
          <div className="text-sm font-medium text-gray-300 mb-3">
            Deep Tier Configuration
          </div>

          {/* Reuse network depth slider */}
          <div>
            <label
              htmlFor="deep-network-depth"
              className="block text-sm text-gray-400 mb-2"
            >
              Search Depth:{" "}
              <span className="text-blue-400 font-semibold">{networkDepth}</span>{" "}
              {networkDepth === 1 ? "level" : "levels"}
            </label>
            <input
              id="deep-network-depth"
              type="range"
              min="1"
              max="3"
              step="1"
              value={networkDepth}
              onChange={(e) => onNetworkDepthChange?.(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
            <div className="flex justify-between text-sm text-gray-500 mt-1">
              <span>Level 1 (fastest)</span>
              <span>Level 2</span>
              <span>Level 3 (most comprehensive)</span>
            </div>
          </div>

          {/* Include Financial Flows toggle */}
          <div className="flex items-start space-x-3">
            <input
              id="include-financial-flows"
              type="checkbox"
              checked={includeFinancialFlows}
              onChange={(e) => onIncludeFinancialFlowsChange?.(e.target.checked)}
              className="mt-1 h-4 w-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500 focus:ring-offset-gray-900"
            />
            <div>
              <label
                htmlFor="include-financial-flows"
                className="text-sm text-gray-400 cursor-pointer"
              >
                Include financial flows
              </label>
              <p className="text-sm text-gray-500 mt-1">
                Analyse federal procurement records (USAspending.gov) and related-party transactions
              </p>
            </div>
          </div>

          {/* Phase 4 toggles */}
          <div className="border-t border-gray-700/50 pt-4 mt-4">
            <p className="text-sm font-medium text-gray-400 mb-3">
              Phase 4 — Advanced Intelligence
            </p>

            <div className="space-y-3">
              {/* Director pivot */}
              <div className="flex items-start space-x-3">
                <input
                  id="include-director-pivot"
                  type="checkbox"
                  checked={includeDirectorPivot}
                  onChange={(e) => onIncludeDirectorPivotChange?.(e.target.checked)}
                  className="mt-1 h-4 w-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500 focus:ring-offset-gray-900"
                />
                <div>
                  <label htmlFor="include-director-pivot" className="text-sm text-gray-400 cursor-pointer">
                    Include director pivoting
                  </label>
                  <p className="text-sm text-gray-500 mt-0.5">
                    Discover interlocking directorates via SEC EDGAR full-text search
                  </p>
                </div>
              </div>

              {/* Infrastructure correlation */}
              <div className="flex items-start space-x-3">
                <input
                  id="include-infrastructure"
                  type="checkbox"
                  checked={includeInfrastructure}
                  onChange={(e) => onIncludeInfrastructureChange?.(e.target.checked)}
                  className="mt-1 h-4 w-4 text-cyan-600 bg-gray-700 border-gray-600 rounded focus:ring-cyan-500 focus:ring-offset-gray-900"
                />
                <div>
                  <label htmlFor="include-infrastructure" className="text-sm text-gray-400 cursor-pointer">
                    Include infrastructure correlation
                  </label>
                  <p className="text-sm text-gray-500 mt-0.5">
                    WHOIS lookups on media-extracted domains; detect shared registrants
                  </p>
                </div>
              </div>

              {/* Beneficial ownership */}
              <div className="flex items-start space-x-3">
                <input
                  id="include-beneficial-ownership"
                  type="checkbox"
                  checked={includeBeneficialOwnership}
                  onChange={(e) => onIncludeBeneficialOwnershipChange?.(e.target.checked)}
                  className="mt-1 h-4 w-4 text-emerald-600 bg-gray-700 border-gray-600 rounded focus:ring-emerald-500 focus:ring-offset-gray-900"
                />
                <div>
                  <label htmlFor="include-beneficial-ownership" className="text-sm text-gray-400 cursor-pointer">
                    Include beneficial ownership lookup
                  </label>
                  <p className="text-sm text-gray-500 mt-0.5">
                    Trace UBOs via OCCRP Aleph and Open Ownership Register
                  </p>
                </div>
              </div>
            </div>
          </div>

          <p className="text-sm text-yellow-400/80">
            Deep Tier runs all Network Tier steps plus financial flow analysis. Expect 5–15 minutes for large companies.
          </p>
        </div>
      )}
    </div>
  );
}
