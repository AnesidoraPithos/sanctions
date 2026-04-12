"use client";

import { useState } from "react";
import { BeneficialOwner, BodsData, BodsPersonStatement, BodsEntityStatement } from "@/lib/types";

interface BeneficialOwnershipTabProps {
  beneficialOwners: BeneficialOwner[];
  bodsData?: BodsData;
}

const SOURCE_STYLES: Record<string, { bg: string; border: string; color: string; label: string }> = {
  occrp: {
    bg: "rgba(168,112,8,0.12)",
    border: "var(--amber-primary)",
    color: "var(--amber-light)",
    label: "OCCRP",
  },
  companies_house: {
    bg: "rgba(0,188,80,0.10)",
    border: "#00bc50",
    color: "#4dffaa",
    label: "Companies House",
  },
  sec_edgar: {
    bg: "rgba(60,130,255,0.10)",
    border: "#3c82ff",
    color: "#7ab8ff",
    label: "SEC EDGAR",
  },
  opencorporates: {
    bg: "rgba(150,80,220,0.10)",
    border: "#9650dc",
    color: "#c496ff",
    label: "OpenCorporates",
  },
};

function SourceBadge({ source }: { source: string }) {
  const base: React.CSSProperties = {
    fontFamily: "var(--font-mono)",
    fontSize: "0.65rem",
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
    padding: "0.2rem 0.5rem",
    border: "1px solid",
    display: "inline-block",
  };

  const lower = source.toLowerCase();

  if (lower.includes("occrp") || lower.includes("aleph")) {
    const s = SOURCE_STYLES.occrp;
    return <span style={{ ...base, background: s.bg, borderColor: s.border, color: s.color }}>{s.label}</span>;
  }
  if (lower.includes("companies_house") || lower.includes("companies house")) {
    const s = SOURCE_STYLES.companies_house;
    return <span style={{ ...base, background: s.bg, borderColor: s.border, color: s.color }}>{s.label}</span>;
  }
  if (lower.includes("sec_edgar") || lower.includes("sec edgar") || lower.includes("sec")) {
    const s = SOURCE_STYLES.sec_edgar;
    return <span style={{ ...base, background: s.bg, borderColor: s.border, color: s.color }}>{s.label}</span>;
  }
  if (lower.includes("opencorporates")) {
    const s = SOURCE_STYLES.opencorporates;
    return <span style={{ ...base, background: s.bg, borderColor: s.border, color: s.color }}>{s.label}</span>;
  }
  return (
    <span style={{ ...base, background: "var(--bg-panel)", borderColor: "var(--border-main)", color: "var(--text-muted)" }}>
      {source}
    </span>
  );
}

function InterestTypeBadge({ type }: { type?: string }) {
  if (!type) return null;
  const isDirectorship = type.toLowerCase().includes("directorship");
  return (
    <span
      style={{
        fontFamily: "var(--font-mono)",
        fontSize: "0.6rem",
        letterSpacing: "0.06em",
        textTransform: "uppercase" as const,
        padding: "0.1rem 0.35rem",
        border: "1px solid",
        display: "inline-block",
        background: isDirectorship ? "rgba(168,112,8,0.08)" : "rgba(0,188,188,0.08)",
        borderColor: isDirectorship ? "rgba(168,112,8,0.5)" : "rgba(0,188,188,0.4)",
        color: isDirectorship ? "var(--amber-light)" : "var(--cyan-bright)",
        marginLeft: "0.3rem",
      }}
    >
      {isDirectorship ? "Director" : "Shareholder"}
    </span>
  );
}

const thStyle: React.CSSProperties = {
  padding: "0.5rem 1rem",
  textAlign: "left",
  fontFamily: "var(--font-mono)",
  fontSize: "0.65rem",
  letterSpacing: "0.14em",
  textTransform: "uppercase",
  color: "var(--text-muted)",
  background: "var(--bg-panel)",
  fontWeight: 500,
  borderBottom: "1px solid var(--border-main)",
};

// ---------------------------------------------------------------------------
// BODS chain section
// ---------------------------------------------------------------------------

