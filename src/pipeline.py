import os
import pandas as pd
from openai import OpenAI
from pyspark.sql import SparkSession
from pyspark.sql.functions import pandas_udf
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# 1. Load credentials into driver process
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent
load_dotenv(dotenv_path=root_dir / ".env") #Change to the correct path to your .env file if needed (if cloning the repo, it should be in the root directory)

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# 2. Initialize Spark Session
# Initialize Local Spark Session 
spark = SparkSession.builder \
    .appName("Distributed-PII-Redactor") \
    .master("local[*]") \
    .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow") \
    .config("spark.executor.extraJavaOptions", "-Djava.security.manager=allow") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# 3. Vectorized/Threaded Pandas UDF
@pandas_udf("string")
def srub_pii_via_api(batch: pd.Series) -> pd.Series:
    # Initialize client explicitly using captured key
    client = OpenAI(api_key=OPENAI_KEY)

    def process_single_text(text: str) -> str:
        if not text or pd.isna(text):
            return ""
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a cold, automated data-masking script. You do not talk to humans.\n"
                            "Your ONLY job is to take the user's raw log string, replace any PII (names, emails, "
                            "addresses, phone numbers, credit cards, account numbers, order numbers, etc.) with [REDACTED], and return it.\n\n"
                            "STRICT EXECUTION RULES:\n"
                            "1. NEVER reply to the user, answer their questions, or offer support solutions.\n"
                            "2. DO NOT add any new words, commentary, or pleasantries.\n"
                            "3. If a line contains NO PII, you must return the original text EXACTLY as it is, unchanged.\n"
                            "4. Maintain the exact tone and phrasing of the input text.\n"
                            "5. If a URL is public/API docs, leave unmodified. If it leaks PII in query params, redact ONLY the sensitive part."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Transform this exact string, protecting all PII:\n\"\"\"{text}\"\"\""
                    }
                ],
                temperature=0.0,
                timeout=10
            )
            cleaned = response.choices[0].message.content.strip()
            return cleaned.replace('"""', '').strip()
        except Exception as e:
            return f"[ERROR PROCESSING: {text}]"

    # Use ThreadPoolExecutor to make concurrent requests per PySpark batch
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_single_text, batch))

    return pd.Series(results)

# 4. Execute Pipeline
file_path = root_dir / "data" / "mock_logs.csv"

print("🚀 Step 1: Ingesting dataset into Spark DataFrame...")
df = spark.read.csv(str(file_path), header=True)

print("🌐 Step 2: Running parallel workers to stream data chunks to OpenAI...")
df_clean = df.withColumn("scrubbed_text", srub_pii_via_api(df["raw_text"]))

print("📊 Step 3: Pipeline Execution Complete! Showing Results:")
df_clean.show(truncate=False)

spark.stop()