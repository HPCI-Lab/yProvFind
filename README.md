
# **yProvFind**

**yProvFind** is a search engine designed to discover and manage *provenance* records coming from **yProvStore** services distributed worldwide.
The system allows provenance search through **structured metadata** (title, description, keywords, author, PID), providing a **hybrid search mechanism** that combines:

* **Full-text search**, powered by *Elasticsearch*, for traditional keyword-based queries.
* **Semantic search**, supported by an *embedding model* that merges the title, description, and keywords fields to capture conceptual relationships between contents.

The architecture is built with **FastAPI** (running on *Uvicorn*), exposing REST endpoints to interact with the search engine.

Moreover, **yProvFind** will be able to maintain an up-to-date **STAC (SpatioTemporal Asset Catalog)** containing all indexed provenance records, enabling integration and federation with external services.
This functionality is currently under development.





## **Running yProvFind with Docker**

The project includes a `docker-compose.yml` file that defines all required services to run **yProvFind** and its dependencies.
The setup consists of two containers:

* **yProvFind** – the main application built from this repository.
* **Elasticsearch** – pulled automatically from Docker Hub (`docker.elastic.co/elasticsearch/elasticsearch:9.0.3`).

### **1. Requirements**

* **Docker** and **Docker Compose** must be installed on your system.

  * On **desktop environments** (Windows, macOS), simply install and start **Docker Desktop**.


### **2. Build the images**

From the root of the repository, run:

```bash
docker compose build
```

This command builds the **yProvFind** image using the local `Dockerfile`, while pulling the official **Elasticsearch** image from Docker Hub.

### **3. Start the services**

To start the full stack:

```bash
docker compose up
```

This launches both containers and attaches their logs to your terminal.
If you prefer to run them in the background:

```bash
docker compose up -d
```

Once running, **yProvFind** will expose its **FastAPI** endpoints (check the `docker-compose.yml` for the configured port), and **Elasticsearch** will be available internally for indexing and search operations.

### **4. Stop and clean up**

To stop and remove all running containers, networks, and temporary data:

```bash
docker compose down
```



