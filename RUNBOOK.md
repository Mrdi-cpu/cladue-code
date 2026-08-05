# Routine bandi inPA — Paderno Dugnano (versione cloud)

Questo e' il nuovo testo da usare come prompt del task schedulato (sostituisce
quello che apriva un browser). Presuppone che l'ambiente sia stato creato con
questo repo collegato (vedi step-by-step separato) e che la network policy
permetta `portale.inpa.gov.it` e `nominatim.openstreetmap.org`.

## Criteri (invariati rispetto alla versione precedente)

- Origine: Paderno Dugnano (MI), raggio 20km reale (Haversine su geocoding
  Nominatim), con l'eccezione "Nazionale -> verifica sede assegnabile a
  Milano/MB nel PDF".
- Profili: istruttore/assistente/operatore amministrativo, assistente
  documentale/gestionale, servizi demografici, URP, servizi culturali,
  agente di polizia locale, assistente giudiziario, ATA (solo diploma),
  assistente amministrativo enti pubblici (solo se il bando specifico
  richiede solo diploma, non laurea).
- Categoria inPA "Concorso", regione Lombardia, stato Aperto, contratto
  SOLO Tempo Indeterminato.
- Titolo di studio: SOLO diploma generico. Area Istruttori (ex Cat. C) va
  bene di default; Area Funzionari/EQ o Istruttore Direttivo richiede
  APERTURA DEL PDF per verificare puntualmente (quasi sempre laurea, ma va
  controllato bando per bando).
- Escludi sempre: interpello/mobilita', manifestazione di interesse,
  stabilizzazione/progressione interna, bandi revocati.

## Procedura

1. `cd` nella working copy del repo (gia' clonato dall'ambiente) ed esegui
   `git pull` per essere sicuro di partire dal tracking piu' recente.

2. Esegui:
   ```
   python3 scripts/fetch_bandi.py \
     --tracking-file bandi_inpa_tracking.json \
     --geocode-cache geocode_cache.json \
     --out /tmp/bandi_report.json
   ```
   Lo script fa TUTTO il lavoro meccanico via chiamate dirette (niente
   browser: da server-side CORS non e' un problema): ricerca su tutti i
   termini, dedup, filtro TI/TD, filtro mobilita', filtro raggio 20km (con
   scorciatoia sulle province lontane), e incrocio con il tracking esistente
   per saltare cio' che e' gia' stato classificato in run precedenti.

   Se lo script termina con `ERRORE FATALE` o con `search_errors` non vuoto,
   e' quasi certamente un problema di rete (dominio non raggiungibile) — non
   proseguire con dati parziali, segnala il problema.

3. Leggi `/tmp/bandi_report.json`. Contiene questi bucket:
   - `nuovi_compatibili_auto`: Area Istruttori, entro 20km, TI, nuovi.
     Compatibili per default, ma dai un'occhiata al `profilo`/titolo per
     scartare eventuali indirizzi di diploma specifici sfuggiti all'euristica
     dello script.
   - `da_verificare_pdf`: Area Funzionari/EQ (o non classificabile dal solo
     titolo), entro 20km, TI, nuovi. **Vanno aperti i PDF uno per uno.**
   - `da_verificare_nazionale`: sede "Nazionale", TI, nuovi. **Vanno aperti
     i PDF/dettagli per controllare se tra le sedi assegnabili c'e' Milano o
     provincia di Milano/Monza-Brianza.**
   - `gia_segnalati_aperti_compatibili`: gia' noti e compatibili, ancora
     aperti — vanno solo nella seconda tabella di output.
   - `esclusi`: esclusioni automatiche deterministiche, pronte per il
     tracking cosi' come sono.
   - `errori`: casi da NON scrivere nel tracking (verranno ririprovati al
     prossimo giro) — se sono tanti, segnalalo, potrebbe indicare che il
     parsing del campo `sedi` va aggiustato (vedi commento in testa allo
     script).

4. Per ogni bando in `da_verificare_pdf` e `da_verificare_nazionale`:
   scarica il PDF (`curl -sS -L -o /tmp/bando_<id>.pdf <link_pdf>`), poi
   usa il tool Read su quel path locale per estrarre il testo. Cerca la
   sezione "Titolo di studio" / "Requisiti per l'ammissione" (e, per i
   nazionali, l'elenco delle sedi/posti per provincia). Decidi:
   - compatibile (diploma generico sufficiente, e per i nazionali: sede a
     Milano/MB tra quelle assegnabili)
   - escluso_laurea_obbligatoria
   - escluso_diploma_indirizzo_specifico
   - escluso_fuori_raggio (per i nazionali senza sede Milano/MB)

5. Costruisci `/tmp/new_entries.json`: una lista con TUTTI i bandi processati
   in questo run (i tre bucket "nuovi"/"da verificare" con lo
   stato_valutazione deciso, piu' tutto il bucket `esclusi` cosi' com'e' —
   NON includere `gia_segnalati_aperti_compatibili` ne' `errori`). Ogni
   oggetto deve avere: concorso_id, stato_valutazione, ente, profilo,
   comune, km, posti, tempo, apertura, scadenza, titolo_richiesto,
   valutazione, link_inpa, link_pdf.

6. Esegui:
   ```
   python3 scripts/merge_tracking.py \
     --tracking-file bandi_inpa_tracking.json \
     --new-entries /tmp/new_entries.json \
     --run-date <data odierna in formato YYYY-MM-DD>
   ```

7. Commit e push:
   ```
   git add bandi_inpa_tracking.json geocode_cache.json
   git commit -m "Aggiornamento bandi inPA <data>"
   git push
   ```

8. Output all'utente secondo il formato gia' concordato in precedenza (due
   tabelle: nuovi compatibili, poi gia' segnalati ancora aperti; oppure
   messaggio breve se non c'e' nulla di nuovo) + riepilogo statistiche.
   OGNI riga di OGNI tabella DEVE includere il link diretto al bando
   (`link_inpa`), non solo ente/profilo/comune/km/scadenza: senza il link
   l'utente non puo' aprire il bando, quindi non e' un dettaglio omissibile.

9. Se questa e' un'esecuzione schedulata automatica (nessuno sta guardando
   la sessione dal vivo) e sono stati trovati bandi NUOVI compatibili,
   manda una notifica push con il riepilogo. Se non c'e' nulla di nuovo,
   resta in silenzio.
