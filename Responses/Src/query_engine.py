import faiss
import numpy as np
import json
import requests
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config import *

class QueryEngine:
    def __init__(self):
        print("🧠 Initializing Query Engine...")
        
        # Load sentence transformer
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Load FAISS index and metadata
        try:
            self.index = faiss.read_index(FAISS_INDEX_PATH)
            with open(METADATA_PATH, 'r') as f:
                data = json.load(f)
            self.texts = data["texts"]
            self.metadata = data["meta"]
            print(f"✅ RAG loaded: {len(self.texts)} documents")
        except Exception as e:
            print(f"❌ Error loading RAG data: {e}")
            self.index = None
            self.texts = []
            self.metadata = []
        
        # Load emergency FAQ
        try:
            with open(FAQ_PATH, 'r') as f:
                faq_data = json.load(f)
            self.emergency_faqs = faq_data["faqs"]
            print(f"✅ Emergency FAQ loaded: {len(self.emergency_faqs)} entries")
        except Exception as e:
            print(f"⚠️ Could not load emergency FAQ: {e}")
            self.emergency_faqs = []
    
    def search_emergency_faq(self, query_text):
        """Search predefined emergency FAQ first"""
        query_lower = query_text.lower()
        
        best_match = None
        best_score = 0
        
        for faq in self.emergency_faqs:
            score = 0
            for keyword in faq["keywords"]:
                if keyword.lower() in query_lower:
                    score += 1
            
            # Normalize score by number of keywords
            normalized_score = score / len(faq["keywords"]) if faq["keywords"] else 0
            
            if normalized_score > best_score and normalized_score > 0.3:  # At least 30% match
                best_score = normalized_score
                best_match = faq
        
        return best_match
    
    def search_rag_database(self, query_text, top_k=3, confidence_threshold=0.65):
        """Search RAG database using vector similarity"""
        if not self.index or not self.texts:
            return None, 0.0
        
        try:
            query_vec = self.model.encode([query_text])
            D, I = self.index.search(np.array(query_vec), top_k)
            
            if I[0][0] == -1:  # No results
                return None, 0.0
            
            # Get best match and calculate cosine similarity
            best_idx = I[0][0]
            best_text = self.texts[best_idx]
            
            text_vec = self.model.encode([best_text])
            similarity = cosine_similarity(query_vec, text_vec)[0][0]
            
            if similarity > confidence_threshold:
                return best_text, similarity
            
            return None, similarity
            
        except Exception as e:
            print(f"❌ RAG search error: {e}")
            return None, 0.0
    
    def call_ollama(self, prompt):
        """Call local Ollama Gemma model"""
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.8,
                        "num_predict": 200
                    }
                },
                timeout=100
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response generated")
            else:
                return f"Ollama error: HTTP {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return "Cannot connect to Ollama. Please ensure it's running on localhost:11434"
        except Exception as e:
            return f"Error calling Ollama: {str(e)[:100]}"
    
    def analyze_crisis_urgency(self, query_text):
        """Analyze urgency level of the crisis"""
        query_lower = query_text.lower()
        
        urgency_level = "low"
        
        # Check for high urgency keywords
        for keyword in HIGH_URGENCY_KEYWORDS:
            if keyword in query_lower:
                urgency_level = "high"
                break
        
        # Check for SOS keywords
        for keyword in SOS_KEYWORDS:
            if keyword in query_lower:
                urgency_level = "high"
                break
        
        return urgency_level
    
    def process_query(self, query_text):
        """Main query processing pipeline"""
        print(f"🔍 Processing: {query_text}")
        
        # Step 1: Check Emergency FAQ first
        faq_match = self.search_emergency_faq(query_text)
        if faq_match:
            print("✅ Found in Emergency FAQ")
            return faq_match["response"]
        
        # Step 2: Search RAG database
        rag_result, similarity = self.search_rag_database(query_text)
        if rag_result:
            print(f"✅ Found in RAG database (similarity: {similarity:.2f})")
            # Use RAG result as context for Ollama
            prompt = self.create_crisis_prompt(query_text, rag_result)
            return self.call_ollama(prompt)
        
        # Step 3: Fallback to Ollama with general crisis prompt
        print("⚠️ No specific match found, using AI response")
        prompt = self.create_crisis_prompt(query_text, "")
        return self.call_ollama(prompt)
    
    def create_crisis_prompt(self, query_text, context=""):
        """Create optimized prompt for crisis situations"""
        urgency = self.analyze_crisis_urgency(query_text)
        
        base_prompt = """You are CRISIS-AI, an offline emergency assistant. Respond in 50-150 words with 3-6 numbered steps.

RULES:
- Start with most life-threatening issue first
- Use simple, clear language for audio output
- Give actionable steps only
- No disclaimers or long explanations"""

        if urgency == "high":
            urgency_text = "\n🚨 HIGH URGENCY - Person may be in immediate danger!"
        else:
            urgency_text = "\n⚠️ Provide practical safety steps."
        
        context_text = ""
        if context and context.strip():
            context_text = f"\n\nRELEVANT INFO:\n{context}\n"
        
        final_prompt = f"""{base_prompt}{urgency_text}{context_text}

USER EMERGENCY: {query_text}

Respond with numbered steps:"""
        
        return final_prompt