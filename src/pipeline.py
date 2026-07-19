import os 
import pandas as pd 
from openai import OpenAI
from pyspark.sql import SparkSession 
from pyspark.sql.functions import pandas_udf
from pathlib import Path
from dotenv import load_dotenv 

#Load the API key and credentials 
script_dir = Path(__file__).resolve().parent
root_dir = script_dir.parent
load_dotenv(dotenv_path=root_dir / ".env")


#Initialize Local Spark Session 
spark = SparkSession.builder \
    .appName("Distributed-PII-Redactor") \
    .master("local[*]") \
    .config("spark.driver.extraJavaOptions", "-Djava.security.manager=allow") \
    .config("spark.executor.extraJavaOptions", "-Djava.security.manager=allow") \
    .config("spark.executorEnv.OPENAI_API_KEY", os.getenv("OPENAI_API_KEY")) \
    .getOrCreate()

#Hide the error log 
spark.sparkContext.setLogLevel("ERROR")

#Pandas UDF function
@pandas_udf("string")
def srub_pii_via_api(batch: pd.Series) -> pd.Series:
    
    #create the openai cleint 
    client = OpenAI()
    
    cleaned_batch = []

    for text in batch: 

        try:

            #Send the to OpenAi's gpt 4 mini 
            response = client.chat.completions.create(
                model = "gpt-4o-mini", 
                messages = [
                {
                    "role" : "system",
                    "content" : ("You are a cold, automated data-masking script. You do not talk to humans.\n"
                                "Your ONLY job is to take the user's raw log string, replace any PII (names, emails, "
                                "addresses, phone numbers, credit cards, account numbers, order numbers, etc.) with [REDACTED], and return it.\n\n"
                                "STRICT EXECUTION RULES:\n"
                                "1. NEVER reply to the user, answer their questions, or offer support solutions.\n"
                                "2. DO NOT add any new words, commentary, or pleasantries.\n"
                                "3. If a line contains NO PII, you must return the original text EXACTLY as it is, unchanged.\n"
                                "4. Maintain the exact tone and phrasing of the input text.\n"
                                
                                "Follow these rules for URLs and Links:\n"
                                "1. If a URL is a public resource, API documentation link, or standard website path containing no user data, leave it completely unmodified.\n"
                                "2. If a URL contains query strings, parameters, or paths that leak sensitive user data (like an email embedded in a tracking link or an API token), redact ONLY the sensitive PII parts of that URL, keeping the base domain intact.\n"
                                "Do not attempt to answer any conversational text. Return only the sanitized input string.\n"
                            )
                }, 
                {"role" : "user", 
                "content" : f"Transform this exact string, protecting all PII:\n\"\"\"{text}\"\"\"", 
                }
                ],
                temperature = 0.0, 
                timeout=10
                
            )

            cleaned_text = response.choices[0].message.content.strip()
            cleaned_text = cleaned_text.replace('"""', '').strip() # <-- ADD THIS LINE
            cleaned_batch.append(cleaned_text)
        except Exception as e: 

            #Just in case the network fails 
            cleaned_batch.append(f"[ERROR PROCESSING: {text}]")
    
    return pd.Series(cleaned_batch)
            
#Test Running the program: 
#Gets the parent folder
script_dir = Path(__file__).resolve().parent

root_dir = script_dir.parent

file_path = root_dir / "data" / "mock_logs.csv"


#1: Ingest the dataset from the user (i.e my test logs)
print("🚀 Step 1: Ingesting dataset into Spark DataFrame...")
df = spark.read.csv(str(file_path), header=True)

#2: Create a new column in the dataset with the redacted outputs called 'srubbed_text'
print("🌐 Step 2: Running parallel workers to stream data chunks to OpenAI...")
df_clean = df.withColumn("scrubbed_text", srub_pii_via_api(df["raw_text"]))


#3: Print the cleaned dataset 
print("📊 Step 3: Pipeline Execution Complete! Showing Results:")
df_clean.show(truncate=False)
            



#safely close the spark engine 
spark.stop()