/**
 * RiskBadge Component
 *
 * Displays risk level with appropriate color coding and optional explanation.
 */

'use client';

import { useState, useMemo } from 'react';
import { RiskLevel, RiskExplanation } from '@/lib/types';

const SCORING_METHODOLOGY = [
  {
    title: 'Regulatory & Legal Indicators',
    range: '0–50 pts',
    note: 'Highest applicable item only',
    items: [
      { label: 'Active sanctions listings', pts: 50 },
      { label: 'Criminal investigations/charges', pts: 40 },
      { label: 'Civil enforcement actions', pts: 30 },
      { label: 'Regulatory violations/fines', pts: 25 },
      { label: 'Pending investigations', pts: 15 },
      { label: 'Past resolved issues (>3 years)', pts: 5 },
    ],
  },
  {
    title: 'Media Signal Strength',
    range: '0–20 pts',
    note: 'Additive up to category max',
    items: [
      { label: 'Official gov sources (treasury.gov, justice.gov, state.gov)', pts: 10, suffix: 'each, max 20' },
      { label: 'Major credible news (Reuters, Bloomberg, WSJ, AP)', pts: 3, suffix: 'each, max 15' },
      { label: 'General media/blogs', pts: 1, suffix: 'each, max 5' },
    ],
  },
  {
    title: 'Severity Factors',
    range: '0–30 pts',
    note: 'Highest applicable item only',
    items: [
      { label: 'National security concerns', pts: 30 },
      { label: 'Financial crimes (money laundering, fraud)', pts: 15 },
      { label: 'Export control violations', pts: 15 },
      { label: 'Corruption/bribery', pts: 12 },
      { label: 'Environmental/labor violations', pts: 8 },
      { label: 'Civil disputes', pts: 5 },
    ],
  },
  {
    title: 'Temporal Relevance',
    range: '0–10 pts',
    note: 'Highest applicable item only',
    items: [
      { label: 'Issues within last 6 months', pts: 10 },
      { label: 'Issues within last 1 year', pts: 8 },
      { label: 'Issues within last 3 years', pts: 5 },
      { label: 'Older than 3 years', pts: 2 },
    ],
  },
];

interface RiskBadgeProps {
  level: RiskLevel;
  size?: 'sm' | 'md' | 'lg';
  explanation?: RiskExplanation;
}

const riskConfig: Record<RiskLevel, { color: string; label: string }> = {
  SAFE: { color: 'bg-green-500', label: 'Safe' },
  LOW: { color: 'bg-blue-500', label: 'Low Risk' },
  MID: { color: 'bg-yellow-500', label: 'Medium Risk' },
  HIGH: { color: 'bg-orange-500', label: 'High Risk' },
  VERY_HIGH: { color: 'bg-red-500', label: 'Very High Risk' },
};

const sizeClasses = {
  sm: 'text-sm px-2 py-1',
  md: 'text-sm px-3 py-1.5',
  lg: 'text-base px-4 py-2',
};

const RAW_SCORE_RE = /RAW:\s*(\d+)\s*→\s*SCORE:\s*(\d+)/;

function parseBreakdown(breakdown: string) {
  const rawScoreMatch = breakdown.match(RAW_SCORE_RE);
  const rawTotal = rawScoreMatch ? rawScoreMatch[1] : null;
  const cappedTotal = rawScoreMatch ? rawScoreMatch[2] : null;
  const wasCapped = rawTotal && cappedTotal && rawTotal !== cappedTotal;

  const segments = breakdown
    .replace(/\s*\|\s*RAW:.*$/, '')
    .split(' | ')
    .filter(Boolean);

  const rows = segments.map(seg => {
    const colonIdx = seg.indexOf(':');
    if (colonIdx === -1) return { category: seg.trim(), detail: '' };
    return {
      category: seg.slice(0, colonIdx).trim(),
      detail: seg.slice(colonIdx + 1).trim(),
    };
  });

  return { rows, rawTotal, cappedTotal, wasCapped };
}

