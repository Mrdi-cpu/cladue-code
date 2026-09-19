#!/usr/bin/env python3
"""
Fetch + dedupe + geo-filter inPA bandi per il profilo Paderno Dugnano.
Nessuna dipendenza da browser: le chiamate sono dirette (server-side), quindi
niente problemi di CORS. Richiede solo che il dominio portale.inpa.gov.it e
nominatim.openstreetmap.org siano raggiungibili dalla rete dell'ambiente.

Uso:
    python3 fetch_bandi.py --tracking-file bandi_inpa_tracking.json \
        --geocode-cache geocode_cache.json --out bandi_report.json

Il file di output (bandi_report.json) contiene bucket gia' pronti per essere
processati dall'agente:
  - nuovi_compatibili_auto : Area Istruttori, entro 20km, TI, non ancora in
        tracking -> compatibili salvo verifica finale del titolo di studio
  - da_verificare_pdf      : Area Funzionari/EQ o non classificabile dal solo
        titolo, entro 20km, TI, non ancora in tracking -> va aperto il PDF
  - da_verificare_nazionale: sede "Nazionale", TI, non ancora in tracking ->
        va aperto il PDF/dettaglio per controllare le sedi assegnabili
  - gia_segnalati_aperti_compatibili : gia' in tracking come "compatibile" e
        ancora aperti -> vanno solo nella tabella promemoria
  - esclusi                : esclusioni automatiche deterministiche (TD,
        mobilita'/stabilizzazione, fuori raggio, diploma di indirizzo
        specifico riconosciuto nel titolo) -> pronte per essere scritte nel
        tracking cosi' come sono
  - errori                 : problemi da rivedere a mano (geocoding fallito,
        campo sedi non parsabile, chiamata di ricerca fallita) -> NON
        scrivere nel tracking, vanno rianalizzati al prossimo giro

IMPORTANTE - avvertenza sul parsing di `sedi`: la struttura esatta del campo
`sedi` restituito dall'API non e' stata verificata contro l'endpoint reale
(il dominio era bloccato dalla policy di rete nell'ambiente in cui questo
script e' stato scritto). Il parsing sotto assume che ogni elemento di `sedi`
sia una stringa tipo "Comune (PR)" o semplicemente "Comune"/"Nazionale". Al
primo run reale, se il conteggio di `errori` e' anomalo, ispeziona
bandi_report.json -> errori[].raw_sedi e aggiusta la funzione parse_sede().
"""
import argparse
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_URL = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/search-better"
CATEGORIA_ID = "8d70df1b4bca4904b3a4"
REGIONE_ID = "9"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "bandi-inpa-tracker/1.0 (uso personale, contatto: d.agata.d@gmail.com)"
PADERNO_DUGNANO_QUERY = "Paderno Dugnano"
RADIUS_KM = 20.0
NOMINATIM_MIN_INTERVAL_S = 1.1  # rispetta la usage policy di Nominatim (max 1 req/s)

SEARCH_TERMS = [
    "polizia locale", "amministrativo", "amministrativi", "documentale",
    "gestionale", "demografici", "anagrafe", "URP", "culturali", "giudiziario",
]

# Province il cui comune di confine piu' vicino a Paderno Dugnano e' comunque
# oltre i 20km (verificato empiricamente nelle esecuzioni precedenti della
# routine). Per queste si salta la geocodifica individuale.
SKIP_GEOCODE_PROVINCES = {"BG", "BS", "CR", "LO", "MN", "SO"}
# MI, MB, VA, CO, LC, PV vanno SEMPRE geocodificate individualmente.

EXCLUDE_TITLE_PATTERNS = [
    r"\binterpell\w*",
    r"\bmobilit[aà]\b",
    r"manifestazion\w+ di interesse",
    r"\bstabilizzazion\w*",
    r"progression\w+ (economic\w*|intern\w*|riservat\w*)",
    r"\brevocat[oa]\b",
    r"\bavviso oiv\b",
    r"\bformez\b",
]

# Riconoscimento (euristico, solo dal titolo) di diploma di indirizzo specifico
# richiesto -> escludi senza bisogno di aprire il PDF.
SPECIFIC_DIPLOMA_PATTERNS = [
    r"diploma (di )?ragioneria",
    r"diploma (tecnico|di perito)",
    r"diploma (di )?geometra",
    r"indirizzo (tecnico|commerciale|amministrazione finanza e marketing)",
]

AREA_FUNZIONARI_PATTERNS = [
    r"funzionari", r"istruttore direttivo", r"categoria d\b", r"area d\b",
    r"elevata qualificazion",
]


