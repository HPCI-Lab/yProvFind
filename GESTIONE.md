# Gestione di yProvFind senza endpoint esposti

## 1. Note generali e requisiti di indicizzazione
- **Modulo LLM disattivato:** in questa configurazione di `yprovfind`, le chiamate al modello linguistico (LLM) sono disattivate per impostazione predefinita a causa della non disponibilità degli endpoint dedicati.
- **Criteri di indicizzazione:** in assenza del modulo LLM, `yprovfind` indicizza un documento soltanto se risulta valorizzato con parole complete in almeno uno dei seguenti campi:
  - titolo
  - descrizione
  - keywords
- **Documenti non indicizzabili:** i documenti privi di contenuto testuale nei campi sopra indicati vengono scartati e non indicizzati.

## 2. Avvio del servizio
Per compilare l'immagine e avviare i servizi definiti in Docker Compose, eseguire dalla directory del progetto:

```bash
docker compose build
docker compose up -d
```

## 3. Configurazione dell'intervallo dello scheduler
Per definire la frequenza (in minuti) con cui lo scheduler periodico interroga le istanze registrate per acquisire nuovi dati, modificare il parametro `SCHEDULER_INTERVAL_MINUTES` all'interno del file `src/settings.py`:

```python
SCHEDULER_INTERVAL_MINUTES: int = 20
```

Dopo la modifica del file `src/settings.py`, è necessario riavviare o ricreare il container `yprovfind2.0` affinché la nuova configurazione venga applicata.

## 4. Gestione delle istanze `yprovstore`
Quando il container di `yprovfind` è in esecuzione, viene resa disponibile tramite bind mount la directory `controlFiles` nella stessa cartella del file `docker-compose.yml`. All'interno di tale directory si trova il file `registryList.json` (da creare manualmente con questo nome qualora non fosse presente), che elenca le istanze `yprovstore` da interrogare.

Formato per una singola istanza:

```json
{
  "https://example.com": {
    "institution": "opzionale",
    "city": "opzionale",
    "country": "opzionale"
  }
}
```

Formato per più istanze:

```json
{
  "http://example.com": {
    "institution": "opzionale",
    "city": "opzionale",
    "country": "opzionale"
  },
  "http://hpc4ds.unitn.it:8022": {
    "institution": "unitn",
    "city": "Trento",
    "country": "Italia"
  }
}
```

- **Sintassi degli URL:** in presenza di rete VPN utilizzare il protocollo `http://` anziché `https://` ed evitare il carattere `/` finale dopo il numero di porta.
- **Aggiornamento automatico:** le modifiche a `registryList.json` vengono recepite automaticamente a ogni avvio del ciclo di indicizzazione, senza necessità di riavviare il servizio.

## 5. Gestione del timestamp di ultima sincronizzazione (`last_fetch.json`)
Il file `controlFiles/last_fetch.json` registra, per ciascuna istanza `yprovstore`, il timestamp dell'ultima sincronizzazione completata con esito positivo:

```json
{
  "http://127.0.0.1:8000": "2026-11-23T14:37:43.675803+00:00",
  "http://hpc4ds.unitn.it:8022": "2026-11-23T14:37:43.675803+00:00"
}
```

A seconda dell'esigenza operativa, è possibile intervenire come segue:
- **Ripresa da una data specifica:** aggiornare il valore di timestamp associato all'istanza interessata con la data e l'ora desiderate.
- **Ripresa dal primo documento di una singola istanza:** rimuovere la voce corrispondente a quella specifica istanza.
- **Ripresa dal primo documento per tutte le istanze:** azzerare o rimuovere il contenuto del file, in modo che `yprovfind` richieda i dati dall'inizio per tutte le istanze configurate.

## 6. Reset dei documenti nell'indice Elasticsearch
Per eliminare tutti i documenti presenti nell'indice configurato mantenendo intatta la struttura dell'indice stesso, eseguire il comando seguente da una shell `bash` sull'host:

```bash
docker exec -i yprovfind2.0 uv run python - << 'EOF'
import asyncio
from settings import settings
from services.elasticSearch.connection.es_connection import ElasticSearchConnection
from services.elasticSearch.delete_documents.delete_documents import DeleteDocuments


async def main():
    conn = ElasticSearchConnection()
    await conn.connect()
    try:
        if conn.client is None:
            raise RuntimeError("Connessione a Elasticsearch non riuscita")
        deleter = DeleteDocuments(conn)
        res = await deleter.delete_all_docuemnts_in_index(settings.INDEX_NAME)
        print(res)
    finally:
        await conn.close()


asyncio.run(main())
EOF
```

L'operazione viene eseguita all'interno del container `yprovfind2.0`, che comunica con Elasticsearch attraverso la rete interna `elastic-network` utilizzando le credenziali e la logica di connessione già configurate, senza esporre porte sull'host né attivare endpoint HTTP esterni.

## 7. Configurazione della dimensione del batch di elaborazione
`yprovfind` elabora più documenti in parallelo per ottimizzare il throughput. Per modificare il numero di documenti elaborati simultaneamente, aprire il file `src/settings.py` e aggiornare il parametro `BATCH_SIZE` con il valore desiderato:

```python
BATCH_SIZE: int = 10
```

Dopo aver salvato la modifica, è necessario riavviare o ricreare il container `yprovfind2.0` affinché il nuovo valore venga applicato.