import google.generativeai as genai
import time
from dotenv import load_dotenv
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

load_dotenv()
API_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_key)
model = genai.GenerativeModel('models/gemini-2.5-flash')

@dataclass
class ConversationMemory:
    """Structure to hold conversation memory"""
    user_name: Optional[str] = None
    key_topics: List[str] = None
    emotional_patterns: List[str] = None
    coping_strategies: List[str] = None
    goals: List[str] = None
    triggers: List[str] = None
    progress_notes: List[str] = None
    session_count: int = 0
    last_session: Optional[str] = None
    conversation_history: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.key_topics is None:
            self.key_topics = []
        if self.emotional_patterns is None:
            self.emotional_patterns = []
        if self.coping_strategies is None:
            self.coping_strategies = []
        if self.goals is None:
            self.goals = []
        if self.triggers is None:
            self.triggers = []
        if self.progress_notes is None:
            self.progress_notes = []
        if self.conversation_history is None:
            self.conversation_history = []

class TherapyMemoryBot:
    def __init__(self, memory_file: str = "therapy_memory.json"):
        self.memory_file = memory_file
        self.memories: Dict[str, ConversationMemory] = {}
        self.load_memories()
    
    def load_memories(self):
        """Load memories from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    for user_id, memory_data in data.items():
                        self.memories[user_id] = ConversationMemory(**memory_data)
            print(f"Loaded memories for {len(self.memories)} users")
        except Exception as e:
            print(f"Error loading memories: {e}")
    
    def save_memories(self):
        """Save memories to file"""
        try:
            data = {user_id: asdict(memory) for user_id, memory in self.memories.items()}
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving memories: {e}")
    
    def get_or_create_memory(self, user_id: str) -> ConversationMemory:
        """Get or create user memory"""
        if user_id not in self.memories:
            self.memories[user_id] = ConversationMemory()
        return self.memories[user_id]
    
    def analyze_and_extract_info(self, user_input: str, memory: ConversationMemory):
        """Analyze user input and extract relevant information"""
        input_lower = user_input.lower()
        
        # Extract potential topics
        mental_health_keywords = [
            "anxiety", "depression", "stress", "panic", "worry", "fear",
            "sad", "lonely", "overwhelmed", "tired", "exhausted", "angry",
            "frustrated", "hopeless", "worthless", "therapy", "medication",
            "sleep", "insomnia", "relationships", "work", "family", "friends",
            "burnout", "ptsd", "trauma", "grief", "loss", "bipolar", "ocd"
        ]
        
        # Add new topics
        for keyword in mental_health_keywords:
            if keyword in input_lower and keyword not in memory.key_topics:
                memory.key_topics.append(keyword)
        
        # Extract name if mentioned
        name_patterns = ["my name is", "i'm", "im", "call me", "i am"]
        for pattern in name_patterns:
            if pattern in input_lower:
                words = user_input.split()
                pattern_words = pattern.split()
                for i, word in enumerate(words):
                    if word.lower() in pattern_words:
                        # Look for the next word that could be a name
                        for j in range(i + 1, min(i + 3, len(words))):
                            potential_name = words[j].strip(".,!?")
                            if potential_name.isalpha() and len(potential_name) > 1:
                                memory.user_name = potential_name
                                break
                        break
        
        # Extract emotional patterns
        emotion_indicators = {
            "anxiety": ["anxious", "nervous", "worried", "panic", "fear"],
            "depression": ["depressed", "sad", "hopeless", "empty", "worthless"],
            "stress": ["stressed", "overwhelmed", "pressure", "burnout"],
            "anger": ["angry", "frustrated", "irritated", "mad"],
            "loneliness": ["lonely", "isolated", "alone", "abandoned"],
            "fatigue": ["tired", "exhausted", "drained", "weary"]
        }
        
        for emotion, indicators in emotion_indicators.items():
            if any(indicator in input_lower for indicator in indicators):
                pattern = f"Experiencing {emotion} - {datetime.now().strftime('%Y-%m-%d')}"
                if pattern not in memory.emotional_patterns:
                    memory.emotional_patterns.append(pattern)
        
        # Extract coping strategies
        coping_keywords = {
            "meditation": ["meditate", "meditation", "mindfulness"],
            "exercise": ["exercise", "gym", "workout", "running", "walk"],
            "breathing": ["breathing", "breath", "breathe"],
            "journaling": ["journal", "write", "writing", "diary"],
            "therapy": ["therapy", "therapist", "counseling", "counselor"],
            "medication": ["medication", "pills", "antidepressant", "meds"],
            "sleep": ["sleep", "rest", "nap"],
            "social": ["friends", "family", "talk", "support group"]
        }
        
        for strategy, keywords in coping_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                if strategy not in memory.coping_strategies:
                    memory.coping_strategies.append(strategy)
        
        # Extract goals
        goal_patterns = ["want to", "goal", "hope to", "trying to", "working on"]
        for pattern in goal_patterns:
            if pattern in input_lower:
                # Extract the sentence containing the goal
                sentences = user_input.split('.')
                for sentence in sentences:
                    if pattern in sentence.lower():
                        goal = f"Goal: {sentence.strip()[:100]}..."
                        if goal not in memory.goals:
                            memory.goals.append(goal)
                        break
        
        # Keep memory manageable
        memory.key_topics = memory.key_topics[-15:]
        memory.emotional_patterns = memory.emotional_patterns[-10:]
        memory.coping_strategies = memory.coping_strategies[-10:]
        memory.goals = memory.goals[-5:]
    
    def build_memory_context(self, memory: ConversationMemory) -> str:
        """Build context string from memory"""
        context_parts = []
        
        if memory.user_name:
            context_parts.append(f"User's name: {memory.user_name}")
        
        if memory.session_count > 0:
            context_parts.append(f"This is session #{memory.session_count + 1}")
        
        if memory.key_topics:
            recent_topics = memory.key_topics[-5:]
            context_parts.append(f"Recent topics: {', '.join(recent_topics)}")
        
        if memory.emotional_patterns:
            recent_patterns = memory.emotional_patterns[-3:]
            context_parts.append(f"Recent emotional patterns: {', '.join(recent_patterns)}")
        
        if memory.coping_strategies:
            context_parts.append(f"Coping strategies user has mentioned: {', '.join(memory.coping_strategies)}")
        
        if memory.goals:
            recent_goals = memory.goals[-2:]
            context_parts.append(f"User's goals: {', '.join(recent_goals)}")
        
        if memory.last_session:
            context_parts.append(f"Last session: {memory.last_session}")
        
        # Add recent conversation snippets
        if memory.conversation_history:
            recent_conversations = memory.conversation_history[-3:]
            context_parts.append("Recent conversation snippets:")
            for conv in recent_conversations:
                context_parts.append(f"  User: {conv['user'][:80]}...")
                context_parts.append(f"  Bot: {conv['bot'][:80]}...")
        
        return "\n".join(context_parts) if context_parts else "This is a new user with no previous conversation history."
    
    def get_therapy_response(self, user_input: str, user_id: str = "default_user") -> str:
        """Main function to get therapy response with memory"""
        try:
            # Get or create memory
            memory = self.get_or_create_memory(user_id)
            
            # Analyze input and extract information
            self.analyze_and_extract_info(user_input, memory)
            
            # Build context from memory
            context = self.build_memory_context(memory)
            
            # Create the therapy prompt with memory context
            therapy_prompt = (
                f"You are a compassionate, conversational mental health chatbot that sounds like a warm, thoughtful therapist friend.\n"
                f"Always acknowledge the user's feelings with empathy.\n"
                f"Offer concise, friendly, and emotionally intelligent advice based on what the user shared.\n"
                f"Ask meaningful, open-ended follow-up questions that help the user reflect deeper.\n"
                f"Give practical suggestions when appropriate, without overwhelming them.\n"
                f"Keep your responses warm, human, and easy to relate to—like a therapist who also sends memes.\n"
                f"Speak in a natural tone, not clinical or robotic.\n"
                f"Keep responses 3-5 sentences max unless the user asks for more detail.\n"
                f"Sprinkle in emojis when it fits, to make the vibe feel soft and safe.\n"
                f"Be curious, caring, and conversational. Help the user open up, feel supported, and gently guided forward.\n\n"
                f"MEMORY CONTEXT (use this to personalize your response):\n"
                f"{context}\n\n"
                f"User's current message: {user_input}\n\n"
                f"Therapist response:"
            )
            
            # Generate response
            response = model.generate_content(therapy_prompt)
            bot_response = response.text.strip()
            
            # Update memory with conversation
            memory.conversation_history.append({
                "user": user_input,
                "bot": bot_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep conversation history manageable
            memory.conversation_history = memory.conversation_history[-10:]
            
            # Update session info
            memory.session_count += 1
            memory.last_session = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Save memories
            self.save_memories()
            
            return bot_response
            
        except Exception as e:
            print(f"Error in get_therapy_response: {e}")
            return "I'm here for you, but I'm having some technical difficulties right now. Can you try again? 💛"
    
    def get_user_summary(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Get a summary of user's therapy journey"""
        if user_id not in self.memories:
            return {"error": "No memory found for this user"}
        
        memory = self.memories[user_id]
        return {
            "user_name": memory.user_name,
            "session_count": memory.session_count,
            "key_topics": memory.key_topics,
            "emotional_patterns": memory.emotional_patterns,
            "coping_strategies": memory.coping_strategies,
            "goals": memory.goals,
            "last_session": memory.last_session,
            "total_conversations": len(memory.conversation_history)
        }
    
    def clear_user_memory(self, user_id: str = "default_user"):
        """Clear memory for a specific user"""
        if user_id in self.memories:
            del self.memories[user_id]
            self.save_memories()
            return True
        return False

