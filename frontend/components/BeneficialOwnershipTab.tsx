"use client";

import { BeneficialOwner } from "@/lib/types";

interface BeneficialOwnershipTabProps {
  beneficialOwners: BeneficialOwner[];
}

function SourceBadge({ source }: { source: string }) {
  const isOccrp = source.toLowerCase().includes("occrp") || source.toLowerCase().includes("aleph");
  const isOpenOwnership =
    source.toLowerCase().includes("openownership") ||
    source.toLowerCase().includes("open ownership");

  if (isOccrp) {
    return (
      <span className="text-sm px-2 py-1 bg-orange-900/40 text-orange-300 border border-orange-700/40 rounded">
        OCCRP
      </span>
    );
  }
  if (isOpenOwnership) {
    return (
      <span className="text-sm px-2 py-1 bg-emerald-900/40 text-emerald-300 border border-emerald-700/40 rounded">
        OpenOwnership
      </span>
    );
  }
  return (
    <span className="text-sm px-2 py-1 bg-gray-700 text-gray-300 rounded">
      {source}
    </span>
  );
}

export default function BeneficialOwnershipTab({
  beneficialOwners,
}: BeneficialOwnershipTabProps) {
  if (!beneficialOwners || beneficialOwners.length === 0) {
    return (
      <div className="bg-gray-800/20 border border-gray-700 rounded-lg p-8 text-center">
        <p className="text-gray-400">
          No beneficial ownership records found in OCCRP Aleph or the Open
          Ownership Register for this entity.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="bg-emerald-900/20 border border-emerald-700 rounded-lg p-4">
        <p className="text-sm text-emerald-300">
          <span className="font-semibold">{beneficialOwners.length}</span>{" "}
          beneficial owner record{beneficialOwners.length !== 1 ? "s" : ""}{" "}
          retrieved from OCCRP Aleph and the Open Ownership Register.
        </p>
      </div>

      {/* Table */}
      <div className="bg-[#0d1425] border border-gray-800 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-900/50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase">
                  Nationality
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase">
                  Ownership %
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase">
                  Source
                </th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-400 uppercase">
                  Verification Date
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {beneficialOwners.map((owner, idx) => (
                <tr key={idx} className="hover:bg-gray-900/30">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="text-white font-medium">
                        {owner.name}
                      </span>
                    </div>
                    {owner.source_url && (
                      <a
                        href={owner.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 text-sm"
                      >
                        View record →
                      </a>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {owner.nationality || "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-300">
                    {owner.ownership_pct != null
                      ? `${owner.ownership_pct.toFixed(1)}%`
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <SourceBadge source={owner.source} />
                  </td>
                  <td className="px-4 py-3 text-gray-300 text-sm">
                    {owner.verification_date || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
