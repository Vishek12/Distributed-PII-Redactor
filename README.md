## 🏗 Architecture Overview

The pipeline follows a distributed batch-processing pattern. PySpark handles data partitioning and parallel execution across worker nodes, while vectorized Pandas UDFs manage high-throughput concurrent API calls to OpenAI for dynamic PII redaction.

+-----------------------------------------------------------------------------------+
|                                  INPUT DATASET                                    |
|                      (Log Files, CSVs, Delta Lake, Parquet)                        |
+-----------------------------------------------------------------------------------+
|
v
+-----------------------------------------------------------------------------------+
|                                PYSPARK DRIVER                                     |
|  * Loads raw dataset into DataFrame                                               |
|  * Configures schemas & partitions workload across worker nodes                   |
+-----------------------------------------------------------------------------------+
|
v
+-----------------------------------------------------------------------------------+
|                                PYSPARK WORKERS                                    |
|  Vectorized Pandas UDF (@pandas_udf) splits execution into PyArrow batches      |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                         THREADPOOL EXECUTOR                                 |  |
|  |  * Asynchronous execution across worker CPU cores                           |  |
|  |  * Dispatches parallel OpenAI Chat API calls (gpt-4o-mini)                  |  |
|  |  * Retries on 429 Rate Limits / API timeouts with exponential backoff        |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
|
v
+-----------------------------------------------------------------------------------+
|                                 LLM INFERENCE                                     |
|  * System Prompt enforces strict text transformation & preserves context           |
|  * Identifies & scrubs Names, Emails, SSNs, Credit Cards, IPs, and Custom PII      |
+-----------------------------------------------------------------------------------+
|
v
+-----------------------------------------------------------------------------------+
|                                OUTPUT STORAGE                                     |
|                       (Cleaned Parquet / Delta Lake / S3)                         |
+-----------------------------------------------------------------------------------+


## 🛠 Tech Stack

| Category | Technology | Usage & Focus |
| :--- | :--- | :--- |
| **Distributed Computing** | `PySpark 3.x` | Large-scale data processing, DataFrame transformations, and worker partitioning. |
| **Data Interchange** | `Apache Arrow` / `PyArrow` | Zero-copy memory transfers between Spark JVM and Python worker processes. |
| **AI / Inference** | `OpenAI API` (`gpt-4o-mini`) | Context-aware PII extraction and text redaction via direct API integration. |
| **Concurrency** | `concurrent.futures` | Multi-threaded asynchronous request dispatching inside Pandas UDFs. |
| **Testing & Mocking** | `pytest`, `unittest.mock` | Unit test execution with full OpenAI API patching for isolated offline CI/CD. |
| **Environment Management**| `python-dotenv` | Secure API key handling and dynamic execution configuration. |
