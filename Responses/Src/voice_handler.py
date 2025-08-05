import queue
import sounddevice as sd
import json
import pyttsx3
import threading
import time
import os
from vosk import Model, KaldiRecognizer
from config import *

class VoiceHandler:
    def __init__(self):
        print("🎤 Initializing Voice Handler...")
        
        # Check Vosk model path first
        if not os.path.exists(VOSK_MODEL_PATH):
            raise FileNotFoundError(f"Vosk model not found at: {VOSK_MODEL_PATH}")
        
        # Initialize Vosk STT
        try:
            print(f"🔄 Loading Vosk model from: {VOSK_MODEL_PATH}")
            self.model = Model(VOSK_MODEL_PATH)
            self.recognizer = KaldiRecognizer(self.model, SAMPLE_RATE)
            print("✅ Vosk STT initialized")
        except Exception as e:
            print(f"❌ Vosk initialization error: {e}")
            raise
        
        # TTS Management
        self.current_tts_process = None
        self.tts_lock = threading.Lock()
        self.should_stop_tts = False
        self.is_speaking = False
        
        # Audio queue and state
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.pause_listening = False  # New: pause STT when speaking
        
        print("✅ TTS initialized")
    
    def _create_fresh_tts(self):
        """Create a fresh TTS engine for each use"""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', TTS_RATE)
            engine.setProperty('volume', TTS_VOLUME)
            return engine
        except Exception as e:
            print(f"❌ TTS creation error: {e}")
            return None
    
    def speak(self, text):
        """Non-blocking speech with interrupt capability"""
        if not text or not text.strip():
            return
        
        # Truncate very long responses
        # if len(text) > 500:
        #     text = text[:450] + "... Please ask for more details if needed."
        
        # print(f"🔈 Speaking: {text[:100]}..." if len(text) > 100 else f"🔈 Speaking: {text}")
        print(f"🔈 Speaking: {text}")
        # Stop any current TTS
        # if self.is_speaking:
        self.stop_current_speech()
        
        # Start new TTS in thread
        def speak_thread():
            try:
                with self.tts_lock:
                    self.is_speaking = True
                    self.should_stop_tts = False
                    self.pause_listening = True  # Pause STT while speaking
                    
                    # Create fresh TTS engine
                    engine = self._create_fresh_tts()
                    if not engine:
                        print("❌ Could not create TTS engine")
                        return
                    
                    self.current_tts_process = engine
                    
                    # Split long text into chunks for better control
                    chunks = self._split_text_into_chunks(text)
                    
                    for i, chunk in enumerate(chunks):
                        if self.should_stop_tts:
                            print("🛑 TTS interrupted")
                            break
                        
                        try:
                            engine.say(chunk)
                            engine.runAndWait()
                        except Exception as e:
                            print(f"TTS chunk {i} error: {e}")
                            break
                    
                    # Cleanup
                    try:
                        engine.stop()
                        del engine
                    except:
                        pass
                    
                    self.current_tts_process = None
                    self.is_speaking = False
                    self.pause_listening = False  # Resume STT
                    
            except Exception as e:
                print(f"❌ Speech thread error: {e}")
                self.is_speaking = False
                self.pause_listening = False
        
        # Start speech thread
        speech_thread = threading.Thread(target=speak_thread, daemon=True)
        speech_thread.start()
    
    def _split_text_into_chunks(self, text, max_length=1500):
        """Split text into manageable chunks"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def stop_current_speech(self):
        """Stop current TTS immediately"""
        self.should_stop_tts = True
        
        if self.current_tts_process:
            try:
                self.current_tts_process.stop()
            except:
                pass
        
        # Wait briefly for cleanup
        max_wait = 20  # 2 seconds max wait
        wait_count = 0
        while self.is_speaking and wait_count < max_wait:
            time.sleep(0.1)
            wait_count += 1
        
        if self.is_speaking:
            print("⚠️ Force stopping TTS")
            self.is_speaking = False
            self.pause_listening = False
    
    def speak_urgent(self, text):
        """Immediate speech for urgent situations"""
        print(f"🚨 URGENT: {text}")
        
        # Stop current speech immediately
        self.stop_current_speech()
        
        # Use simple, direct TTS
        try:
            engine = self._create_fresh_tts()
            if engine:
                engine.setProperty('rate', TTS_RATE + 30)  # Faster for urgent
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                del engine
        except Exception as e:
            print(f"❌ Urgent speech error: {e}")
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input"""
        if status:
            print(f"Audio input error: {status}")
        
        # Don't process audio while speaking
        if not self.pause_listening:
            self.audio_queue.put(bytes(indata))
    
    def listen_for_speech(self, callback_function):
        """Start listening for speech input"""
        self.is_listening = True
        print("🎤 Listening... (Say 'stop listening' to pause)")
        
        try:
            with sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                dtype='int16',
                channels=1,
                callback=self.audio_callback
            ):
                while self.is_listening:
                    try:
                        # Skip if paused or no data
                        if self.pause_listening:
                            time.sleep(0.1)
                            continue
                        
                        data = self.audio_queue.get(timeout=0.1)
                        
                        if self.recognizer.AcceptWaveform(data):
                            result = json.loads(self.recognizer.Result())
                            text = result.get("text", "").strip()
                            
                            if text:
                                print(f"🗣️ You said: {text}")
                                
                                # Check for stop command
                                if "stop listening" in text.lower():
                                    self.speak("Voice assistant paused.")
                                    self.is_listening = False
                                    break
                                
                                # Stop current speech if new input comes
                                if self.is_speaking:
                                    print("🛑 Interrupting current response...")
                                    self.stop_current_speech()
                                
                                # Process the speech
                                callback_function(text)
                    
                    except queue.Empty:
                        continue
                    
        except KeyboardInterrupt:
            print("\n🛑 Voice input stopped by user")
        except Exception as e:
            print(f"❌ Voice input error: {e}")
        finally:
            self.is_listening = False
    
    def stop_listening(self):
        """Stop voice input"""
        self.is_listening = False
        self.stop_current_speech()
        print("🔇 Voice input stopped")
    
    def cleanup(self):
        """Clean up resources"""
        self.is_listening = False
        self.stop_current_speech()
        
        # Clear audio queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                break
        
        print("🧹 Voice handler cleaned up")
    
    def get_status(self):
        """Get current status"""
        return {
            "listening": self.is_listening,
            "speaking": self.is_speaking,
            "paused": self.pause_listening
        }