import os

# Paths
# PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = "D:\Gemma3n_Local\Voice_Assistant"
MODELS_PATH = os.path.join(PROJECT_ROOT, "Models")
DATA_PATH = os.path.join(PROJECT_ROOT, "Data")

# Vosk Model
VOSK_MODEL_PATH = os.path.join(MODELS_PATH, "vosk-model-small-en-us-0.15")

# RAG Files
FAISS_INDEX_PATH = os.path.join(DATA_PATH, "rag_index.faiss")
METADATA_PATH = os.path.join(DATA_PATH, "rag_metadata.json")
FAQ_PATH = os.path.join(DATA_PATH, "emergency_faq.json")

# Audio Settings
SAMPLE_RATE = 16000
BLOCK_SIZE = 8000

# Ollama Settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma3n:latest"

# TTS Settings
TTS_RATE = 150
TTS_VOLUME = 0.9

# Crisis Detection
SOS_KEYWORDS = ["sos", "help me", "emergency", "urgent", "critical", "mayday"]
HIGH_URGENCY_KEYWORDS = [
    "bleeding", "blood", "stuck", "trapped", "drowning", "fire", "burning",
    "can't breathe", "chest pain", "unconscious", "choking", "severe pain",
    "broken bone", "head injury", "allergic reaction", "poisoned", "dying"
]

# BLE Settings (for SOS device)
BLE_DEVICE_NAME = "SOS_BEACON"  # Your BLE device name
BLE_SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"