'use client';

import { useState, useRef, useEffect } from 'react';
import { api } from '@/lib/api-client';

interface SaveButtonProps {
  searchId: string;
  initialSaved: boolean;
  initialLabel?: string;
  onSaveChange?: (saved: boolean) => void;
}

export default function SaveButton({ searchId, initialSaved, initialLabel, onSaveChange }: SaveButtonProps) {
  const [isSaved, setIsSaved] = useState(initialSaved);
  const [label, setLabel] = useState(initialLabel ?? '');
  const [isLoading, setIsLoading] = useState(false);
  const [showLabelInput, setShowLabelInput] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (showLabelInput && inputRef.current) {
      inputRef.current.focus();
    }
  }, [showLabelInput]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  const handleClick = () => {
    if (isSaved) {
      handleUnsave();
    } else {
      setShowLabelInput(true);
    }
  };

  const handleSave = async () => {
    setIsLoading(true);
    setShowLabelInput(false);
    try {
      await api.saveResult(searchId, label || undefined);
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
    if (!confirm('Remove bookmark from this result?')) return;
    setIsLoading(true);
    try {
      await api.unsaveResult(searchId);
      setIsSaved(false);
      setLabel('');
      onSaveChange?.(false);
      showToast('Bookmark removed');
    } catch {
      showToast('Failed to remove bookmark');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex items-center gap-2">
      {/* Label input popup */}
      {showLabelInput && (
        <div className="absolute right-0 top-full mt-2 z-50 bg-[#0d1425] border border-gray-700 rounded-lg shadow-xl p-3 w-64">
          <p className="text-sm text-gray-400 mb-2">Add a label (optional)</p>
          <input
            ref={inputRef}
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave();
              if (e.key === 'Escape') setShowLabelInput(false);
            }}
            placeholder="e.g. Review next week"
            className="w-full bg-[#1a2035] border border-gray-600 rounded px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 mb-2"
          />
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              className="flex-1 bg-green-600 hover:bg-green-500 text-white text-sm font-medium py-1.5 rounded transition-colors"
            >
              Save
            </button>
            <button
              onClick={() => setShowLabelInput(false)}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm font-medium py-1.5 rounded transition-colors"
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
        title={isSaved ? 'Remove bookmark' : 'Bookmark this result'}
        className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all
          ${isSaved
            ? 'bg-green-900/40 border border-green-600 text-green-400 hover:bg-red-900/30 hover:border-red-600 hover:text-red-400'
            : 'bg-gray-800 border border-gray-600 text-gray-300 hover:border-green-500 hover:text-green-400'
          }
          ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        {isSaved ? (
          <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
          </svg>
        ) : (
          <svg className="w-4 h-4" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z" />
          </svg>
        )}
        <span>{isSaved ? 'Saved' : 'Save'}</span>
      </button>

      {/* Toast */}
      {toast && (
        <div className="absolute right-0 top-full mt-2 z-50 bg-gray-800 border border-gray-600 text-white text-sm px-3 py-1.5 rounded-lg shadow-lg whitespace-nowrap">
          {toast}
        </div>
      )}
    </div>
  );
}
