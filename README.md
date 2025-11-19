
# **yProvFind**


## Table of Content
- [Overview](#overview)
- [Deployment with Docker](#running-yprovfind-with-docker)
- [yProvFind CLI](#yprovfind-cli)


## **Overview**
**yProvFind** is a search engine designed to discover and manage *provenance* records coming from **yProvStore** services distributed worldwide.
The system allows provenance search through **structured metadata** (title, description, keywords, author, PID), providing a **hybrid search mechanism** that combines:

* **Full-text search**, powered by *Elasticsearch*, for traditional keyword-based queries.
* **Semantic search**, supported by an *embedding model* that merges the title, description, and keywords fields to capture conceptual relationships between contents.

The architecture is built with **FastAPI** (running on *Uvicorn*), exposing REST endpoints to interact with the search engine.

Moreover, **yProvFind** will be able to maintain an up-to-date **STAC (SpatioTemporal Asset Catalog)** containing all indexed provenance records, enabling integration and federation with external services.
This functionality is currently under development.

### **Search methods**
#### 1. Research full-text 
It analyzes and tokenizes text by eliminating stop words (conjunctions, etc.) to compare query words with indexed terms, calculating the relevance of results using the BM25 scoring. It is useful for keyword-based searches and text relevance

#### 2. Semantic search 
It uses vector representations (embeddings) of sentences and documents to compare meanings rather than exact words, calculating similarity using functions such as cosine similarity. The embedding is performed by Hugging Face's all-MiniLM-L6-v2 model, which generates a vector of 384 features.

#### 3. Hybrid search 
It combines text and semantic matching: Elasticsearch runs both searches in parallel and calculates an overall score that takes into account both keywords and meaning.

#### 4. KNN Search with HNSW
This search method uses the Hierarchical Navigable Small World (HNSW) algorithm to efficiently find the vectors most similar to the query vector in the semantic_embedding field. The query embedding is then computed and compared with those indexed via approximate k-nearest neighbor (KNN) search, reducing the number of direct comparisons thanks to the hierarchical structure of the HNSW graph. In parallel, a textual bool query (with multi-match on fields such as title, description, etc.) filters and refines the results, combining vector search and textual criteria. This approach guarantees high efficiency on large datasets, maintaining good accuracy, and can exploit early termination strategies to stop the graph traversal early when the results are already sufficiently good.



## **Running yProvFind with Docker**

The project includes a `docker-compose.yml` file that defines all required services to run **yProvFind** and its dependencies.
The setup consists of two containers:

* **yProvFind** – the main application built from this repository.
* **Elasticsearch** – pulled automatically from Docker Hub (`docker.elastic.co/elasticsearch/elasticsearch:9.0.3`).

### **1. Requirements**

* **Docker** and **Docker Compose** must be installed on your system.

  * On **desktop environments** (Windows, macOS, Linux), simply install from the official website and start **Docker Desktop**.
 

### **2. Create the .env file**

Before starting the containers, you **must** create a `.env` file in the root directory of the project. This file contains the credentials needed to connect the `yProvFind` container to Elasticsearch.

**Important:** At first startup, Elasticsearch sets the username and password based on the values in this file. If the `.env` file is not created beforehand, Elasticsearch will generate random credentials automatically, making the connection impossible.

Create a file named `.env` in the project root with the following content:

```env
ELASTICSEARCH_URL=http://localhost:9200
ES_USER=elastic
ES_PASSWORD=password
```

> **Note:** You can customize the `ES_USER` and `ES_PASSWORD` value for better security. 



### **3. Build the images**

From the root of the repository, run:

```bash
docker compose build
```

This command builds the **yProvFind** image using the local `Dockerfile`, while pulling the official **Elasticsearch** image from Docker Hub.

### **4. Start the services**

To start the full stack:

```bash
docker compose up
```

This launches both containers and attaches their logs to your terminal.
If you prefer to run them in the background:

```bash
docker compose up -d
```

Once running, **yProvFind** will expose its **FastAPI** endpoints (check the `docker-compose.yml` for the configured port, right now it should be 8002), and **Elasticsearch** will be available internally for indexing and search operations.

### **5. Access the API docs:**
Open http://localhost:8002/docs in your browser.

### **6. Access the CLI**

Once **yprovfind** is fully started, you can interact with it directly from any terminal on your machine.  
To view all available commands, run:

```bash
docker exec yprovfind ypfind --help
```

### **7. Stop and clean up**

To stop and remove all running containers, networks, and temporary data:

```bash
docker compose down
```



## **yProvFind CLI**
The command-line interface is installed automatically inside the **yprovfind** container.
To use it, all commands must be prefixed with:

```
docker exec yprovfind
```

This prefix is required because the CLI runs inside the container rather than on the host system.

You can run these commands from **any terminal**, as long as:

1. Docker Desktop is running.
2. The `yprovfinddocker` environment is fully started (this includes both the `elasticsearch` container and the `yprovfind` container).

Once these conditions are met, you can execute any CLI command. 
### **All commands**
The prefix **docker exec yprovfind** must be added to each command
```
ypfind start-index
ypfind registry list 
ypfind registry add <address>
ypfind registry delete <address>
ypfind search <query> [--date-from <DD-MM-YYYY>]  [--date-to <DD-MM-YYYY>] [--version <version_number>] [--instance <url>] [--other-versions / --no-other-versions] [--limit <page_size>]
ypfind tmstamp list
ypfind tmstamp delete <address>
ypfind demo start
ypfind demo end

```


### **1. General**
To list all available options:
```
docker exec yprovfind ypfind --help
```
### **2. Start the indexing process**
In order to manually start the indexing process you can type:
```
docker exec yprovfind ypfind start-index
```
The process checks the yProvStore instances in the registry list. For each active instance, it looks at the last timestamp—the time it was last queried to retrieve provenance metadata—and uses this information to request only the new or updated files since that date. Once the process is complete, the results are displayed.

### **3. Registry**

The registry manages the list of yProvStore addresses. You can list, add, and delete these addresses using the following commands:

```
docker exec yprovfind ypfind registry list
docker exec yprovfind ypfind registry add <address>
docker exec yprovfind ypfind registry delete <address>
```

Addresses must be provided in a valid URL format. The input is validated through `pydantic` (`BaseModel`, `HttpUrl`, and `field_validator`), so incorrectly formatted addresses will result in an error.
**Examples of valid addresses:**

* Using a domain name:

```
docker exec yprovfind ypfind registry add http://example.com:9000
```

* Using an IP address:

```
docker exec yprovfind ypfind registry delete http://192.129.202.10:8000
```


### **4. Search**

The CLI provides four search methods to query documents stored across the registered yProvStore instances: **Full-text search**, **Semantic search**, **Hybrid search**, **KNN search (HSNW)**

You can run searches using:

```
docker exec yprovfind ypfind search  <QUERY> [OPTIONS]
```

**QUERY** is the text you want to search for.

Below are examples of supported search modes:

```
Full-text search:
docker exec yprovfind ypfind search climate --ftx

Semantic search:
docker exec yprovfind ypfind search "sea ​​level rise" --smt

Hybrid search:
docker exec yprovfind ypfind search "geospatial data" --hyb

Knn search:
docker exec yprovfind ypfind search forests --knn
```

Additional filtering options are available:

```
Search with date range:
docker exec yprovfind ypfind search "climate change" --date-from 01-01-2024 --date-to 31-12-2024

Search specific version:
docker exec yprovfind ypfind search "climate change" --version 3

Search from a specific instance:
docker exec yprovfind ypfind search "climate change" --instance http://localhost:8000

Include other versions:
docker exec yprovfind ypfind search "climate change" --other-versions
```

**Available options:**

```
--type TEXT                     Search type: ftx (full-text), smt (semantic),
                                hyb (hybrid), knn (semantic Knn)

--date-from DD-MM-YYYY          Filter documents from this date
--date-to DD-MM-YYYY            Filter documents until this date

--version INT                   Filter by document version

--instance URL                  Filter by yProv instance URL

--other-versions / --no-other-versions
                                Include other versions of documents

--limit INTEGER                 Maximum number of results to display
                                [default: 10]

--help                          Show command help
```


> **Note:** You can search directly the documents PID, but in this case the full-text search and hybrid search are the recommended ones to use as they check for the exact match.


### **5. Timestamp**

The **Timestamp** component keeps track of the last time each yProvStore instance (i.e., each registered address) was queried to download provenance metadata.
Whenever the indexing process is run, the timestamp for each address is updated. This ensures that on the next indexing run, only new or updated data is retrieved instead of downloading everything again.

You can manage timestamps through the CLI:

```
docker exec yprovfind ypfind tmstamp list
docker exec yprovfind ypfind tmstamp delete <address>
```


* **list** — returns all registered yProvStore addresses along with their last update timestamp:


* **delete** — removes all stored timestamps for all yProvStore addresses, effectively forcing a full re-index on the next run:




### **6. Demo Mode**

The demo mode allows you to test yProvFind without requiring any external yProvStore instances.
When started, it loads a set of example provenance metadata and indexes them automatically.
This makes it possible to verify that the system is working correctly and to test all search methods (full-text, semantic, hybrid, and KNN) without any additional setup.

You can manage the demo mode with the following commands:
 ```
  docker exec yprovfind ypfind demo start
  docker exec yprovfind ypfind demo end

 ```

* **Start demo mode**
  Loads and indexes the sample provenance metadata.


* **End demo mode**
  Removes all demo data and restores the system to its normal state.


This mode is useful for quick validation, presentations, and development testing.







