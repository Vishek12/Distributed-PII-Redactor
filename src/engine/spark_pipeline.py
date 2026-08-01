"""This file handles the Pyspark engine, wrapping a process single text inside a @pandas_udf and leveraging ThreadPoolExecutor to process batches of text in parallel. It also loads the OpenAI API 
key from the .env file for use in the Spark workers."""

import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from pyspark.sql import SparkSession
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import StringType



#Import the worker function from llm_client.py
from src.engine.llm_client import process_single_text

"""Function execute will multi-threaded HTTP requests across pandas series batches 
to maximize throughput and minimize latency. It will be used as a @pandas_udf in the Spark pipeline."""
@pandas_udf(StringType())
def scrub_pii_via_api(batch: pd.Series) -> pd.Series:
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_single_text, batch))
    return pd.Series(results)


# Function to initialize the Spark session and set up the environment for the Spark pipeline.
def build_spark_session(app_name: str = "Distributed-PII-Redactor") -> SparkSession:
    """Initializes the Spark session and sets up the environment for the Spark pipeline."""

    spark = SparkSession.builder \
        .appName(app_name) \
        .master("local[*]") \
        .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow") \
        .config("spark.executor.extraJavaOptions", "-Djava.security.manager=allow") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    return spark

# Function to run the Spark pipeline for PII redaction on a given CSV file.
def run_pipeline(input_csv_path: str, api_key: str = None) -> pd.DataFrame:
    spark = build_spark_session()
    spark.sparkContext.setLogLevel("ERROR")

    # Read log dataset
    df = spark.read.csv(input_csv_path, header=True, inferSchema=True)

    target_column = "raw_text"  

    # Apply the Pandas UDF to redact PII concurrently
    df_redacted = df.withColumn("redacted_text", scrub_pii_via_api(df[target_column]))
    
    return df_redacted


# Local testing of the redaction pipeline
if __name__ == "__main__": 

    sample_file_path = "data/mock_logs.csv"  # Adjust path as needed

    if os.path.exists(sample_file_path):
        print(f"🚀 Running Spark pipeline on {sample_file_path}...")
        result_df = run_pipeline(sample_file_path)
        result_df.show(truncate=False)
    else:
        print(f"❌ Sample file {sample_file_path} not found. Please ensure the file exists.")