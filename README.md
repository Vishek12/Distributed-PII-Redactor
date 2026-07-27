## 🏗 Architecture Overview

The pipeline follows a distributed batch-processing pattern. PySpark handles data partitioning and parallel execution across worker nodes, while vectorized Pandas UDFs manage high-throughput concurrent API calls to OpenAI for dynamic PII redaction.


[Input Dataset]  (Logs, CSVs, Parquet, Delta Lake)
       │
       ▼
[PySpark Driver]  Configures schema & partitions workload
       │
       ▼
[PySpark Workers] Vectorized Pandas UDF (@pandas_udf)
       │          └─ ThreadPoolExecutor (Async OpenAI calls w/ retries)
       ▼
[LLM Inference]  gpt-4o-mini (Context-aware PII scrubbing)
       │
       ▼
[Output Storage] (Cleaned Parquet / Delta Lake / S3)


## 🛠 Tech Stack

| Category | Technology | Usage & Focus |
| :--- | :--- | :--- |
| **Distributed Computing** | `PySpark 3.x` | Large-scale data processing, DataFrame transformations, and worker partitioning. |
| **Data Interchange** | `Apache Arrow` / `PyArrow` | Zero-copy memory transfers between Spark JVM and Python worker processes. |
| **AI / Inference** | `OpenAI API` (`gpt-4o-mini`) | Context-aware PII extraction and text redaction via direct API integration. |
| **Concurrency** | `concurrent.futures` | Multi-threaded asynchronous request dispatching inside Pandas UDFs. |
| **Testing & Mocking** | `pytest`, `unittest.mock` | Unit test execution with full OpenAI API patching for isolated offline CI/CD. |
| **Environment Management**| `python-dotenv` | Secure API key handling and dynamic execution configuration. |
