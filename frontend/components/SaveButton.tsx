'use client';

import { useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api-client';

interface SaveButtonProps {
  searchId: string;
  initialSaved: boolean;
  initialLabel?: string;
  initialNotes?: string;
  initialTags?: string;
  onSaveChange?: (saved: boolean) => void;
}

export default function SaveButton({ searchId, initialSaved, initialLabel, initialNotes, initialTags, onSaveChange }: SaveButtonProps) {
  const [isSaved, setIsSaved] = useState(initialSaved);
  const [label, setLabel] = useState(initialLabel ?? '');
  const [notes, setNotes] = useState(initialNotes ?? '');
  const [tags, setTags] = useState(initialTags ?? '');
  const [isLoading, setIsLoading] = useState(false);
  const [showLabelInput, setShowLabelInput] = useState(false);
  const [confirmingRemove, setConfirmingRemove] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (showLabelInput && inputRef.current) {
      inputRef.current.focus();
    }
  }, [showLabelInput]);

  // Close popup and cancel remove-confirm on outside click
  useEffect(() => {
    if (!showLabelInput && !confirmingRemove) return;
    const handler = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
        setShowLabelInput(false);
        setConfirmingRemove(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showLabelInput, confirmingRemove]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  const handleClick = () => {
    if (isSaved) {
      if (confirmingRemove) {
        handleUnsave();
      } else {
        setConfirmingRemove(true);
      }
    } else {
      setShowLabelInput(true);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    setShowLabelInput(false);
    try {
      await api.saveResult(searchId, label || undefined, notes || undefined, tags || undefined);
      setIsSaved(true);
      onSaveChange?.(true);
      showToast('Saved');
    } catch {
      showToast('Failed to save');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUnsave = async () => {
    setConfirmingRemove(false);
    setIsLoading(true);
    try {
      await api.unsaveResult(searchId);
      setIsSaved(false);
      setLabel('');
      setNotes('');
      setTags('');
      onSaveChange?.(false);
      showToast('Bookmark removed');
    } catch {
      showToast('Failed to remove bookmark');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div ref={popupRef} className="relative flex items-center gap-2">
      {/* Label input popup */}
      {showLabelInput && (
        <div
          style={{
            position: 'absolute',
            right: 0,
            top: 'calc(100% + 6px)',
            zIndex: 50,
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-main)',
            padding: '0.875rem',
            width: '280px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
          }}
        >
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '0.375rem', textTransform: 'uppercase' }}>
            Label (optional)
          </p>
          <input
            ref={inputRef}
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') setShowLabelInput(false);
            }}
            placeholder="e.g. Review next week"
            className="intel-input"
            style={{ marginBottom: '0.625rem', fontSize: '0.75rem' }}
          />
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '0.375rem', textTransform: 'uppercase' }}>
            Tags (comma-separated)
          </p>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="sanctions, china, review"
            className="intel-input"
            style={{ marginBottom: '0.625rem', fontSize: '0.75rem' }}
          />
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '0.375rem', textTransform: 'uppercase' }}>
            Notes
          </p>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Free-form notes about this entity..."
            className="intel-input"
            rows={3}
            style={{ marginBottom: '0.625rem', fontSize: '0.75rem', resize: 'vertical', width: '100%', boxSizing: 'border-box' }}
          />
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={handleSave}
              className="btn-primary"
              style={{ flex: 1, fontSize: '0.65rem', padding: '0.375rem' }}
            >
              Save
            </button>
            <button
              onClick={() => setShowLabelInput(false)}
              className="btn-secondary"
              style={{ flex: 1, fontSize: '0.65rem', padding: '0.375rem' }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Bookmark button */}
      <button
        onClick={handleClick}
        disabled={isLoading}
        title={confirmingRemove ? 'Click again to confirm removal' : isSaved ? 'Remove bookmark' : 'Bookmark this result'}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
          padding: '0.375rem 0.75rem',
          fontSize: '0.65rem',
          fontFamily: 'var(--font-mono)',
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          border: confirmingRemove
            ? '1px solid var(--risk-high)'
            : isSaved
              ? '1px solid var(--risk-safe)'
              : '1px solid var(--border-main)',
          background: confirmingRemove
            ? 'var(--risk-high-bg)'
            : isSaved
              ? 'var(--risk-safe-bg)'
              : 'var(--bg-panel)',
          color: confirmingRemove
            ? 'var(--risk-high-bright)'
            : isSaved
              ? 'var(--risk-safe-bright)'
              : 'var(--text-secondary)',
          cursor: isLoading ? 'not-allowed' : 'pointer',
          opacity: isLoading ? 0.5 : 1,
          transition: 'all 0.15s',
          whiteSpace: 'nowrap',
        }}
      >
        {isSaved ? (
          <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor">
            <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
          </svg>
        ) : (
          <svg width="12" height="12" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
          </svg>
        )}
        <span>{confirmingRemove ? 'Confirm Remove?' : isSaved ? 'Saved' : 'Save'}</span>
      </button>

      {/* Toast */}
      {toast && (
        <div
          style={{
            position: 'absolute',
            right: 0,
            top: 'calc(100% + 6px)',
            zIndex: 50,
            background: 'var(--bg-surface)',
            border: '1px solid var(--border-main)',
            color: 'var(--text-main)',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.7rem',
            letterSpacing: '0.06em',
            padding: '0.375rem 0.75rem',
            whiteSpace: 'nowrap',
            boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
          }}
        >
          {toast}
        </div>
      )}
    </div>
  );
}