def http_post_json(url, payload, timeout=30):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, method="GET")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_bandi(text):
    payload = {
        "text": text, "categoriaId": CATEGORIA_ID, "regioneId": REGIONE_ID,
        "status": ["OPEN"], "settoreId": None, "provinciaCodice": None,
        "dateFrom": None, "dateTo": None, "livelliAnzianitaIds": None,
        "tipoImpiegoId": None, "salaryMin": None, "salaryMax": None,
        "enteRiferimentoName": None,
    }
    all_content = []
    page = 0
    while True:
        resp = http_post_json(f"{API_URL}?page={page}&size=100", payload)
        data = resp.get("data", resp)
        content = data.get("content", [])
        all_content.extend(content)
        total = data.get("totalElements", len(content))
        if len(all_content) >= total or not content:
            break
        page += 1
    return all_content


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_json(path, default):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text())
    return default


def geocode(place, cache, cache_path, state):
    key = place.strip().lower()
    if key in cache:
        return cache[key]
    coord = None
    last_err = None
    for attempt in range(4):
        if state["last_call"] is not None:
            elapsed = time.monotonic() - state["last_call"]
            if elapsed < NOMINATIM_MIN_INTERVAL_S:
                time.sleep(NOMINATIM_MIN_INTERVAL_S - elapsed)
        try:
            q = urllib.parse.quote(place)
            results = http_get_json(
                f"{NOMINATIM_URL}?q={q},Italy&format=json&limit=1&countrycodes=it",
                headers={"User-Agent": USER_AGENT},
            )
            state["last_call"] = time.monotonic()
            if results:
                coord = {"lat": float(results[0]["lat"]), "lon": float(results[0]["lon"])}
            break
        except urllib.error.HTTPError as e:
            state["last_call"] = time.monotonic()
            last_err = e
            if e.code == 429 and attempt < 3:
                time.sleep(2.0 * (attempt + 1))
                continue
            print(f"WARN geocoding fallito per '{place}': {e}", file=sys.stderr)
            break
        except Exception as e:
            last_err = e
            print(f"WARN geocoding fallito per '{place}': {e}", file=sys.stderr)
            break
    if coord is not None:
        # Non mettiamo in cache i fallimenti: potrebbero essere transitori
        # (es. rate limit Nominatim) e vogliamo ritentare al prossimo giro.
        cache[key] = coord
        Path(cache_path).write_text(json.dumps(cache, ensure_ascii=False, indent=2))
    return coord


def detect_ti_td(text):
    t = text.lower()
    if "tempo indeterminato" in t:
        return "TI"
    if "tempo determinato" in t:
        return "TD"
    return None


