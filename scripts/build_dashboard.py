#!/usr/bin/env python3
"""
Genera la dashboard HTML "Bacheca Bandi" a partire da bandi_inpa_tracking.json.

Uso:
    python3 scripts/build_dashboard.py \
        --tracking-file bandi_inpa_tracking.json \
        --out /tmp/bacheca_bandi.html

La dashboard è un singolo file HTML autosufficiente (font incorporati come
base64, nessuna dipendenza esterna) pensato per essere pubblicato come
Artifact ad ogni esecuzione della routine (vedi RUNBOOK.md, step 8) e
riaggiornato in-place sullo stesso URL. Lo stato "mi sono iscritto/a" vive
nel localStorage del browser dell'utente: rigenerare/ripubblicare questo
file NON cancella le iscrizioni già segnate, perché lo script incorpora solo
i dati dei bandi, non lo stato di iscrizione.
"""
import argparse
import base64
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FONTS_DIR = SCRIPT_DIR / "assets" / "fonts"


def load_font_b64(filename):
    return base64.b64encode((FONTS_DIR / filename).read_bytes()).decode("ascii")


def build_records(tracking):
    records = []
    for cid, v in tracking.get("bandi_segnalati", {}).items():
        if v.get("stato_valutazione") != "compatibile":
            continue
        link_inpa = v.get("link_inpa") or (
            "https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/"
            f"?concorso_id={cid}"
        )
        records.append(
            {
                "id": cid,
                "ente": v.get("ente") or "",
                "profilo": v.get("profilo") or "",
                "comune": v.get("comune") or "",
                "km": v.get("km"),
                "posti": v.get("posti"),
                "tempo": v.get("tempo") or "TI",
                "scadenza": v.get("scadenza"),
                "apertura": v.get("apertura"),
                "link_inpa": link_inpa,
                "link_pdf": v.get("link_pdf"),
            }
        )
    records.sort(key=lambda r: (r["scadenza"] or "9999-99-99"))
    return records


def render(records, run_date, fonts):
    html = TEMPLATE
    html = html.replace("__RUN_DATE__", json.dumps(run_date or ""))
    html = html.replace("__DATA_JSON__", json.dumps(records, ensure_ascii=False))
    html = html.replace("__FONT_PUBLIC_SANS__", fonts["public_sans"])
    html = html.replace("__FONT_BIG_SHOULDERS__", fonts["big_shoulders"])
    html = html.replace("__FONT_JETBRAINS_MONO__", fonts["jetbrains_mono"])
    return html


