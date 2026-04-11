"use client";

import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { ResultsResponse, NetworkData } from "@/lib/types";

/**
 * GeographicMap Component
 *
 * Plots entity geographic footprint on a dark-themed Leaflet map.
 * Derives country-level map points from text-based location fields
 * (jurisdiction, nationality, address) via an embedded centroid lookup —
 * no external geocoding API required.
 */

interface GeographicMapProps {
  results: ResultsResponse;
}

interface MapPoint {
  lat: number;
  lng: number;
  type: "subsidiary" | "beneficial_owner" | "network_country" | "sanctions";
  entities: string[];
}

// Compact country name/code → [lat, lng] centroid lookup.
// Keys are lowercase ISO-2 codes AND lowercase full English names.
const COUNTRY_CENTROIDS: Record<string, [number, number]> = {
  // Americas
  us: [37.09, -95.71], "united states": [37.09, -95.71], usa: [37.09, -95.71],
  ca: [56.13, -106.35], canada: [56.13, -106.35],
  mx: [23.63, -102.55], mexico: [23.63, -102.55],
  br: [-14.24, -51.93], brazil: [-14.24, -51.93], brasil: [-14.24, -51.93],
  ar: [-38.42, -63.62], argentina: [-38.42, -63.62],
  co: [4.57, -74.3], colombia: [4.57, -74.3],
  ve: [6.42, -66.59], venezuela: [6.42, -66.59],
  cu: [21.52, -77.78], cuba: [21.52, -77.78],
  // Europe
  gb: [55.38, -3.44], uk: [55.38, -3.44], "united kingdom": [55.38, -3.44],
  de: [51.17, 10.45], germany: [51.17, 10.45],
  fr: [46.23, 2.21], france: [46.23, 2.21],
  it: [41.87, 12.57], italy: [41.87, 12.57],
  es: [40.46, -3.75], spain: [40.46, -3.75],
  nl: [52.13, 5.29], netherlands: [52.13, 5.29], holland: [52.13, 5.29],
  be: [50.5, 4.47], belgium: [50.5, 4.47],
  ch: [46.82, 8.23], switzerland: [46.82, 8.23],
  at: [47.52, 14.55], austria: [47.52, 14.55],
  se: [60.13, 18.64], sweden: [60.13, 18.64],
  no: [60.47, 8.47], norway: [60.47, 8.47],
  dk: [56.26, 9.5], denmark: [56.26, 9.5],
  fi: [61.92, 25.75], finland: [61.92, 25.75],
  pl: [51.92, 19.15], poland: [51.92, 19.15],
  cz: [49.82, 15.47], "czech republic": [49.82, 15.47], czechia: [49.82, 15.47],
  pt: [39.4, -8.22], portugal: [39.4, -8.22],
  gr: [39.07, 21.82], greece: [39.07, 21.82],
  hu: [47.16, 19.5], hungary: [47.16, 19.5],
  ro: [45.94, 24.97], romania: [45.94, 24.97],
  ua: [48.38, 31.17], ukraine: [48.38, 31.17],
  by: [53.71, 27.95], belarus: [53.71, 27.95],
  // Russia & CIS
  ru: [61.52, 105.32], russia: [61.52, 105.32],
  kz: [48.02, 66.92], kazakhstan: [48.02, 66.92],
  uz: [41.38, 64.59], uzbekistan: [41.38, 64.59],
  az: [40.14, 47.58], azerbaijan: [40.14, 47.58],
  ge: [42.32, 43.36], georgia: [42.32, 43.36],
  // Middle East
  ae: [23.42, 53.85], "united arab emirates": [23.42, 53.85], uae: [23.42, 53.85],
  sa: [23.89, 45.08], "saudi arabia": [23.89, 45.08],
  ir: [32.43, 53.69], iran: [32.43, 53.69],
  iq: [33.22, 43.68], iraq: [33.22, 43.68],
  sy: [34.8, 38.99], syria: [34.8, 38.99],
  il: [31.05, 34.85], israel: [31.05, 34.85],
  jo: [30.59, 36.24], jordan: [30.59, 36.24],
  lb: [33.85, 35.86], lebanon: [33.85, 35.86],
  tr: [38.96, 35.24], turkey: [38.96, 35.24], türkiye: [38.96, 35.24],
  ye: [15.55, 48.52], yemen: [15.55, 48.52],
  qa: [25.35, 51.18], qatar: [25.35, 51.18],
  kw: [29.31, 47.48], kuwait: [29.31, 47.48],
  bh: [26.0, 50.55], bahrain: [26.0, 50.55],
  om: [21.51, 55.92], oman: [21.51, 55.92],
  // Asia
  cn: [35.86, 104.2], china: [35.86, 104.2],
  hk: [22.32, 114.17], "hong kong": [22.32, 114.17],
  tw: [23.7, 120.96], taiwan: [23.7, 120.96],
  jp: [36.2, 138.25], japan: [36.2, 138.25],
  kr: [35.91, 127.77], "south korea": [35.91, 127.77], korea: [35.91, 127.77],
  kp: [40.34, 127.51], "north korea": [40.34, 127.51],
  in: [20.59, 78.96], india: [20.59, 78.96],
  pk: [30.38, 69.35], pakistan: [30.38, 69.35],
  bd: [23.68, 90.36], bangladesh: [23.68, 90.36],
  sg: [1.35, 103.82], singapore: [1.35, 103.82],
  my: [4.21, 108.0], malaysia: [4.21, 108.0],
  id: [-0.79, 113.92], indonesia: [-0.79, 113.92],
  th: [15.87, 100.99], thailand: [15.87, 100.99],
  vn: [14.06, 108.28], vietnam: [14.06, 108.28],
  ph: [12.88, 121.77], philippines: [12.88, 121.77],
  mm: [19.15, 95.96], myanmar: [19.15, 95.96], burma: [19.15, 95.96],
  // Africa
  za: [-30.56, 22.94], "south africa": [-30.56, 22.94],
  ng: [9.08, 8.68], nigeria: [9.08, 8.68],
  eg: [26.82, 30.8], egypt: [26.82, 30.8],
  ly: [26.34, 17.23], libya: [26.34, 17.23],
  sd: [12.86, 30.22], sudan: [12.86, 30.22],
  et: [9.15, 40.49], ethiopia: [9.15, 40.49],
  ke: [-0.02, 37.91], kenya: [-0.02, 37.91],
  ma: [31.79, -7.09], morocco: [31.79, -7.09],
  // Oceania
  au: [-25.27, 133.78], australia: [-25.27, 133.78],
  nz: [-40.9, 174.89], "new zealand": [-40.9, 174.89],
  // Offshore / special
  ky: [19.31, -81.25], "cayman islands": [19.31, -81.25], cayman: [19.31, -81.25],
  bvi: [18.43, -64.62], "british virgin islands": [18.43, -64.62],
  vg: [18.43, -64.62],
  pa: [8.54, -80.78], panama: [8.54, -80.78],
  lu: [49.82, 6.13], luxembourg: [49.82, 6.13],
  mt: [35.94, 14.38], malta: [35.94, 14.38],
  cy: [35.13, 33.43], cyprus: [35.13, 33.43],
  lv: [56.88, 24.6], latvia: [56.88, 24.6],
  ee: [58.6, 25.01], estonia: [58.6, 25.01],
  lt: [55.17, 23.88], lithuania: [55.17, 23.88],
  ie: [53.41, -8.24], ireland: [53.41, -8.24],
  is: [64.96, -19.02], iceland: [64.96, -19.02],
  li: [47.14, 9.55], liechtenstein: [47.14, 9.55],
  mc: [43.74, 7.41], monaco: [43.74, 7.41],
  im: [54.24, -4.55], "isle of man": [54.24, -4.55],
  gg: [49.46, -2.59], guernsey: [49.46, -2.59],
  je: [49.21, -2.13], jersey: [49.21, -2.13],
};

