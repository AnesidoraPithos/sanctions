"use client";

import { useState } from "react";
import { DirectorPivot } from "@/lib/types";

interface ManagementNetworkTabProps {
  directorPivots: DirectorPivot[];
}

export default function ManagementNetworkTab({
  directorPivots,
}: ManagementNetworkTabProps) {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  if (!directorPivots || directorPivots.length === 0) {
    return (
      <div className="bg-gray-800/20 border border-gray-700 rounded-lg p-8 text-center">
        <p className="text-gray-400">
          No interlocking directorate data found. This may occur when SEC EDGAR
          has no filings linking directors to other companies.
        </p>
      </div>
    );
  }

  const toggle = (idx: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  const totalCompanies = directorPivots.reduce(
    (sum, p) => sum + (p.companies?.length || 0),
    0
  );

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-4">
        <p className="text-sm text-purple-300">
          <span className="font-semibold">{directorPivots.length}</span>{" "}
          director{directorPivots.length !== 1 ? "s" : ""} analysed —{" "}
          <span className="font-semibold">{totalCompanies}</span> interlocking
          company link{totalCompanies !== 1 ? "s" : ""} found via SEC EDGAR
          filings.
        </p>
      </div>

      {directorPivots.map((pivot, idx) => {
        const isOpen = expanded.has(idx);
        const companyCount = pivot.companies?.length || 0;

        return (
          <div
            key={idx}
            className="bg-[#0d1425] border border-gray-800 rounded-lg overflow-hidden"
          >
            {/* Director card header */}
            <button
              type="button"
              onClick={() => toggle(idx)}
              className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-900/40 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-full bg-purple-900/50 border border-purple-600 flex items-center justify-center flex-shrink-0">
                  <span className="text-purple-400 text-sm font-bold">
                    {pivot.director_name?.charAt(0)?.toUpperCase() || "?"}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">
                    {pivot.director_name || "Unknown"}
                  </p>
                  {pivot.title && (
                    <p className="text-sm text-gray-400">{pivot.title}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm px-2 py-1 bg-purple-900/30 text-purple-300 rounded">
                  {companyCount} company link{companyCount !== 1 ? "s" : ""}
                </span>
                <span className="text-gray-500 text-sm">
                  {isOpen ? "▲" : "▼"}
                </span>
              </div>
            </button>

            {/* Expanded company table */}
            {isOpen && (
              <div className="border-t border-gray-800">
                {companyCount === 0 ? (
                  <p className="text-sm text-gray-500 px-5 py-4">
                    No related company filings found for this director.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-900/50">
                        <tr>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-400 uppercase">
                            Company
                          </th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-400 uppercase">
                            Role
                          </th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-400 uppercase">
                            Filing Date
                          </th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-400 uppercase">
                            Source
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-800">
                        {pivot.companies.map((company, cIdx) => (
                          <tr key={cIdx} className="hover:bg-gray-900/30">
                            <td className="px-4 py-3 text-white font-medium">
                              {company.company_name}
                            </td>
                            <td className="px-4 py-3 text-gray-300">
                              {company.role || "—"}
                            </td>
                            <td className="px-4 py-3 text-gray-300">
                              {company.filing_date || "—"}
                            </td>
                            <td className="px-4 py-3">
                              {company.source_url ? (
                                <a
                                  href={company.source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-400 hover:text-blue-300 text-sm"
                                >
                                  SEC EDGAR →
                                </a>
                              ) : (
                                <span className="text-gray-500 text-sm">—</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