TEMPLATE = r"""<title>Bacheca Bandi — Paderno Dugnano</title>
<style>
@font-face {
  font-family: 'Public Sans';
  font-style: normal;
  font-weight: 380 760;
  font-display: swap;
  src: url(data:font/woff2;base64,__FONT_PUBLIC_SANS__) format('woff2');
}
@font-face {
  font-family: 'Big Shoulders';
  font-style: normal;
  font-weight: 500 900;
  font-display: swap;
  src: url(data:font/woff2;base64,__FONT_BIG_SHOULDERS__) format('woff2');
}
@font-face {
  font-family: 'JetBrains Mono';
  font-style: normal;
  font-weight: 380 620;
  font-display: swap;
  src: url(data:font/woff2;base64,__FONT_JETBRAINS_MONO__) format('woff2');
}

:root {
  --bg: #eef1ec;
  --surface: #ffffff;
  --surface-2: #e4e9e0;
  --border: #d5dbcf;
  --ink: #16232a;
  --ink-soft: #4c5b5a;
  --ink-faint: #7c8a84;
  --accent: #1f5c73;
  --accent-ink: #0f3849;
  --accent-soft: #dfebee;
  --accent-contrast: #f7fbfb;
  --good: #3f7d53;
  --good-soft: #dfeee1;
  --good-ink: #244a30;
  --warn: #a8711b;
  --warn-soft: #f3e8d3;
  --warn-ink: #5c4210;
  --critical: #ab392c;
  --critical-soft: #f5dfda;
  --critical-ink: #5c1d15;
  --muted: #8b9289;
  --muted-soft: #e8eae4;
  --shadow: 0 1px 2px rgba(22, 35, 42, 0.06), 0 8px 20px -12px rgba(22, 35, 42, 0.18);
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #10161a;
    --surface: #182027;
    --surface-2: #1d262c;
    --border: #2b353c;
    --ink: #e8edec;
    --ink-soft: #aab6b3;
    --ink-faint: #78827f;
    --accent: #6fb9d1;
    --accent-ink: #d3edf4;
    --accent-soft: #1c333b;
    --accent-contrast: #082027;
    --good: #7bc492;
    --good-soft: #1d3324;
    --good-ink: #cdedd6;
    --warn: #e3b062;
    --warn-soft: #3a2c14;
    --warn-ink: #f4dfb9;
    --critical: #e58579;
    --critical-soft: #3a1e19;
    --critical-ink: #f6d4cd;
    --muted: #71797a;
    --muted-soft: #212a2c;
    --shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 8px 24px -12px rgba(0, 0, 0, 0.5);
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #10161a;
  --surface: #182027;
  --surface-2: #1d262c;
  --border: #2b353c;
  --ink: #e8edec;
  --ink-soft: #aab6b3;
  --ink-faint: #78827f;
  --accent: #6fb9d1;
  --accent-ink: #d3edf4;
  --accent-soft: #1c333b;
  --accent-contrast: #082027;
  --good: #7bc492;
  --good-soft: #1d3324;
  --good-ink: #cdedd6;
  --warn: #e3b062;
  --warn-soft: #3a2c14;
  --warn-ink: #f4dfb9;
  --critical: #e58579;
  --critical-soft: #3a1e19;
  --critical-ink: #f6d4cd;
  --muted: #71797a;
  --muted-soft: #212a2c;
  --shadow: 0 1px 2px rgba(0, 0, 0, 0.3), 0 8px 24px -12px rgba(0, 0, 0, 0.5);
  color-scheme: dark;
}

* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: 'Public Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
  font-weight: 400;
  line-height: 1.45;
  -webkit-font-smoothing: antialiased;
}
.page {
  max-width: 640px;
  margin: 0 auto;
  padding: 0 0 3rem;
  min-height: 100dvh;
}
a { color: var(--accent); }
.tabular { font-variant-numeric: tabular-nums; }
.mono { font-family: 'JetBrains Mono', ui-monospace, Menlo, Consolas, monospace; }

/* ---------- Header ---------- */
.hero {
  padding: 1.75rem 1.25rem 1.25rem;
  border-bottom: 1px solid var(--border);
}
.hero-eyebrow {
  font-family: 'Big Shoulders', sans-serif;
  font-weight: 700;
  font-size: 0.82rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0 0 0.35rem;
}
.hero h1 {
  font-family: 'Big Shoulders', sans-serif;
  font-weight: 800;
  font-stretch: 88%;
  font-size: clamp(1.9rem, 8vw, 2.5rem);
  line-height: 0.98;
  letter-spacing: -0.01em;
  text-wrap: balance;
  margin: 0 0 0.55rem;
  color: var(--ink);
}
.hero p {
  margin: 0;
  color: var(--ink-soft);
  font-size: 0.92rem;
  max-width: 46ch;
}
.hero .updated {
  display: inline-flex;
  align-items: center;
  gap: 0.4em;
  margin-top: 0.85rem;
  font-size: 0.78rem;
  color: var(--ink-faint);
}
.hero .updated .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--good);
  flex: none;
}

/* ---------- Stats ---------- */
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: var(--border);
  border-bottom: 1px solid var(--border);
}
.stat {
  background: var(--surface);
  padding: 0.9rem 0.6rem 1rem;
  text-align: center;
}
.stat .n {
  font-family: 'Big Shoulders', sans-serif;
  font-weight: 800;
  font-size: 2rem;
  line-height: 1;
  color: var(--ink);
}
.stat.is-urgent .n { color: var(--warn); }
.stat.is-applied .n { color: var(--good); }
.stat .l {
  margin-top: 0.3rem;
  font-size: 0.68rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-faint);
}

/* ---------- Controls ---------- */
.controls {
  position: sticky;
  top: 0;
  z-index: 5;
  background: var(--bg);
  padding: 0.85rem 1.25rem 0.75rem;
  border-bottom: 1px solid var(--border);
  backdrop-filter: saturate(1.4) blur(6px);
}
.search {
  position: relative;
  margin-bottom: 0.6rem;
}
.search svg {
  position: absolute;
  left: 0.65rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--ink-faint);
  pointer-events: none;
}
.search input {
  width: 100%;
  padding: 0.6rem 0.75rem 0.6rem 2.1rem;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--ink);
  font: inherit;
  font-size: 0.9rem;
}
.search input:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
}
.chiprow {
  display: flex;
  gap: 0.4rem;
  overflow-x: auto;
  scrollbar-width: none;
  padding-bottom: 0.1rem;
}
.chiprow::-webkit-scrollbar { display: none; }
.chip {
  flex: none;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.4rem 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--ink-soft);
  cursor: pointer;
  white-space: nowrap;
}
.chip[aria-pressed="true"] {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--accent-contrast);
}
.chip:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.sortbtn {
  margin-left: auto;
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font: inherit;
  font-size: 0.8rem;
  color: var(--ink-soft);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.4rem 0.2rem;
}
.sortbtn:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; border-radius: 4px; }

/* ---------- List / Cards ---------- */
.list {
  padding: 1rem 1.25rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.card {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 1rem 1rem 0.9rem 1.1rem;
  box-shadow: var(--shadow);
  overflow: hidden;
}
.card::before {
  content: "";
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 5px;
  background: var(--stripe, var(--muted));
}
.card.is-applied { background: var(--good-soft); }
.card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.6rem;
}
.card-ente {
  font-family: 'Big Shoulders', sans-serif;
  font-weight: 700;
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0 0 0.2rem;
}
.card h2 {
  font-size: 1.05rem;
  font-weight: 650;
  line-height: 1.25;
  margin: 0;
  text-wrap: balance;
  color: var(--ink);
}
.badge {
  flex: none;
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.3rem 0.55rem;
  border-radius: 999px;
  white-space: nowrap;
}
.badge.tier-critico { background: var(--critical-soft); color: var(--critical-ink); }
.badge.tier-urgente { background: var(--warn-soft); color: var(--warn-ink); }
.badge.tier-aperto { background: var(--accent-soft); color: var(--accent-ink); }
.badge.tier-scaduto { background: var(--muted-soft); color: var(--ink-faint); }
.badge.applied { background: var(--good); color: var(--accent-contrast); }

.card-meta {
  margin-top: 0.55rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.7rem;
  font-size: 0.82rem;
  color: var(--ink-soft);
}
.card-meta span { display: inline-flex; align-items: baseline; gap: 0.3em; }
.card-meta .val { color: var(--ink); font-weight: 500; }

.card-deadline {
  margin-top: 0.7rem;
  display: flex;
  align-items: baseline;
  gap: 0.55rem;
  font-size: 0.86rem;
  color: var(--ink-soft);
}
.card-deadline .date { color: var(--ink); font-weight: 500; }

.card-actions {
  margin-top: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.btn-open {
  display: inline-flex;
  align-items: center;
  gap: 0.4em;
  font: inherit;
  font-size: 0.86rem;
  font-weight: 600;
  color: var(--accent-contrast);
  background: var(--accent);
  padding: 0.5rem 0.85rem;
  border-radius: 9px;
  text-decoration: none;
}
.btn-open:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.toggle-wrap {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.82rem;
  color: var(--ink-soft);
  cursor: pointer;
  user-select: none;
}
.toggle {
  width: 36px; height: 21px;
  border-radius: 999px;
  background: var(--border);
  border: none;
  position: relative;
  flex: none;
  cursor: pointer;
  transition: background 0.15s ease;
}
.toggle::after {
  content: "";
  position: absolute;
  top: 2px; left: 2px;
  width: 17px; height: 17px;
  border-radius: 50%;
  background: var(--surface);
  box-shadow: 0 1px 2px rgba(0,0,0,0.25);
  transition: transform 0.15s ease;
}
.toggle[aria-checked="true"] { background: var(--good); }
.toggle[aria-checked="true"]::after { transform: translateX(15px); }
.toggle:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.card-note {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px dashed var(--border);
}
.card-note label {
  display: block;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-faint);
  margin-bottom: 0.3rem;
}
.card-note textarea {
  width: 100%;
  min-height: 2.4rem;
  resize: vertical;
  font: inherit;
  font-size: 0.85rem;
  color: var(--ink);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.5rem 0.6rem;
}
.card-note textarea:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.card-note .applied-on {
  margin-top: 0.4rem;
  font-size: 0.74rem;
  color: var(--good-ink);
}

.empty {
  padding: 2.5rem 1.25rem;
  text-align: center;
  color: var(--ink-faint);
  font-size: 0.9rem;
}

/* ---------- Archive ---------- */
.archive {
  margin: 0.5rem 1.25rem 0;
  border-top: 1px solid var(--border);
  padding-top: 1rem;
}
.archive summary {
  cursor: pointer;
  font-family: 'Big Shoulders', sans-serif;
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--ink-soft);
  list-style: none;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.archive summary::-webkit-details-marker { display: none; }
.archive summary::before {
  content: "▸";
  font-size: 0.7em;
  transition: transform 0.15s ease;
}
.archive[open] summary::before { transform: rotate(90deg); }
.archive-list {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.archive-row {
  display: flex;
  justify-content: space-between;
  gap: 0.6rem;
  font-size: 0.82rem;
  color: var(--ink-faint);
  padding: 0.55rem 0.7rem;
  background: var(--surface-2);
  border-radius: 8px;
}
.archive-row .a-title { color: var(--ink-soft); }
.archive-row a { color: inherit; text-decoration: underline; }

/* ---------- Footer ---------- */
.footer {
  margin-top: 1.75rem;
  padding: 1.25rem 1.25rem 0;
  border-top: 1px solid var(--border);
}
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  font-size: 0.74rem;
  color: var(--ink-faint);
  margin-bottom: 1rem;
}
.legend span { display: inline-flex; align-items: center; gap: 0.35em; }
.legend i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.footer-actions {
  display: flex;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.btn-ghost {
  font: inherit;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--ink-soft);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 0.5rem 0.8rem;
  cursor: pointer;
}
.btn-ghost:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.footer-note {
  margin: 0.9rem 0 1.5rem;
  font-size: 0.72rem;
  color: var(--ink-faint);
  line-height: 1.5;
}
#importFile { display: none; }
.toast {
  position: fixed;
  left: 50%;
  bottom: 1.2rem;
  transform: translate(-50%, 8px);
  background: var(--ink);
  color: var(--bg);
  font-size: 0.82rem;
  padding: 0.55rem 0.9rem;
  border-radius: 999px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease, transform 0.18s ease;
  z-index: 20;
  box-shadow: var(--shadow);
}
.toast.show { opacity: 1; transform: translate(-50%, 0); }

@media (prefers-reduced-motion: reduce) {
  * { transition: none !important; }
}
</style>

<div class="page">
  <header class="hero">
    <p class="hero-eyebrow">Bacheca Bandi</p>
    <h1>Concorsi compatibili entro 20&nbsp;km da Paderno&nbsp;Dugnano</h1>
    <p>Tempo indeterminato, diploma generico (o Area Istruttori). Aggiornata in automatico dalla routine di ricerca su inPA.</p>
    <div class="updated"><span class="dot" aria-hidden="true"></span><span id="updatedLabel">—</span></div>
  </header>

  <div class="stats" id="stats">
    <div class="stat"><div class="n tabular" id="statTotal">0</div><div class="l">Aperti</div></div>
    <div class="stat is-urgent"><div class="n tabular" id="statUrgent">0</div><div class="l">Entro 7&nbsp;gg</div></div>
    <div class="stat is-applied"><div class="n tabular" id="statApplied">0</div><div class="l">Candidature</div></div>
  </div>

  <div class="controls">
    <div class="search">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><circle cx="7" cy="7" r="5.25" stroke="currentColor" stroke-width="1.4"/><path d="M11 11L14.5 14.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
      <input type="search" id="searchInput" placeholder="Cerca ente, comune, profilo…" aria-label="Cerca">
    </div>
    <div class="chiprow" role="group" aria-label="Filtri">
      <button class="chip" data-filter="tutti" aria-pressed="true">Tutti</button>
      <button class="chip" data-filter="davalutare" aria-pressed="false">Da valutare</button>
      <button class="chip" data-filter="urgenti" aria-pressed="false">Urgenti</button>
      <button class="chip" data-filter="candidato" aria-pressed="false">Candidato</button>
      <button class="sortbtn" id="sortBtn" type="button" data-sort="scadenza" aria-label="Cambia ordinamento">
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M4 6l4-4 4 4M4 10l4 4 4-4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span id="sortLabel">Scadenza</span>
      </button>
    </div>
  </div>

  <main class="list" id="list" aria-live="polite"></main>
  <p class="empty" id="emptyState" hidden>Nessun bando corrisponde ai filtri attuali.</p>

  <details class="archive" id="archiveWrap" hidden>
    <summary>Archivio — bandi compatibili scaduti</summary>
    <div class="archive-list" id="archiveList"></div>
  </details>

  <footer class="footer">
    <div class="legend">
      <span><i style="background:var(--critical)"></i>Scade entro 2&nbsp;gg</span>
      <span><i style="background:var(--warn)"></i>Entro 7&nbsp;gg</span>
      <span><i style="background:var(--accent)"></i>Aperto</span>
      <span><i style="background:var(--good)"></i>Candidatura inviata</span>
    </div>
    <div class="footer-actions">
      <button class="btn-ghost" id="exportBtn" type="button">Esporta le mie candidature</button>
      <button class="btn-ghost" id="importBtn" type="button">Importa backup</button>
      <input type="file" id="importFile" accept="application/json">
    </div>
    <p class="footer-note">Le candidature che segni qui restano salvate su questo dispositivo/browser. Usa “Esporta” per avere una copia di riserva o per portarle su un altro dispositivo con “Importa”.</p>
  </footer>
</div>

<div class="toast" id="toast" role="status" aria-live="polite"></div>

<script>
(function () {
  "use strict";
  var DATA = __DATA_JSON__;
  var RUN_DATE = __RUN_DATE__;
  var STORAGE_KEY = "bacheca-bandi-iscrizioni-v1";

  var state = {};
  try {
    var raw = localStorage.getItem(STORAGE_KEY);
    if (raw) state = JSON.parse(raw) || {};
  } catch (e) { state = {}; }

  function persist() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) {}
  }

  function todayStart() {
    var n = new Date();
    return new Date(n.getFullYear(), n.getMonth(), n.getDate());
  }

  function daysUntil(dateStr) {
    if (!dateStr) return null;
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return null;
    var target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    return Math.round((target - todayStart()) / 86400000);
  }

  function tierOf(days) {
    if (days === null) return "aperto";
    if (days < 0) return "scaduto";
    if (days <= 2) return "critico";
    if (days <= 7) return "urgente";
    return "aperto";
  }

  var itFmt = new Intl.DateTimeFormat("it-IT", { day: "numeric", month: "long", year: "numeric" });
  function formatDate(dateStr) {
    if (!dateStr) return "scadenza non indicata";
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return itFmt.format(d);
  }

  function deadlineLabel(days) {
    if (days === null) return "—";
    if (days < 0) return "Scaduto";
    if (days === 0) return "Scade oggi";
    if (days === 1) return "Scade domani";
    return "Scade tra " + days + " giorni";
  }

  var updatedEl = document.getElementById("updatedLabel");
  if (RUN_DATE) {
    var rd = new Date(RUN_DATE);
    updatedEl.textContent = "Aggiornata il " + (isNaN(rd.getTime()) ? RUN_DATE : itFmt.format(rd));
  } else {
    updatedEl.textContent = "Data aggiornamento non disponibile";
  }

  var open = DATA.filter(function (b) { return (daysUntil(b.scadenza) === null) || daysUntil(b.scadenza) >= 0; });
  var expired = DATA.filter(function (b) { var d = daysUntil(b.scadenza); return d !== null && d < 0; });

  var listEl = document.getElementById("list");
  var emptyEl = document.getElementById("emptyState");
  var archiveWrap = document.getElementById("archiveWrap");
  var archiveList = document.getElementById("archiveList");

  var currentFilter = "tutti";
  var currentSort = "scadenza";
  var currentQuery = "";

  function matchesQuery(b, q) {
    if (!q) return true;
    var hay = (b.ente + " " + b.profilo + " " + b.comune).toLowerCase();
    return hay.indexOf(q) !== -1;
  }

  function matchesFilter(b, f) {
    var s = state[b.id] || {};
    var d = daysUntil(b.scadenza);
    if (f === "davalutare") return !s.iscritto;
    if (f === "candidato") return !!s.iscritto;
    if (f === "urgenti") return d !== null && d >= 0 && d <= 7;
    return true;
  }

  function sortRecords(list) {
    var copy = list.slice();
    if (currentSort === "km") {
      copy.sort(function (a, b) {
        var ka = (a.km === null || a.km === undefined) ? Infinity : a.km;
        var kb = (b.km === null || b.km === undefined) ? Infinity : b.km;
        return ka - kb;
      });
    } else {
      copy.sort(function (a, b) {
        var da = a.scadenza || "9999";
        var db = b.scadenza || "9999";
        return da < db ? -1 : da > db ? 1 : 0;
      });
    }
    return copy;
  }

  function cardHTML(b) {
    var s = state[b.id] || {};
    var d = daysUntil(b.scadenza);
    var tier = tierOf(d);
    var applied = !!s.iscritto;
    var stripeVar = applied ? "var(--good)" : "var(--" + (tier === "critico" ? "critical" : tier === "urgente" ? "warn" : tier === "scaduto" ? "muted" : "accent") + ")";
    var metaBits = [];
    if (b.comune) metaBits.push('<span>' + esc(b.comune) + '</span>');
    if (b.km !== null && b.km !== undefined) metaBits.push('<span class="val mono">' + b.km.toFixed(1).replace(".", ",") + ' km</span>');
    if (b.posti) metaBits.push('<span class="val mono">' + b.posti + ' post' + (b.posti === 1 ? 'o' : 'i') + '</span>');
    metaBits.push('<span class="val">' + esc(b.tempo || "TI") + '</span>');

    var badge = applied
      ? '<span class="badge applied">✓ Candidato</span>'
      : '<span class="badge tier-' + tier + '">' + deadlineLabel(d) + '</span>';

    var noteBlock = applied ? (
      '<div class="card-note">' +
      '<label for="note-' + b.id + '">Appunti personali</label>' +
      '<textarea id="note-' + b.id + '" data-note="' + b.id + '" placeholder="Es. numero domanda, data prova…">' + esc(s.nota || "") + '</textarea>' +
      (s.dataIscrizione ? '<div class="applied-on">Segnato come candidato il ' + esc(s.dataIscrizione) + '</div>' : '') +
      '</div>'
    ) : "";

    return (
      '<article class="card' + (applied ? ' is-applied' : '') + '" style="--stripe:' + stripeVar + '" data-id="' + b.id + '">' +
        '<div class="card-top">' +
          '<div><p class="card-ente">' + esc(b.ente) + '</p><h2>' + esc(b.profilo || "Profilo non specificato") + '</h2></div>' +
          badge +
        '</div>' +
        '<div class="card-meta">' + metaBits.join("") + '</div>' +
        '<div class="card-deadline"><span>Scadenza</span><span class="date tabular">' + formatDate(b.scadenza) + '</span></div>' +
        '<div class="card-actions">' +
          '<a class="btn-open" href="' + esc(b.link_inpa) + '" target="_blank" rel="noopener">Apri il bando ↗</a>' +
          '<label class="toggle-wrap">' +
            '<button type="button" class="toggle" role="switch" aria-checked="' + (applied ? "true" : "false") + '" data-toggle="' + b.id + '" aria-label="Segna come candidato/a"></button>' +
            'Mi sono iscritto/a' +
          '</label>' +
        '</div>' +
        noteBlock +
      '</article>'
    );
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function render() {
    var q = currentQuery.trim().toLowerCase();
    var filtered = open.filter(function (b) { return matchesQuery(b, q) && matchesFilter(b, currentFilter); });
    filtered = sortRecords(filtered);

    listEl.innerHTML = filtered.map(cardHTML).join("");
    emptyEl.hidden = filtered.length !== 0;

    var appliedCount = open.filter(function (b) { return state[b.id] && state[b.id].iscritto; }).length;
    var urgentCount = open.filter(function (b) { var d = daysUntil(b.scadenza); return d !== null && d >= 0 && d <= 7; }).length;
    document.getElementById("statTotal").textContent = open.length;
    document.getElementById("statUrgent").textContent = urgentCount;
    document.getElementById("statApplied").textContent = appliedCount;

    if (expired.length) {
      archiveWrap.hidden = false;
      archiveList.innerHTML = sortRecords(expired).map(function (b) {
        var s = state[b.id] || {};
        return '<div class="archive-row"><span class="a-title">' + esc(b.ente) + ' — ' + esc(b.profilo) + (s.iscritto ? " · candidato" : "") + '</span><a href="' + esc(b.link_inpa) + '" target="_blank" rel="noopener">apri↗</a></div>';
      }).join("");
    }
  }

  listEl.addEventListener("click", function (ev) {
    var t = ev.target.closest("[data-toggle]");
    if (!t) return;
    var id = t.getAttribute("data-toggle");
    var s = state[id] || {};
    s.iscritto = !s.iscritto;
    if (s.iscritto && !s.dataIscrizione) {
      s.dataIscrizione = itFmt.format(new Date());
    }
    state[id] = s;
    persist();
    render();
    showToast(s.iscritto ? "Segnato come candidato/a" : "Rimosso dai candidati");
  });

  listEl.addEventListener("change", function (ev) {
    var t = ev.target.closest("[data-note]");
    if (!t) return;
    var id = t.getAttribute("data-note");
    var s = state[id] || {};
    s.nota = t.value;
    state[id] = s;
    persist();
  });

  document.querySelectorAll(".chip[data-filter]").forEach(function (chip) {
    chip.addEventListener("click", function () {
      currentFilter = chip.getAttribute("data-filter");
      document.querySelectorAll(".chip[data-filter]").forEach(function (c) {
        c.setAttribute("aria-pressed", c === chip ? "true" : "false");
      });
      render();
    });
  });

  var sortBtn = document.getElementById("sortBtn");
  var sortLabel = document.getElementById("sortLabel");
  sortBtn.addEventListener("click", function () {
    currentSort = currentSort === "scadenza" ? "km" : "scadenza";
    sortLabel.textContent = currentSort === "scadenza" ? "Scadenza" : "Distanza";
    render();
  });

  document.getElementById("searchInput").addEventListener("input", function (ev) {
    currentQuery = ev.target.value;
    render();
  });

  var toastEl = document.getElementById("toast");
  var toastTimer = null;
  function showToast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove("show"); }, 2200);
  }

  function backupPayload() {
    return JSON.stringify({ tipo: "bacheca-bandi-backup", versione: 1, esportato_il: new Date().toISOString(), stato: state }, null, 2);
  }

  document.getElementById("exportBtn").addEventListener("click", function () {
    var data = backupPayload();
    var filename = "bacheca-bandi-backup.json";
    if (window.claude && window.claude.downloads && window.claude.downloads.save) {
      window.claude.downloads.save({ filename: filename, data: data })
        .then(function () { showToast("Backup esportato"); })
        .catch(function () { showToast("Esportazione annullata"); });
      return;
    }
    try {
      var blob = new Blob([data], { type: "application/json" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url; a.download = filename;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      showToast("Backup esportato");
    } catch (e) { showToast("Esportazione non riuscita"); }
  });

  var importFile = document.getElementById("importFile");
  document.getElementById("importBtn").addEventListener("click", function () { importFile.click(); });
  importFile.addEventListener("change", function () {
    var file = importFile.files && importFile.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var parsed = JSON.parse(String(reader.result));
        var incoming = parsed && parsed.stato ? parsed.stato : parsed;
        if (incoming && typeof incoming === "object") {
          Object.keys(incoming).forEach(function (id) { state[id] = incoming[id]; });
          persist();
          render();
          showToast("Backup importato");
        } else {
          showToast("File non valido");
        }
      } catch (e) {
        showToast("File non valido");
      }
      importFile.value = "";
    };
    reader.readAsText(file);
  });

  render();
})();
</script>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracking-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-date", default=None)
    args = ap.parse_args()

    tracking = json.loads(Path(args.tracking_file).read_text())
    records = build_records(tracking)
    run_date = args.run_date or tracking.get("ultima_esecuzione") or ""

    fonts = {
        "public_sans": load_font_b64("public-sans-variable.woff2"),
        "big_shoulders": load_font_b64("big-shoulders-variable.woff2"),
        "jetbrains_mono": load_font_b64("jetbrains-mono-variable.woff2"),
    }

    html = render(records, run_date, fonts)
    Path(args.out).write_text(html, encoding="utf-8")
    print(f"Dashboard generata: {args.out} ({len(records)} bandi compatibili)")


if __name__ == "__main__":
    main()
