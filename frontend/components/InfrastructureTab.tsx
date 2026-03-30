"use client";

import { InfrastructureHit } from "@/lib/types";

interface InfrastructureTabProps {
  infrastructure: InfrastructureHit[];
}

export default function InfrastructureTab({
  infrastructure,
}: InfrastructureTabProps) {
  if (!infrastructure || infrastructure.length === 0) {
    return (
      <div className="bg-gray-800/20 border border-gray-700 rounded-lg p-8 text-center">
        <p className="text-gray-400">
          No digital infrastructure data available. WHOIS correlation requires
          domains to be present in media intelligence results.
        </p>
      </div>
    );
  }

  const sharedCount = infrastructure.filter(
    (h) => (h.related_entities?.length || 0) > 0
  ).length;

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="bg-cyan-900/20 border border-cyan-700 rounded-lg p-4">
        <p className="text-sm text-cyan-300">
          <span className="font-semibold">{infrastructure.length}</span>{" "}
          domain{infrastructure.length !== 1 ? "s" : ""} analysed via WHOIS
          {sharedCount > 0 && (
            <>
              {" "}—{" "}
              <span className="font-semibold text-orange-300">
                {sharedCount}
              </span>{" "}
              with shared registrant or nameserver infrastructure
            </>
          )}
          .
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {infrastructure.map((hit, idx) => {
          const hasRelated = (hit.related_entities?.length || 0) > 0;

          return (
            <div
              key={idx}
              className={`bg-[#0d1425] rounded-lg p-5 border ${
                hasRelated
                  ? "border-orange-600/60"
                  : "border-gray-800"
              }`}
            >
              {/* Domain header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-sm px-2 py-1 bg-cyan-900/40 text-cyan-300 rounded font-mono">
                    {hit.domain}
                  </span>
                  {hasRelated && (
                    <span className="text-sm px-2 py-1 bg-orange-900/40 text-orange-300 rounded">
                      Shared infra
                    </span>
                  )}
                </div>
              </div>

              {/* WHOIS fields */}
              <dl className="space-y-1 text-sm">
                {hit.registrant_org && (
                  <div className="flex gap-2">
                    <dt className="text-gray-500 w-28 flex-shrink-0">
                      Registrant
                    </dt>
                    <dd className="text-gray-200 break-all">
                      {hit.registrant_org}
                    </dd>
                  </div>
                )}
                {hit.registrar && (
                  <div className="flex gap-2">
                    <dt className="text-gray-500 w-28 flex-shrink-0">
                      Registrar
                    </dt>
                    <dd className="text-gray-300">{hit.registrar}</dd>
                  </div>
                )}
                {hit.creation_date && (
                  <div className="flex gap-2">
                    <dt className="text-gray-500 w-28 flex-shrink-0">
                      Created
                    </dt>
                    <dd className="text-gray-300">{hit.creation_date}</dd>
                  </div>
                )}
                {hit.nameservers && hit.nameservers.length > 0 && (
                  <div className="flex gap-2">
                    <dt className="text-gray-500 w-28 flex-shrink-0">
                      Nameservers
                    </dt>
                    <dd className="text-gray-300 font-mono text-sm">
                      {hit.nameservers.slice(0, 3).join(", ")}
                      {hit.nameservers.length > 3 && (
                        <span className="text-gray-500">
                          {" "}+{hit.nameservers.length - 3} more
                        </span>
                      )}
                    </dd>
                  </div>
                )}
              </dl>

              {/* Related entity badges */}
              {hasRelated && (
                <div className="mt-3 pt-3 border-t border-gray-800">
                  <p className="text-sm text-gray-400 mb-2">
                    Shares infrastructure with:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {hit.related_entities.map((entity, eIdx) => (
                      <span
                        key={eIdx}
                        className="text-sm px-2 py-1 bg-orange-900/30 text-orange-300 border border-orange-700/40 rounded font-mono"
                      >
                        {entity}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