const MARKER_COLORS: Record<MapPoint["type"], string> = {
  sanctions:        "#c0392b",  // risk-critical red
  subsidiary:       "#9A6200",  // amber-main
  beneficial_owner: "#009AB8",  // cyan-glow
  network_country:  "#7A4E00",  // amber-primary
};

const TYPE_LABELS: Record<MapPoint["type"], string> = {
  sanctions:        "Sanctions Hit",
  subsidiary:       "Subsidiary / Sister",
  beneficial_owner: "Beneficial Owner",
  network_country:  "Network Country",
};

function resolveLatLng(raw: string | undefined | null): [number, number] | null {
  if (!raw) return null;
  const key = raw.trim().toLowerCase();
  return COUNTRY_CENTROIDS[key] ?? null;
}

/**
 * Extract a probable country token from a free-text address.
 * Tries the last comma-separated segment, then a 2-letter uppercase suffix.
 */
function extractCountryFromAddress(address: string): [number, number] | null {
  const parts = address.split(",").map((s) => s.trim());
  for (let i = parts.length - 1; i >= 0; i--) {
    const candidate = parts[i].toLowerCase();
    if (COUNTRY_CENTROIDS[candidate]) return COUNTRY_CENTROIDS[candidate];
    // strip trailing post-code digits
    const stripped = candidate.replace(/\d+/g, "").trim();
    if (COUNTRY_CENTROIDS[stripped]) return COUNTRY_CENTROIDS[stripped];
  }
  return null;
}

