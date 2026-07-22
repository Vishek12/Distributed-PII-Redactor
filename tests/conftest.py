# Global test configuration for pytest 
import os
from pathlib import Path
import pytest
from pyspark.sql import SparkSession
from dotenv import load_dotenv

# Load environment variables from .env file in parent directory
test_dir = Path(__file__).resolve().parent
root_dir = test_dir.parent
load_dotenv(dotenv_path=root_dir / ".env")

@pytest.fixture(scope="session")
def spark_session():
    # Obtain the OpenAI API key or fallback to a dummy string for unit testing
    api_key = os.getenv("OPENAI_API_KEY", "mock-api-key")

    # Create a single Spark session for all tests
    spark = SparkSession.builder \
        .appName("PII-Redactor-Tests") \
        .master("local[*]") \
        .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow") \
        .config("spark.executor.extraJavaOptions", "-Djava.security.manager=allow") \
        .config("spark.sql.shuffle.partitions", "1") \
        .config("spark.executorEnv.OPENAI_API_KEY", api_key) \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("ERROR")

    yield spark

    # Close the Spark session after all tests are done
    spark.stop()