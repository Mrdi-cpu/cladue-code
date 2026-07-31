#!/usr/bin/env python3
"""
Applica un elenco di decisioni (nuove o aggiornate) al file di tracking.

Uso:
    python3 merge_tracking.py --tracking-file bandi_inpa_tracking.json \
        --new-entries /tmp/new_entries.json --run-date 2026-07-31

new_entries.json e' una lista di oggetti, ciascuno con almeno:
    concorso_id, stato_valutazione
e idealmente anche: ente, profilo, comune, km, posti, tempo, apertura,
scadenza, titolo_richiesto, valutazione, link_inpa, link_pdf.

--run-date va passato esplicitamente (niente datetime.now() nello script:
la data la conosce gia' l'agente dal contesto della conversazione/sistema).
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracking-file", required=True)
    ap.add_argument("--new-entries", required=True)
    ap.add_argument("--run-date", required=True)
    args = ap.parse_args()

    tp = Path(args.tracking_file)
    doc = {"bandi_segnalati": {}}
    if tp.exists():
        doc = json.loads(tp.read_text())
        doc.setdefault("bandi_segnalati", {})

    new_entries = json.loads(Path(args.new_entries).read_text())
    added, updated = 0, 0
    for entry in new_entries:
        cid = str(entry["concorso_id"])
        entry["ultimo_controllo"] = args.run_date
        if cid in doc["bandi_segnalati"]:
            entry["prima_rilevazione"] = doc["bandi_segnalati"][cid].get(
                "prima_rilevazione", args.run_date
            )
            updated += 1
        else:
            entry["prima_rilevazione"] = args.run_date
            added += 1
        doc["bandi_segnalati"][cid] = entry

    doc["ultima_esecuzione"] = args.run_date
    tp.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"Tracking aggiornato: {added} nuovi, {updated} aggiornati. Totale: {len(doc['bandi_segnalati'])}")


if __name__ == "__main__":
    main()
