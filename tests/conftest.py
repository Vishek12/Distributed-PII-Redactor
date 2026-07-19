# Global test configuration for pytest 
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark_session():
    # Create a single Spark session for all tests
    spark = SparkSession.builder \
        .appName("PII-Redactor-Tests") \
        .master("local[*]") \
        .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow") \
        .config("spark.executor.extraJavaOptions", "-Djava.security.manager=allow") \
        .config("spark.sql.shuffle.partitions", "1") \
        .config("spark.executorEnv.OPENAI_API_KEY", os.getenv("OPENAI_API_KEY")) \
        .getOrCreate()
    yield spark
    # Close the Spark session after all tests are done
    spark.stop()