/** Upsert a MapPoint into the accumulator keyed by "lat,lng". */
function upsert(
  acc: Map<string, MapPoint>,
  latLng: [number, number],
  type: MapPoint["type"],
  entity: string,
) {
  const key = `${latLng[0].toFixed(1)},${latLng[1].toFixed(1)}`;
  const existing = acc.get(key);
  if (existing) {
    if (!existing.entities.includes(entity)) existing.entities.push(entity);
    // Promote type priority: sanctions > subsidiary > beneficial_owner > network_country
    const priority = { sanctions: 0, subsidiary: 1, beneficial_owner: 2, network_country: 3 };
    if (priority[type] < priority[existing.type]) existing.type = type;
  } else {
    acc.set(key, { lat: latLng[0], lng: latLng[1], type, entities: [entity] });
  }
}

function deriveMapPoints(results: ResultsResponse): {
  points: MapPoint[];
  unplotted: string[];
} {
  const acc = new Map<string, MapPoint>();
  const unplotted: string[] = [];
  const networkData = results.network_data as NetworkData | undefined;
  const entityName = results.entity_name;

  // 1. network_data.statistics.countries
  networkData?.statistics?.countries?.forEach((country) => {
    const ll = resolveLatLng(country);
    if (ll) upsert(acc, ll, "network_country", entityName);
  });

  // 2. network_data.nodes — company nodes with jurisdiction
  networkData?.nodes?.forEach((node) => {
    const jur = node.data.jurisdiction;
    const ll = resolveLatLng(jur);
    if (ll) upsert(acc, ll, "subsidiary", node.data.label || node.data.id);
  });

  // 3. subsidiaries
  results.subsidiaries?.forEach((sub) => {
    const ll = resolveLatLng(sub.jurisdiction);
    if (ll) upsert(acc, ll, "subsidiary", sub.name);
  });

  // 4. beneficial_owners
  results.beneficial_owners?.forEach((ubo) => {
    const ll = resolveLatLng(ubo.nationality);
    if (ll) upsert(acc, ll, "beneficial_owner", ubo.name);
  });

  // 5. sanctions addresses (best-effort country extraction)
  results.sanctions_data?.forEach((hit) => {
    if (!hit.address) return;
    const ll = extractCountryFromAddress(hit.address);
    if (ll) {
      upsert(acc, ll, "sanctions", hit.name);
    } else {
      unplotted.push(`${hit.name} — ${hit.address}`);
    }
  });

  return { points: Array.from(acc.values()), unplotted };
}

const legendStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "0.4rem",
  fontFamily: "var(--font-mono)",
  fontSize: "0.67rem",
  letterSpacing: "0.08em",
  color: "var(--text-muted)",
  textTransform: "uppercase",
};

