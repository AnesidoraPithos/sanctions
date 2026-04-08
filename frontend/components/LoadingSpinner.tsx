interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
}

const spinnerSize = { sm: 20, md: 32, lg: 44 };

export default function LoadingSpinner({ size = 'md', message }: LoadingSpinnerProps) {
  const s = spinnerSize[size];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
      <div
        style={{
          width: s,
          height: s,
          border: `${size === 'lg' ? 2 : 2}px solid var(--border-main)`,
          borderTopColor: 'var(--amber-main)',
          borderRadius: '50%',
          animation: 'spin 0.9s linear infinite',
          boxShadow: '0 0 10px rgba(196, 140, 12, 0.2)',
        }}
      />
      {message && (
        <p
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.72rem',
            letterSpacing: '0.1em',
            color: 'var(--text-muted)',
            animation: 'data-pulse 2s ease-in-out infinite',
            textTransform: 'uppercase',
          }}
        >
          {message}
        </p>
      )}
    </div>
  );
}
