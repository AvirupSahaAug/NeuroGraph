import os

# Neo4j Config
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# LLM Config
OLLAMA_BASE_URL = "http://localhost:11434"
# We will auto-detect or let user specify, but default to a common one
MODEL_NAME = "llama3.1:8b" 
EMBEDDING_MODEL = "nomic-embed-text:latest"

# Logging
DATASET_FILE = "dissatisfaction_dataset.jsonl"

# Remote Inference (Gemini Pro / External Model)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key="
