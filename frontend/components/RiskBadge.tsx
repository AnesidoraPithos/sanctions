/**
 * RiskBadge Component
 *
 * Displays risk level with appropriate color coding and optional explanation.
 */

'use client';

import { useState } from 'react';
import { RiskLevel, RiskExplanation } from '@/lib/types';

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
  sm: 'text-xs px-2 py-1',
  md: 'text-sm px-3 py-1.5',
  lg: 'text-base px-4 py-2',
};

export default function RiskBadge({ level, size = 'md', explanation }: RiskBadgeProps) {
  const [showExplanation, setShowExplanation] = useState(false);
  const config = riskConfig[level];

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
                          <div className="flex justify-between text-xs text-gray-600 mb-1">
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
                          <div className="flex justify-between text-xs text-gray-500 mt-1">
                            <span>Low (0-35)</span>
                            <span>Medium (36-65)</span>
                            <span>High (66-100)</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Scoring Breakdown */}
                    {explanation.intelligence_breakdown && (
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-1">
                          Scoring Breakdown:
                        </label>
                        <p className="text-gray-900 font-mono text-sm bg-gray-50 p-3 rounded border border-gray-200">
                          {explanation.intelligence_breakdown}
                        </p>
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

                  {/* Footer */}
                  <div className="mt-6 pt-4 border-t border-gray-200">
                    <p className="text-xs text-gray-500">
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