export default function GeographicMap({ results }: GeographicMapProps) {
  const { points, unplotted } = deriveMapPoints(results);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "0.75rem",
        }}
      >
        <div>
          <div
            className="label-stamp"
            style={{ fontSize: "0.65rem", marginBottom: "0.25rem" }}
          >
            Phase Intelligence / Geographic
          </div>
          <h2
            className="font-editorial"
            style={{
              fontSize: "1.05rem",
              fontWeight: 600,
              color: "var(--text-bright)",
              margin: 0,
            }}
          >
            Geographic Footprint
          </h2>
        </div>

        {/* Legend */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
          {(Object.entries(TYPE_LABELS) as [MapPoint["type"], string][]).map(
            ([type, label]) => (
              <div key={type} style={legendStyle}>
                <span
                  style={{
                    display: "inline-block",
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: MARKER_COLORS[type],
                    flexShrink: 0,
                  }}
                />
                {label}
              </div>
            ),
          )}
        </div>
      </div>

      {points.length === 0 ? (
        <div
          style={{
            background: "var(--bg-surface)",
            border: "1px solid var(--border-dim)",
            padding: "3rem",
            textAlign: "center",
          }}
        >
          <p
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.78rem",
              color: "var(--text-muted)",
              margin: 0,
              letterSpacing: "0.06em",
            }}
          >
            No geographic data available — run a Network or Deep tier search to
            populate this map.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
          {/* Map */}
          <div
            style={{
              flex: 1,
              minWidth: 0,
              border: "1px solid var(--border-dim)",
              overflow: "hidden",
            }}
          >
            <MapContainer
              center={[20, 15]}
              zoom={2}
              minZoom={1}
              maxZoom={10}
              style={{ height: 520, width: "100%", background: "#0d1117" }}
              worldCopyJump={false}
            >
              <TileLayer
                attribution='&copy; <a href="https://carto.com">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                subdomains="abcd"
                maxZoom={19}
              />
              {points.map((pt, i) => (
                <CircleMarker
                  key={i}
                  center={[pt.lat, pt.lng]}
                  radius={pt.type === "sanctions" ? 10 : pt.type === "subsidiary" ? 8 : 7}
                  pathOptions={{
                    color: MARKER_COLORS[pt.type],
                    fillColor: MARKER_COLORS[pt.type],
                    fillOpacity: 0.75,
                    weight: 1.5,
                  }}
                >
                  <Popup>
                    <div
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: "0.72rem",
                        minWidth: 160,
                        maxWidth: 260,
                      }}
                    >
                      <div
                        style={{
                          fontSize: "0.6rem",
                          letterSpacing: "0.12em",
                          textTransform: "uppercase",
                          color: MARKER_COLORS[pt.type],
                          marginBottom: "0.4rem",
                          fontWeight: 600,
                        }}
                      >
                        {TYPE_LABELS[pt.type]}
                      </div>
                      <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
                        {pt.entities.map((e, j) => (
                          <li
                            key={j}
                            style={{
                              padding: "0.2rem 0",
                              borderBottom:
                                j < pt.entities.length - 1
                                  ? "1px solid #eee"
                                  : "none",
                              fontSize: "0.72rem",
                            }}
                          >
                            {e}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>

          {/* Unplotted addresses sidebar */}
          {unplotted.length > 0 && (
            <div
              style={{
                width: 240,
                flexShrink: 0,
                background: "var(--bg-surface)",
                border: "1px solid var(--border-dim)",
                padding: "0.875rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.5rem",
                maxHeight: 520,
                overflowY: "auto",
              }}
            >
              <div
                className="label-stamp"
                style={{ fontSize: "0.6rem", marginBottom: "0.25rem" }}
              >
                Unresolved Addresses
              </div>
              {unplotted.map((addr, i) => (
                <p
                  key={i}
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.67rem",
                    color: "var(--text-secondary)",
                    margin: 0,
                    lineHeight: 1.5,
                    borderBottom:
                      i < unplotted.length - 1
                        ? "1px solid var(--border-dim)"
                        : "none",
                    paddingBottom: i < unplotted.length - 1 ? "0.5rem" : 0,
                  }}
                >
                  {addr}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Summary line */}
      {points.length > 0 && (
        <p
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "0.67rem",
            color: "var(--text-faint)",
            margin: 0,
            letterSpacing: "0.05em",
          }}
        >
          {points.length} location{points.length !== 1 ? "s" : ""} plotted
          {unplotted.length > 0
            ? ` · ${unplotted.length} address${unplotted.length !== 1 ? "es" : ""} unresolved`
            : ""}
          {" "}· Tiles © CARTO / OSM contributors
        </p>
      )}
    </div>
  );
}