# Create global instance
therapy_bot = TherapyMemoryBot()

def get_therapy_response(user_input: str, user_id: str = "default_user") -> str:
    """Function to get therapy response with memory - this is what main.py imports"""
    return therapy_bot.get_therapy_response(user_input, user_id)

def get_user_summary(user_id: str = "default_user") -> Dict[str, Any]:
    """Get user therapy summary"""
    return therapy_bot.get_user_summary(user_id)

def clear_user_memory(user_id: str = "default_user") -> bool:
    """Clear user memory"""
    return therapy_bot.clear_user_memory(user_id)

# Optional: Keep the terminal version in a separate function
def run_terminal_chat():
    """Run the chatbot in terminal mode with memory"""
    print("Mental Health Chatbot with Memory - Terminal Mode")
    print("Type 'exit' to quit, 'summary' to see your therapy summary, 'clear' to clear memory\n")
    
    user_id = input("Enter your user ID (or press Enter for default): ").strip()
    if not user_id:
        user_id = "default_user"
    
    print(f"Starting session for user: {user_id}\n")
    
    while True:
        prompt = input("You: ")
        if prompt.lower() == "exit":
            print("Therapist: Take care of yourself. You're doing your best. 💛")
            break
        elif prompt.lower() == "summary":
            summary = get_user_summary(user_id)
            print(f"\nTherapy Summary:")
            print(f"Name: {summary.get('user_name', 'Not provided')}")
            print(f"Sessions: {summary.get('session_count', 0)}")
            print(f"Topics: {', '.join(summary.get('key_topics', [])[:5])}")
            print(f"Coping strategies: {', '.join(summary.get('coping_strategies', []))}")
            print(f"Last session: {summary.get('last_session', 'Never')}")
            print()
            continue
        elif prompt.lower() == "clear":
            if clear_user_memory(user_id):
                print("Memory cleared successfully!\n")
            else:
                print("No memory to clear.\n")
            continue
        
        try:
            reply = get_therapy_response(prompt, user_id)
            print("Therapist:", reply, "\n")
        except Exception as e:
            print(f"An error occurred: {e}")
        time.sleep(1)

# Only run terminal chat if this file is executed directly
if __name__ == "__main__":
    run_terminal_chat()