def matches_any(patterns, text):
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def parse_sede(raw):
    """Ritorna (comune_o_none, provincia_sigla_o_none, is_nazionale)."""
    s = str(raw).strip()
    if not s:
        return None, None, False
    if "nazional" in s.lower():
        return None, None, True
    m = re.search(r"\(([A-Za-z]{2})\)\s*$", s)
    provincia = m.group(1).upper() if m else None
    comune = re.sub(r"\([A-Za-z]{2}\)\s*$", "", s).strip()
    return comune or s, provincia, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracking-file", required=True)
    ap.add_argument("--geocode-cache", default="geocode_cache.json")
    ap.add_argument("--out", default="bandi_report.json")
    args = ap.parse_args()

    tracking_doc = load_json(args.tracking_file, {"bandi_segnalati": {}})
    tracking = tracking_doc.get("bandi_segnalati", {})

    cache = load_json(args.geocode_cache, {})
    geostate = {"last_call": None}
    origin = geocode(PADERNO_DUGNANO_QUERY, cache, args.geocode_cache, geostate)
    if not origin:
        print("ERRORE FATALE: impossibile geocodificare Paderno Dugnano. Interrompo.", file=sys.stderr)
        sys.exit(2)

    all_bandi = {}
    search_errors = []
    for term in SEARCH_TERMS:
        try:
            for item in search_bandi(term):
                iid = str(item.get("id"))
                if iid and iid != "None":
                    all_bandi[iid] = item
        except Exception as e:
            search_errors.append({"term": term, "error": str(e)})

    report = {
        "totale_univoci": len(all_bandi),
        "search_errors": search_errors,
        "nuovi_compatibili_auto": [],
        "da_verificare_pdf": [],
        "da_verificare_nazionale": [],
        "gia_segnalati_aperti_compatibili": [],
        "esclusi": [],
        "errori": [],
    }

    for cid, item in all_bandi.items():
        titolo = item.get("titolo") or ""
        figura = item.get("figuraRicercata") or ""
        descr = item.get("descrizioneBreve") or ""
        full_text = f"{titolo} {figura} {descr}"

        base = {
            "concorso_id": cid,
            "ente": ", ".join(item.get("entiRiferimento") or []) or None,
            "profilo": figura or titolo,
            "posti": item.get("numPosti"),
            "valutazione": item.get("tipoProcedura"),
            "apertura": item.get("dataPubblicazione"),
            "scadenza": item.get("dataScadenza"),
            "link_inpa": f"https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/?concorso_id={cid}",
            "link_pdf": (f"https://portale.inpa.gov.it/api/media/{item['allegatoMediaId']}"
                         if item.get("allegatoMediaId") else None),
            "raw_sedi": item.get("sedi"),
        }

        # Bando gia' processato in un run precedente: salta tutto il lavoro
        # pesante (geocoding/PDF) e limitati a controllare se e' ancora aperto.
        prev = tracking.get(cid)
        if prev:
            if prev.get("stato_valutazione") == "compatibile":
                base["comune"] = prev.get("comune")
                base["km"] = prev.get("km")
                base["tempo"] = "TI"
                base["titolo_richiesto"] = prev.get("titolo_richiesto")
                report["gia_segnalati_aperti_compatibili"].append(base)
            # se escluso_*, non serve fare nulla: resta escluso per sempre
            continue

        if matches_any(EXCLUDE_TITLE_PATTERNS, full_text):
            base["stato_valutazione"] = "escluso_avviso_mobilita"
            report["esclusi"].append(base)
            continue

        tempo = detect_ti_td(full_text)
        if tempo != "TI":
            base["stato_valutazione"] = "escluso_TD"
            report["esclusi"].append(base)
            continue
        base["tempo"] = "TI"

        if matches_any(SPECIFIC_DIPLOMA_PATTERNS, full_text):
            base["stato_valutazione"] = "escluso_diploma_indirizzo_specifico"
            report["esclusi"].append(base)
            continue

        sedi_raw = item.get("sedi") or []
        if not sedi_raw:
            base["errore"] = "campo sedi vuoto/assente"
            report["errori"].append(base)
            continue

        parsed = [parse_sede(s) for s in sedi_raw]
        if any(nazionale for _, _, nazionale in parsed):
            report["da_verificare_nazionale"].append(base)
            continue

        # Il campo 'sedi' reale include spesso il nome della regione
        # ("Lombardia") come uno degli elementi (non sempre in prima
        # posizione). Va scartato: non e' un comune/provincia utile alla
        # geocodifica, e prenderlo per buono produce sempre la stessa
        # distanza fittizia (~47km) causando falsi "fuori raggio".
        specifiche = [(c, p) for c, p, _ in parsed if c and c.strip().lower() != "lombardia"]
        if not specifiche:
            base["errore"] = f"nessuna sede specifica (solo regione) in sedi: {sedi_raw!r}"
            report["errori"].append(base)
            continue

        comune, provincia = specifiche[0]
        if provincia in SKIP_GEOCODE_PROVINCES:
            base["comune"] = comune
            base["km"] = None
            base["stato_valutazione"] = "escluso_fuori_raggio"
            report["esclusi"].append(base)
            continue

        if not comune:
            base["errore"] = f"comune non estraibile da sedi: {sedi_raw!r}"
            report["errori"].append(base)
            continue

        coord = geocode(comune, cache, args.geocode_cache, geostate)
        if not coord:
            base["errore"] = f"geocoding fallito per comune '{comune}'"
            report["errori"].append(base)
            continue

        km = round(haversine_km(origin["lat"], origin["lon"], coord["lat"], coord["lon"]), 1)
        base["comune"] = comune
        base["km"] = km

        if km > RADIUS_KM:
            base["stato_valutazione"] = "escluso_fuori_raggio"
            report["esclusi"].append(base)
            continue

        if matches_any(AREA_FUNZIONARI_PATTERNS, full_text):
            report["da_verificare_pdf"].append(base)
        else:
            report["nuovi_compatibili_auto"].append(base)

    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(
        f"OK: {len(all_bandi)} bandi univoci. "
        f"nuovi_compatibili_auto={len(report['nuovi_compatibili_auto'])} "
        f"da_verificare_pdf={len(report['da_verificare_pdf'])} "
        f"da_verificare_nazionale={len(report['da_verificare_nazionale'])} "
        f"gia_segnalati_aperti={len(report['gia_segnalati_aperti_compatibili'])} "
        f"esclusi={len(report['esclusi'])} errori={len(report['errori'])} "
        f"search_errors={len(search_errors)}"
    )


if __name__ == "__main__":
    main()