export default function RiskBadge({ level, size = 'md', explanation }: RiskBadgeProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const [showMethodology, setShowMethodology] = useState(false);
  const config = riskConfig[level];
  const parsedBreakdown = useMemo(
    () => explanation?.intelligence_breakdown ? parseBreakdown(explanation.intelligence_breakdown) : null,
    [explanation?.intelligence_breakdown],
  );

  return (
    <div className="flex items-center gap-2 relative">
      {/* Risk Badge */}
      <span
        className={`${config.color} ${sizeClasses[size]} text-white font-semibold rounded-md inline-block`}
      >
        {config.label}
      </span>

      {/* Info Button (only show if explanation exists) */}
      {explanation && (
        <>
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="w-6 h-6 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-gray-700 font-bold text-sm transition-colors"
            title="How was this risk level determined?"
            aria-label="Show risk explanation"
          >
            ?
          </button>

          {/* Explanation Modal */}
          {showExplanation && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 bg-black bg-opacity-50 z-40"
                onClick={() => setShowExplanation(false)}
              />

              {/* Modal */}
              <div className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-xl z-50 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
                <div className="p-6">
                  {/* Header */}
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-bold text-gray-900">
                      Risk Assessment Breakdown
                    </h3>
                    <button
                      onClick={() => setShowExplanation(false)}
                      className="text-gray-400 hover:text-gray-600"
                      aria-label="Close modal"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>

                  {/* Content */}
                  <div className="space-y-4">
                    {/* Sanctions Signal */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Sanctions Screening:
                      </label>
                      <p className="text-gray-900">{explanation.sanctions_signal}</p>
                    </div>

                    {/* Intelligence Analysis */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Intelligence Analysis:
                      </label>
                      <p className="text-gray-900 mb-2">{explanation.intelligence_signal}</p>

                      {/* Score Bar (if score available) */}
                      {explanation.intelligence_score !== null && (
                        <div className="mt-2">
                          <div className="flex justify-between text-sm text-gray-600 mb-1">
                            <span>Intelligence Score</span>
                            <span>{explanation.intelligence_score}/100</span>
                          </div>
                          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all ${
                                explanation.intelligence_score >= 66
                                  ? 'bg-red-500'
                                  : explanation.intelligence_score >= 36
                                  ? 'bg-yellow-500'
                                  : 'bg-blue-500'
                              }`}
                              style={{ width: `${explanation.intelligence_score}%` }}
                            />
                          </div>
                          <div className="flex justify-between text-sm text-gray-500 mt-1">
                            <span>Low (0-35)</span>
                            <span>Medium (36-65)</span>
                            <span>High (66-100)</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Scoring Breakdown */}
                    {parsedBreakdown && (
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Scoring Breakdown:
                        </label>
                        <div className="bg-gray-50 rounded border border-gray-200 divide-y divide-gray-100">
                          {parsedBreakdown.rows.map((row, i) => (
                            <div key={i} className="px-3 py-2 flex items-start justify-between gap-4">
                              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">
                                {row.category}
                              </span>
                              <span className="text-sm text-gray-800 font-mono text-right">
                                {row.detail}
                              </span>
                            </div>
                          ))}
                          {parsedBreakdown.rawTotal && (
                            <div className="px-3 py-2 bg-gray-100 flex justify-between font-bold text-gray-900 text-sm">
                              <span>{parsedBreakdown.wasCapped ? `Raw: ${parsedBreakdown.rawTotal} → Capped` : 'Total Score'}</span>
                              <span>{parsedBreakdown.cappedTotal}/100</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Final Reasoning */}
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1">
                        Final Assessment:
                      </label>
                      <p className="text-gray-900">{explanation.final_reasoning}</p>
                    </div>
                  </div>

                  {/* Scoring Methodology */}
                  <div className="mt-6 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => setShowMethodology(!showMethodology)}
                      className="flex items-center justify-between w-full text-sm font-semibold text-gray-600 hover:text-gray-900 transition-colors"
                    >
                      <span>Scoring Methodology</span>
                      <svg
                        className={`w-4 h-4 transition-transform ${showMethodology ? 'rotate-180' : ''}`}
                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {showMethodology && (
                      <div className="mt-3 space-y-4">
                        <p className="text-xs text-gray-500">
                          Total score is capped at 100. If the raw sum of all categories exceeds 100, the displayed score is capped at 100.
                        </p>
                        {SCORING_METHODOLOGY.map(category => (
                          <div key={category.title} className="bg-gray-50 rounded border border-gray-200">
                            <div className="px-3 py-2 bg-gray-100 rounded-t border-b border-gray-200 flex items-center justify-between">
                              <span className="text-xs font-bold text-gray-800 uppercase tracking-wide">
                                {category.title}
                              </span>
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-semibold text-indigo-600">{category.range}</span>
                                <span className="text-xs text-gray-500 italic">{category.note}</span>
                              </div>
                            </div>
                            <div className="divide-y divide-gray-100">
                              {category.items.map(item => (
                                <div key={item.label} className="px-3 py-1.5 flex items-center justify-between gap-4">
                                  <span className="text-xs text-gray-700">{item.label}</span>
                                  <span className="text-xs font-mono font-semibold text-gray-900 whitespace-nowrap">
                                    {item.pts} pts{'suffix' in item ? ` (${item.suffix})` : ''}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}

                        <div className="bg-gray-50 rounded border border-gray-200 divide-y divide-gray-100">
                          {[
                            { label: 'Low', range: '0–35', color: 'bg-blue-500' },
                            { label: 'Medium', range: '36–65', color: 'bg-yellow-500' },
                            { label: 'High', range: '66–100', color: 'bg-red-500' },
                          ].map(tier => (
                            <div key={tier.label} className="px-3 py-1.5 flex items-center gap-3">
                              <span className={`w-2 h-2 rounded-full ${tier.color} flex-shrink-0`} />
                              <span className="text-xs font-semibold text-gray-800">{tier.label}</span>
                              <span className="text-xs text-gray-500">{tier.range} points</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Footer */}
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <p className="text-sm text-gray-500">
                      This risk assessment combines sanctions screening results with AI-generated
                      intelligence analysis for a comprehensive evaluation.
                    </p>
                  </div>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
