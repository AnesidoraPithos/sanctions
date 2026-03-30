"use client";

import { useProgress } from "@/lib/websocket";

interface ProgressTrackerProps {
  searchId: string | null | undefined;
}

/**
 * ProgressTracker — animated progress bar shown while a search is in-flight.
 * Connects to the backend WebSocket and updates in real time.
 * Renders nothing once the search is done or if searchId is absent.
 */
export default function ProgressTracker({ searchId }: ProgressTrackerProps) {
  const { step, percent, done, error } = useProgress(searchId);

  if (!searchId || done) return null;

  return (
    <div className="mt-6 p-5 bg-[#0d1425] border border-blue-800/60 rounded-xl shadow-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-blue-300">{step}</span>
        <span className="text-sm font-mono text-blue-400">{percent}%</span>
      </div>

      {/* Track */}
      <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
        {/* Animated fill */}
        <div
          className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>

      {error && (
        <p className="text-sm text-red-400 mt-2">{error}</p>
      )}

      <p className="text-sm text-gray-500 mt-2">
        Results will load automatically when research completes.
      </p>
    </div>
  );
}
