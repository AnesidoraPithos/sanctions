/**
 * TierBadge Component
 *
 * Displays research tier (BASE/NETWORK/DEEP).
 */

import { ResearchTier } from '@/lib/types';

interface TierBadgeProps {
  tier: ResearchTier;
  size?: 'sm' | 'md';
}

const tierConfig: Record<ResearchTier, { color: string; label: string }> = {
  base: { color: 'bg-blue-600', label: 'BASE' },
  network: { color: 'bg-purple-600', label: 'NETWORK' },
  deep: { color: 'bg-indigo-600', label: 'DEEP' },
};

const sizeClasses = {
  sm: 'text-sm px-2 py-0.5',
  md: 'text-sm px-3 py-1',
};

export default function TierBadge({ tier, size = 'md' }: TierBadgeProps) {
  const config = tierConfig[tier];

  return (
    <span
      className={`${config.color} ${sizeClasses[size]} text-white font-mono font-bold rounded uppercase inline-block`}
    >
      {config.label}
    </span>
  );
}
