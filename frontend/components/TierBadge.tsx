import { ResearchTier } from '@/lib/types';

interface TierBadgeProps {
  tier: ResearchTier;
  size?: 'sm' | 'md';
}

const tierConfig: Record<ResearchTier, { color: string; borderColor: string; label: string }> = {
  base:    { color: 'var(--cyan-deep)',    borderColor: 'var(--cyan-dim)',  label: 'BASE' },
  network: { color: 'var(--bg-panel)',     borderColor: 'var(--amber-primary)', label: 'NETWORK' },
  deep:    { color: 'var(--risk-mid-bg)',  borderColor: 'var(--risk-mid)',  label: 'DEEP' },
};

export default function TierBadge({ tier, size = 'md' }: TierBadgeProps) {
  const config = tierConfig[tier];
  return (
    <span
      style={{
        fontFamily: 'var(--font-mono)',
        fontSize: size === 'sm' ? '0.6rem' : '0.65rem',
        letterSpacing: '0.15em',
        padding: size === 'sm' ? '0.15rem 0.4rem' : '0.2rem 0.55rem',
        background: config.color,
        color: tier === 'network' ? 'var(--amber-light)' : tier === 'deep' ? 'var(--risk-mid-bright)' : 'var(--cyan-bright)',
        border: `1px solid ${config.borderColor}`,
        display: 'inline-block',
        textTransform: 'uppercase',
      }}
    >
      {config.label}
    </span>
  );
}
