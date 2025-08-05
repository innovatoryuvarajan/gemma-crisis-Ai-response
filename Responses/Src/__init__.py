# src/__init__.py
"""
Crisis Response Voice Assistant

An offline voice-based emergency response system that combines:
- Speech-to-Text (Vosk) for voice input
- Text-to-Speech (pyttsx3) for audio responses  
- RAG (Retrieval Augmented Generation) for knowledge base
- Local LLM (Ollama + Gemma) for intelligent responses
- Emergency detection and BLE SOS beacon integration

Components:
- voice_handler: STT/TTS processing
- query_engine: RAG + Ollama integration
- emergency_detector: SOS detection & BLE trigger
- config: Configuration settings
- main_voice_assistant: Main application coordinator

Usage:
    from src import CrisisVoiceAssistant
    assistant = CrisisVoiceAssistant()
    assistant.start()
"""

__version__ = "1.0.0"
__author__ = "Crisis Response Team"
__description__ = "Offline Voice-Based Crisis Response Assistant"

# Import main components for easy access
try:
    from .main_voice_assistant import CrisisVoiceAssistant
    from .voice_handler import VoiceHandler
    from .query_engine import QueryEngine
    from .emergency_detector import EmergencyDetector
    from . import config
    
    __all__ = [
        'CrisisVoiceAssistant',
        'VoiceHandler', 
        'QueryEngine',
        'EmergencyDetector',
        'config'
    ]
    
except ImportError as e:
    # Handle import errors gracefully during development
    print(f"Warning: Some components could not be imported: {e}")
    __all__ = []

# Package metadata
PACKAGE_INFO = {
    "name": "crisis_voice_assistant",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "requires": [
        "sounddevice>=0.4.6",
        "vosk>=0.3.45", 
        "pyttsx3>=2.90",
        "faiss-cpu>=1.7.4",
        "sentence-transformers>=2.2.2",
        "requests>=2.31.0",
        "numpy>=1.24.3",
        "scikit-learn>=1.3.0",
        "bleak>=0.21.1"
    ],
    "python_requires": ">=3.8"
}

def get_version():
    """Return package version"""
    return __version__

def get_package_info():
    """Return package information"""
    return PACKAGE_INFO

# Initialize logging for the package
import logging
import os

def setup_logging(level=logging.INFO):
    """Setup logging for the crisis assistant"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('crisis_assistant.log') if os.access('.', os.W_OK) else logging.NullHandler()
        ]
    )
    return logging.getLogger(__name__)

# Package-level logger
logger = setup_logging()
logger.info(f"Crisis Voice Assistant v{__version__} initialized")

# Configuration validation
def validate_setup():
    """Validate that required files and dependencies are available"""
    issues = []
    
    # Check for required model files
    from .config import VOSK_MODEL_PATH, FAISS_INDEX_PATH, METADATA_PATH
    
    if not os.path.exists(VOSK_MODEL_PATH):
        issues.append(f"Vosk model not found at: {VOSK_MODEL_PATH}")
    
    if not os.path.exists(FAISS_INDEX_PATH):
        issues.append(f"FAISS index not found at: {FAISS_INDEX_PATH}")
        
    if not os.path.exists(METADATA_PATH):
        issues.append(f"Metadata file not found at: {METADATA_PATH}")
    
    # Check Ollama connection
    try:
        import requests
        from .config import OLLAMA_BASE_URL
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            issues.append("Ollama server not responding properly")
    except Exception:
        issues.append("Cannot connect to Ollama server")
    
    if issues:
        logger.warning("Setup validation found issues:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        return False, issues
    else:
        logger.info("✅ All setup validations passed")
        return True, []

# Run validation on import (optional - can be disabled)
VALIDATE_ON_IMPORT = True
if VALIDATE_ON_IMPORT:
    try:
        is_valid, validation_issues = validate_setup()
        if not is_valid:
            logger.warning("Some components may not work properly. Run validate_setup() for details.")
    except Exception as e:
        logger.warning(f"Could not run setup validation: {e}")

# Emergency contact information (can be customized)
EMERGENCY_CONTACTS = {
    "general": "112",  # International emergency number
    "fire": "101",     # Fire services
    "police": "100",   # Police
    "medical": "108",  # Medical emergency
    "disaster": "1078" # Disaster management
}

def get_emergency_contacts():
    """Return emergency contact numbers"""
    return EMERGENCY_CONTACTS

# Quick start helper
def quick_start():
    """Quick start the crisis assistant with default settings"""
    try:
        assistant = CrisisVoiceAssistant()
        print("🚁 Starting Crisis Voice Assistant...")
        print("Say 'help', 'emergency', or describe your situation")
        print("Press Ctrl+C to stop")
        assistant.start()
    except Exception as e:
        logger.error(f"Failed to start assistant: {e}")
        print(f"❌ Error: {e}")
        print("Make sure all dependencies are installed and Ollama is running")

if __name__ == "__main__":
    quick_start()