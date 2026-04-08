'use client';

import { useProgress } from '@/lib/websocket';

interface ProgressTrackerProps {
  searchId: string | null | undefined;
}

/**
 * ProgressTracker — shown while a search is in-flight.
 * Connects to the backend WebSocket and updates in real time.
 * Renders nothing once the search is done or if searchId is absent.
 */
export default function ProgressTracker({ searchId }: ProgressTrackerProps) {
  const { step, percent, done, error } = useProgress(searchId);

  if (!searchId || done) return null;

  return (
    <div
      style={{
        borderTop: '1px solid var(--border-dim)',
        padding: '1.25rem 1.5rem',
        background: 'var(--bg-panel)',
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '0.625rem',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: 0 }}>
          <div
            style={{
              width: '6px',
              height: '6px',
              background: 'var(--cyan-bright)',
              flexShrink: 0,
              animation: 'data-pulse 1s ease-in-out infinite',
              boxShadow: '0 0 6px var(--cyan-main)',
            }}
          />
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--text-main)',
              letterSpacing: '0.02em',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {step}
          </span>
        </div>
        <span
          className="font-data"
          style={{
            fontSize: '0.875rem',
            color: 'var(--amber-light)',
            flexShrink: 0,
          }}
        >
          {percent}
          <span style={{ fontSize: '0.6rem', color: 'var(--amber-primary)', marginLeft: '1px' }}>%</span>
        </span>
      </div>

      {/* Progress bar */}
      <div
        style={{
          width: '100%',
          height: '3px',
          background: 'var(--border-dim)',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            width: `${percent}%`,
            background: 'linear-gradient(90deg, var(--amber-primary), var(--amber-light))',
            boxShadow: '0 0 8px var(--amber-primary)',
            transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        />
      </div>

      {/* Error state */}
      {error && (
        <p
          style={{
            marginTop: '0.5rem',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.72rem',
            color: 'var(--risk-critical-bright)',
          }}
        >
          {error}
        </p>
      )}

      {/* Info text */}
      <p
        style={{
          marginTop: '0.5rem',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.68rem',
          color: 'var(--text-faint)',
          letterSpacing: '0.04em',
        }}
      >
        Results will load automatically when research completes.
      </p>
    </div>
  );
}
