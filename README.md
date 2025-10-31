
# **yProvFind**

**yProvFind** is a search engine designed to discover and manage *provenance* records coming from **yProvStore** services distributed worldwide.
The system allows provenance search through **structured metadata** (title, description, keywords, author, PID), providing a **hybrid search mechanism** that combines:

* **Full-text search**, powered by *Elasticsearch*, for traditional keyword-based queries.
* **Semantic search**, supported by an *embedding model* that merges the title, description, and keywords fields to capture conceptual relationships between contents.

The architecture is built with **FastAPI** (running on *Uvicorn*), exposing REST endpoints to interact with the search engine.

Moreover, **yProvFind** will be able to maintain an up-to-date **STAC (SpatioTemporal Asset Catalog)** containing all indexed provenance records, enabling integration and federation with external services.
This functionality is currently under development.

## Table of Content
- [Deployment with Docker](#running-yprovfind-with-docker)
- [Research methods](#research-methods)




## **Running yProvFind with Docker**

The project includes a `docker-compose.yml` file that defines all required services to run **yProvFind** and its dependencies.
The setup consists of two containers:

* **yProvFind** – the main application built from this repository.
* **Elasticsearch** – pulled automatically from Docker Hub (`docker.elastic.co/elasticsearch/elasticsearch:9.0.3`).

### **1. Requirements**

* **Docker** and **Docker Compose** must be installed on your system.

  * On **desktop environments** (Windows, macOS), simply install and start **Docker Desktop**.


### **2. Create the .env file**

Before starting the containers, you **must** create a `.env` file in the root directory of the project. This file contains the credentials needed to connect the `yProvFind` container to Elasticsearch.

**Important:** At first startup, Elasticsearch sets the username and password based on the values in this file. If the `.env` file is not created beforehand, Elasticsearch will generate random credentials automatically, making the connection impossible.

Create a file named `.env` in the project root with the following content:

```env
ELASTICSEARCH_URL=https://localhost:9200
ES_USER=elastic
ES_PASSWORD=password
```

> **Note:** You can customize the `ES_PASSWORD` value for better security. 



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

### 5. Access the API docs:
Open http://localhost:8002/docs in your browser.


### **6. Stop and clean up**

To stop and remove all running containers, networks, and temporary data:

```bash
docker compose down
```

## **Research methods**

### 1. Research full-text 
It analyzes and tokenizes text by eliminating stop words (conjunctions, etc.) to compare query words with indexed terms, calculating the relevance of results using the BM25 scoring. It is useful for keyword-based searches and text relevance

### 2. Semantic search 
It uses vector representations (embeddings) of sentences and documents to compare meanings rather than exact words, calculating similarity using functions such as cosine similarity. The embedding is performed by Hugging Face's all-MiniLM-L6-v2 model, which generates a vector of 384 features.

### 3. Hibrid search 
It combines text and semantic matching: Elasticsearch runs both searches in parallel and calculates an overall score that takes into account both keywords and meaning.

### 4. KNN Search with HNSW
This search method uses the Hierarchical Navigable Small World (HNSW) algorithm to efficiently find the vectors most similar to the query vector in the semantic_embedding field. The query embedding is then computed and compared with those indexed via approximate k-nearest neighbor (KNN) search, reducing the number of direct comparisons thanks to the hierarchical structure of the HNSW graph. In parallel, a textual bool query (with multi-match on fields such as title, description, etc.) filters and refines the results, combining vector search and textual criteria. This approach guarantees high efficiency on large datasets, maintaining good accuracy, and can exploit early termination strategies to stop the graph traversal early when the results are already sufficiently good.


