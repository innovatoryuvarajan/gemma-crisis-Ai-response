"""
Voice Assistant
Main application that coordinates all components
"""

import os
import sys
import threading
import time
import queue  # FIXED: Added missing import
import json
import sounddevice as sd

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from voice_handler import VoiceHandler
from query_engine import QueryEngine
from emergency_detector import EmergencyDetector
from config import *

class CrisisVoiceAssistant:
    def __init__(self):
        print("🚁 Initializing Crisis Response Voice Assistant...")
        print("=" * 60)
        
        # Initialize components
        try:
            self.voice_handler = VoiceHandler()
            self.query_engine = QueryEngine()
            self.emergency_detector = EmergencyDetector()
            
            self.is_running = False
            self.processing_lock = threading.Lock()
            
            print("✅ All components initialized successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            sys.exit(1)
    
    def process_voice_input(self, text):
        """Process voice input and generate response"""
        # Prevent overlapping processing
        if not self.processing_lock.acquire(blocking=False):
            print("⏳ Still processing previous request...")
            return
        
        try:
            # Check for emergency/SOS first
            is_emergency, keyword = self.emergency_detector.detect_sos_in_text(text)
            
            if is_emergency:
                # Handle emergency with immediate response
                print(f"🚨 EMERGENCY DETECTED: {keyword}")
                
                # Immediate emergency acknowledgment
                emergency_ack = f"Emergency detected: {keyword}. Getting help now."
                self.voice_handler.speak_urgent(emergency_ack)
                
                # Trigger SOS in background (non-blocking)
                def background_sos():
                    try:
                        self.emergency_detector.handle_emergency(text, keyword)
                    except Exception as e:
                        print(f"SOS trigger error: {e}")
                
                threading.Thread(target=background_sos, daemon=True).start()
                
                # Brief pause before getting detailed response
                time.sleep(1)
                
                # Get emergency guidance
                print("📋 Getting emergency guidance...")
                response = self.query_engine.process_query(text)
                
                # Clean the response for better TTS
                cleaned_response = self._clean_response_for_tts(response)
                self.voice_handler.speak(cleaned_response)
                
            else:
                # Normal query processing
                response = self.query_engine.process_query(text)
                cleaned_response = self._clean_response_for_tts(response)
                self.voice_handler.speak(cleaned_response)
                
        except Exception as e:
            error_msg = "I encountered an error. Please try again."
            print(f"❌ Processing error: {e}")
            self.voice_handler.speak(error_msg)
        
        finally:
            self.processing_lock.release()
    
    def _clean_response_for_tts(self, response):
        """Clean AI response for better TTS"""
        if not response:
            return "I couldn't generate a response. Please try again."
        
        # Remove excessive formatting
        cleaned = response.replace('**', '').replace('*', '')
        cleaned = cleaned.replace('⚠️', 'Warning:').replace('🚨', 'Emergency:')
        cleaned = cleaned.replace('✅', 'Step:').replace('❌', 'Error:')
        
        # Remove excessive line breaks
        cleaned = ' '.join(cleaned.split())
        
        # Limit length for TTS
        # if len(cleaned) > 400:
        #     sentences = cleaned.split('. ')
        #     result = ""
        #     for sentence in sentences:
        #         if len(result + sentence) < 350:
        #             result += sentence + ". "
        #         else:
        #             break
        #     cleaned = result + "Ask for more details if needed."
        
        return cleaned.strip()
    
    def start(self):
        """Start the voice assistant"""
        self.is_running = True
        
        print("🎤 Crisis Voice Assistant is now active!")
        print("📢 Available commands:")
        print("   - Say anything for help")
        print("   - Say 'stop listening' to pause")
        print("   - Say 'start listening' to resume")
        print("   - Press Ctrl+C to exit")
        print("-" * 60)
        
        try:
            # Start voice listening loop
            while self.is_running:
                try:
                    self.voice_handler.listen_for_speech(self.process_voice_input)
                    
                    # If listening stopped, wait for restart command
                    if self.is_running:
                        print("🔄 Say 'start listening' to resume, or Ctrl+C to exit")
                        self.wait_for_restart()
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Voice loop error: {e}")
                    time.sleep(2)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def wait_for_restart(self):
        """Wait for restart command with proper imports"""
        print("🎤 Listening for 'start listening' command... (30 second timeout)")
        
        try:
            from vosk import KaldiRecognizer, Model
            
            model = Model(VOSK_MODEL_PATH)
            recognizer = KaldiRecognizer(model, SAMPLE_RATE)
            restart_queue = queue.Queue()
            
            def restart_callback(indata, frames, time, status):
                restart_queue.put(bytes(indata))
            
            found_restart = False
            start_time = time.time()
            
            with sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                dtype='int16',
                channels=1,
                callback=restart_callback
            ):
                while time.time() - start_time < 30 and not found_restart:
                    try:
                        data = restart_queue.get(timeout=0.1)
                        if recognizer.AcceptWaveform(data):
                            result = json.loads(recognizer.Result())
                            text = result.get("text", "").strip().lower()
                            
                            if "start listening" in text:
                                print("▶️ Resuming voice assistant...")
                                found_restart = True
                                break
                            elif "exit" in text or "quit" in text:
                                self.is_running = False
                                break
                                
                    except queue.Empty:
                        continue
                        
            if not found_restart and self.is_running:
                print("⏰ Timeout reached. Auto-resuming...")
                
        except Exception as e:
            print(f"❌ Restart detection error: {e}")
            print("⏰ Auto-resuming after error...")
    
    def stop(self):
        """Stop the voice assistant"""
        self.is_running = False
        
        # Clean up components
        try:
            self.voice_handler.cleanup()
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        print("\n🛑 Crisis Voice Assistant stopped.")
        print("Stay safe! 🚁")

def main():
    """Main entry point"""
    print("🚁 CRISIS RESPONSE VOICE ASSISTANT")
    print("===================================")
    
    # Check if Ollama is running
    try:
        import requests
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
        else:
            print("⚠️ Ollama may not be properly configured")
    except:
        print("❌ Cannot connect to Ollama. Please start it with: ollama serve")
        print("   And ensure your model is available: ollama run gemma3n:latest")
        return
    
    # Start the assistant
    assistant = CrisisVoiceAssistant()
    
    try:
        assistant.start()
    except Exception as e:
        print(f"❌ Assistant crashed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()