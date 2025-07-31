# test_env.py
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="d:/SMART-FARM-kENYA/.env")
print("GEMINI_API_KEY =", os.getenv("GEMINI_API_KEY"))