function resolvePartyName(
  partyId: string | undefined,
  personMap: Map<string, BodsPersonStatement>,
  entityMap: Map<string, BodsEntityStatement>
): { name: string; isEntity: boolean } {
  if (!partyId) return { name: "Unknown", isEntity: false };
  const person = personMap.get(partyId);
  if (person) {
    return { name: person.names?.[0]?.fullName || partyId, isEntity: false };
  }
  const entity = entityMap.get(partyId);
  if (entity) {
    return { name: entity.name || partyId, isEntity: true };
  }
  return { name: partyId, isEntity: false };
}

function BodsChainsSection({ bodsData }: { bodsData: BodsData }) {
  const [expanded, setExpanded] = useState(true);

  const personMap = new Map<string, BodsPersonStatement>(
    bodsData.persons.map((p) => [p.statementID, p])
  );
  const entityMap = new Map<string, BodsEntityStatement>(
    bodsData.entities.map((e) => [e.statementID, e])
  );

  // Group ownership statements by subject entity name
  const grouped: Record<string, typeof bodsData.ownershipOrControlStatements> = {};
  for (const stmt of bodsData.ownershipOrControlStatements) {
    const subjectId = stmt.subject.describedByEntityStatement;
    const subjectName = entityMap.get(subjectId)?.name || subjectId;
    if (!grouped[subjectName]) grouped[subjectName] = [];
    grouped[subjectName].push(stmt);
  }

  const subjectNames = Object.keys(grouped);
  if (subjectNames.length === 0) return null;

  return (
    <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-dim)" }}>
      {/* Header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        style={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "0.75rem 1rem",
          background: "transparent",
          border: "none",
          borderBottom: expanded ? "1px solid var(--border-dim)" : "none",
          cursor: "pointer",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.7rem",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: "var(--text-secondary)",
            fontWeight: 600,
          }}
        >
          Ownership Chain (BODS)
        </span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--text-muted)" }}>
          {expanded ? "▲" : "▼"}
        </span>
      </button>

      {expanded && (
        <div style={{ padding: "1rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
          {subjectNames.map((subjectName) => (
            <div key={subjectName}>
              {/* Subject entity label */}
              <div
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.72rem",
                  color: "var(--amber-light)",
                  letterSpacing: "0.08em",
                  marginBottom: "0.5rem",
                  paddingBottom: "0.3rem",
                  borderBottom: "1px solid var(--border-void)",
                }}
              >
                {subjectName}
              </div>
              {/* Ownership statements */}
              <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem", paddingLeft: "1rem" }}>
                {grouped[subjectName].map((stmt) => {
                  const partyPersonId = stmt.interestedParty.describedByPersonStatement;
                  const partyEntityId = stmt.interestedParty.describedByEntityStatement;
                  const { name: partyName, isEntity } = resolvePartyName(
                    partyPersonId || partyEntityId,
                    personMap,
                    entityMap
                  );
                  const interest = stmt.interests?.[0];
                  const interestType = interest?.type || "shareholding";
                  const sharePct = interest?.share?.exact ?? interest?.share?.minimum;
                  const source = (partyPersonId
                    ? personMap.get(partyPersonId)?.identifiers?.[0]?.scheme
                    : entityMap.get(partyEntityId || "")?.identifiers?.[0]?.scheme) || "unknown";

                  return (
                    <div
                      key={stmt.statementID}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.6rem",
                        flexWrap: "wrap",
                        padding: "0.35rem 0.5rem",
                        background: "var(--bg-panel)",
                        border: "1px solid var(--border-void)",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: "var(--font-mono)",
                          fontSize: "0.75rem",
                          color: "var(--text-bright)",
                          fontWeight: 500,
                        }}
                      >
                        {partyName}
                      </span>
                      {isEntity && (
                        <span
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.6rem",
                            letterSpacing: "0.06em",
                            color: "var(--text-muted)",
                            border: "1px solid var(--border-dim)",
                            padding: "0.1rem 0.3rem",
                          }}
                        >
                          ENTITY
                        </span>
                      )}
                      <InterestTypeBadge type={interestType} />
                      {sharePct != null && (
                        <span
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: "0.72rem",
                            color: "var(--cyan-bright)",
                          }}
                        >
                          {sharePct.toFixed(1)}%
                        </span>
                      )}
                      {stmt.statementDate && (
                        <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.68rem", color: "var(--text-muted)" }}>
                          {stmt.statementDate}
                        </span>
                      )}
                      <SourceBadge source={source} />
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function BeneficialOwnershipTab({
  beneficialOwners,
  bodsData,
}: BeneficialOwnershipTabProps) {
  const hasOwners = beneficialOwners && beneficialOwners.length > 0;
  const hasBods = bodsData && (
    bodsData.entities.length > 0 ||
    bodsData.persons.length > 0 ||
    bodsData.ownershipOrControlStatements.length > 0
  );

  if (!hasOwners && !hasBods) {
    return (
      <div
        style={{
          background: "var(--bg-panel)",
          border: "1px solid var(--border-dim)",
          padding: "2rem",
          textAlign: "center",
        }}
      >
        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", margin: 0 }}>
          No beneficial ownership records found in Companies House, SEC EDGAR,
          OpenCorporates, or OCCRP Aleph for this entity.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Summary */}
      <div
        style={{
          background: "rgba(0,188,188,0.06)",
          border: "1px solid var(--cyan-dark)",
          borderLeft: "3px solid var(--cyan-main)",
          padding: "0.875rem 1rem",
        }}
      >
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", margin: 0, lineHeight: 1.5 }}>
          <span style={{ color: "var(--cyan-bright)", fontWeight: 600 }}>
            {beneficialOwners.length}
          </span>{" "}
          beneficial owner record{beneficialOwners.length !== 1 ? "s" : ""}{" "}
          structured using BODS from Companies House, SEC EDGAR, OpenCorporates, and OCCRP Aleph.
        </p>
      </div>

      {/* Flat owners table */}
      {hasOwners && (
        <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-dim)", overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8rem" }}>
              <thead>
                <tr>
                  <th style={thStyle}>Name</th>
                  <th style={thStyle}>Nationality</th>
                  <th style={thStyle}>Ownership %</th>
                  <th style={thStyle}>Source</th>
                  <th style={thStyle}>Verification Date</th>
                </tr>
              </thead>
              <tbody>
                {beneficialOwners.map((owner, idx) => (
                  <tr
                    key={idx}
                    style={{
                      background: idx % 2 === 0 ? "var(--bg-surface)" : "var(--bg-panel)",
                      borderBottom: "1px solid var(--border-void)",
                    }}
                  >
                    <td style={{ padding: "0.75rem 1rem" }}>
                      <div style={{ display: "flex", alignItems: "baseline", gap: "0.4rem", flexWrap: "wrap" }}>
                        <span style={{ color: "var(--text-bright)", fontWeight: 500, fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                          {owner.name}
                        </span>
                        {owner.entity_type === "entity" && (
                          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.6rem", letterSpacing: "0.08em", color: "var(--text-muted)", border: "1px solid var(--border-dim)", padding: "0.1rem 0.3rem" }}>
                            ENTITY
                          </span>
                        )}
                        <InterestTypeBadge type={owner.interest_type} />
                      </div>
                      {owner.via && owner.via.length > 0 && (
                        <div style={{ color: "var(--text-muted)", fontSize: "0.68rem", fontFamily: "var(--font-mono)", marginTop: "0.2rem", lineHeight: 1.4 }}>
                          via {owner.via.join(" \u2192 ")}
                        </div>
                      )}
                      {owner.source_url && (
                        <div style={{ marginTop: "0.15rem" }}>
                          <a
                            href={owner.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: "var(--amber-primary)", fontSize: "0.72rem", fontFamily: "var(--font-mono)", textDecoration: "none", letterSpacing: "0.04em" }}
                          >
                            View record →
                          </a>
                        </div>
                      )}
                    </td>
                    <td style={{ padding: "0.75rem 1rem", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                      {owner.nationality || "—"}
                    </td>
                    <td style={{ padding: "0.75rem 1rem", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                      {owner.ownership_pct != null ? `${owner.ownership_pct.toFixed(1)}%` : "—"}
                    </td>
                    <td style={{ padding: "0.75rem 1rem" }}>
                      <SourceBadge source={owner.source} />
                    </td>
                    <td style={{ padding: "0.75rem 1rem", color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>
                      {owner.verification_date || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* BODS chain view */}
      {hasBods && <BodsChainsSection bodsData={bodsData} />}
    </div>
  );
}
