/**
 * RiskBadge Component
 *
 * Displays risk level with appropriate color coding.
 */

import { RiskLevel } from '@/lib/types';

interface RiskBadgeProps {
  level: RiskLevel;
  size?: 'sm' | 'md' | 'lg';
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

export default function RiskBadge({ level, size = 'md' }: RiskBadgeProps) {
  const config = riskConfig[level];

  return (
    <span
      className={`${config.color} ${sizeClasses[size]} text-white font-semibold rounded-md inline-block`}
    >
      {config.label}
    </span>
  );
}
