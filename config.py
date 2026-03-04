"""
config.py — Spark Assistant configuration
Reads from environment variables on Railway, falls back to local values.
"""
import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8718417061:AAGyMqdvf7VN7QwkxX_ttHMvF2hGKVW_rkQ")
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY",     "AIzaSyBkFvx00JZ2VwWezXHlPFgBUZfFFBDl7VI")
TIMEZONE           = os.environ.get("TIMEZONE",           "Asia/Kuala_Lumpur")
