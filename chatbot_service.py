"""
PawParties AI Chatbot Service
Handles user queries with intelligent intent detection, fuzzy matching for typos,
and comprehensive training data integration.
"""

import time
from difflib import SequenceMatcher
from chatbot_training_data import (
    SYSTEM_OVERVIEW, USER_ROLES, FEATURES_GUIDE, FEES_STRUCTURE,
    DOCUMENTS_REQUIRED, BLOCKCHAIN_INFO, TROUBLESHOOTING, FAQ_DATABASE,
    INTENT_KEYWORDS, SYSTEM_RULES
)


class ChatbotService:
    """Comprehensive chatbot service with training data and fuzzy matching"""
    def __init__(self, blockchain, gemini_client=None):
        self.blockchain = blockchain
        self.gemini_client = gemini_client
        self.response_delay = 5  # 5 second delay before responding
        
    def handle_message(self, user_id, message):
        """Handle incoming messages with delay and intent detection"""
        # Add 5 second delay before responding
        time.sleep(self.response_delay)
        
        # Detect user intent even with spelling mistakes
        intent = self._detect_intent_fuzzy(message)
        
        # Try to get specific answer first
        specific_answer = self._get_specific_answer(message, intent)
        if specific_answer:
            return specific_answer
        
        # Otherwise use AI or general fallback
        return self._handle_general_question(message, intent)
    
    def _detect_intent_fuzzy(self, message):
        """Detect user intent with fuzzy matching for spelling mistakes"""
        message_lower = message.lower()
        best_intent = None
        best_score = 0
        
        for intent, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                # Check exact match first
                if keyword in message_lower:
                    return intent
                
                # Check fuzzy match for spelling mistakes
                for word in message_lower.split():
                    similarity = self._similarity(word, keyword)
                    if similarity > 0.75 and similarity > best_score:  # 75% similarity threshold
                        best_score = similarity
                        best_intent = intent
        
        return best_intent if best_score > 0.75 else "general"
    
    def _similarity(self, a, b):
        """Calculate similarity between two strings (0 to 1)"""
        return SequenceMatcher(None, a, b).ratio()
    
    def _get_specific_answer(self, message, intent):
        """Get specific answers from training data based on intent"""
        message_lower = message.lower()
        
        # Check FAQ database first (with fuzzy matching)
        best_match = None
        best_score = 0
        
        for question, answer in FAQ_DATABASE.items():
            similarity = self._similarity(message_lower, question.lower())
            if similarity > best_score:
                best_score = similarity
                best_match = answer
        
        # If we found a good match in FAQ (>60% similarity)
        if best_score > 0.6:
            return best_match
        
        # Return intent-based specific answers
        if intent == "registration":
            return self._get_registration_info(message_lower)
        elif intent == "transfer":
            return self._get_transfer_info(message_lower)
        elif intent == "inheritance":
            return self._get_inheritance_info(message_lower)
        elif intent == "fees":
            return self._get_fees_info(message_lower)
        elif intent == "documents":
            return self._get_documents_info(message_lower)
        elif intent == "appointment":
            return self._get_appointment_info(message_lower)
        elif intent == "blockchain":
            return self._get_blockchain_info(message_lower)
        elif intent == "search":
            return self._get_search_info(message_lower)
        elif intent == "history":
            return self._get_history_info(message_lower)
        elif intent == "login":
            return self._get_login_help(message_lower)
        elif intent == "roles":
            return self._get_roles_info(message_lower)
        
        return None  # No specific answer found
    
    def _get_registration_info(self, message):
        """Detailed registration information"""
        feature = FEATURES_GUIDE["add_property"]
        
        if any(word in message for word in ["how", "process", "step"]):
            steps = "\n".join([f"  {step}" for step in feature["process_steps"]])
            return f"📝 Property Registration Process:\n{steps}\n\n💰 Fee: {feature['fees']}\n⏱️ Time: {feature['time']}"
        
        elif any(word in message for word in ["document", "paper", "need", "require"]):
            docs = "\n• ".join(feature["required_documents"])
            return f"📄 Documents Required for Registration:\n• {docs}\n\n💰 Fee: {feature['fees']}"
        
        elif any(word in message for word in ["fee", "cost", "charge"]):
            return f"💰 Property Registration Fee: {feature['fees']}\n\nThis is a one-time fee that covers document verification, blockchain entry, and property key generation.\n\n⏱️ Processing time: {feature['time']}"
        
        else:
            return f"🏠 Property Registration:\n\n{feature['description']}\n\nWho can register: {feature['who_can_use']}\nFee: {feature['fees']}\nTime: {feature['time']}\n\nAccess: {feature['how_to_access']}"
    
    def _get_transfer_info(self, message):
        """Detailed transfer information"""
        feature = FEATURES_GUIDE["transfer_property"]
        
        if any(word in message for word in ["how", "process", "step"]):
            steps = "\n".join([f"  {step}" for step in feature["process_steps"][:6]])
            return f"📝 Property Transfer Process:\n{steps}\n...\n\n💰 Fee: ₹3,000 + 2% stamp duty + 5% registration fee\n⏱️ Time: {feature['time']}"
        
        elif any(word in message for word in ["fee", "cost", "charge"]):
            fees = feature["fees"]
            return f"💰 Transfer Fees:\n• Base fee: {fees['base']}\n• Stamp duty: {fees['stamp_duty']}\n• Registration: {fees['registration_fee']}\n\nExample: {fees['example']}"
        
        elif any(word in message for word in ["document", "paper", "need"]):
            docs = "\n• ".join(feature["required_documents"])
            return f"📄 Documents for Transfer:\n• {docs}"
        
        else:
            important = "\n⚠️ ".join(feature["important_notes"])
            return f"📝 Property Transfer:\n\n{feature['description']}\n\n⚠️ {important}\n\n💰 Fee: ₹3,000 + 2% + 5%\n⏱️ Time: {feature['time']}"
    
    def _get_inheritance_info(self, message):
        """Detailed inheritance information"""
        feature = FEATURES_GUIDE["inherit_property"]
        docs = "\n• ".join(feature["required_documents"])
        fees = feature["fees"]
        
        return f"👨‍👩‍👧‍👦 Property Inheritance:\n\n{feature['description']}\n\n📄 Required Documents:\n• {docs}\n\n💰 Fees:\n• Base: {fees['base']}\n• Stamp duty: {fees['stamp_duty']}\n• Example: {fees['example']}\n\n⏱️ Time: {feature['time']}"
    
    def _get_fees_info(self, message):
        """Complete fee information"""
        reg = FEES_STRUCTURE["registration"]
        trans = FEES_STRUCTURE["transfer"]
        inher = FEES_STRUCTURE["inheritance"]
        
        return f"""💰 Complete Fee Structure:

1️⃣ Registration: {reg['amount']}
   One-time fee for new property

2️⃣ Transfer:
   • Base: {trans['base_fee']}
   • Stamp duty: {trans['stamp_duty']}
   • Registration: {trans['registration_fee']}
   Example: {trans['example']}

3️⃣ Inheritance:
   • Base: {inher['base_fee']}
   • Stamp duty: {inher['stamp_duty']}
   Example: {inher['example']}

4️⃣ Other Services:
   • Document verification: {FEES_STRUCTURE['document_verification']}
   • Appointments: {FEES_STRUCTURE['appointment']}
   • History reports: {FEES_STRUCTURE['history_report']}"""
    
    def _get_documents_info(self, message):
        """Document requirements information"""
        if any(word in message for word in ["transfer", "sell"]):
            docs = "\n• ".join(DOCUMENTS_REQUIRED["transfer"])
            return f"📄 Documents for Transfer:\n• {docs}"
        
        elif any(word in message for word in ["inherit", "succession"]):
            docs = "\n• ".join(DOCUMENTS_REQUIRED["inheritance"])
            return f"📄 Documents for Inheritance:\n• {docs}"
        
        else:
            docs = "\n• ".join(DOCUMENTS_REQUIRED["registration"])
            return f"📄 Documents for Registration:\n• {docs}"
    
    def _get_appointment_info(self, message):
        """Appointment system information"""
        feature = FEATURES_GUIDE["appointments"]
        
        if any(word in message for word in ["how", "book", "schedule"]):
            steps = "\n".join(feature["how_to_book"])
            return f"📅 How to Book Appointment:\n\n{steps}\n\n✅ Fees: {feature['fees']}"
        
        else:
            types = "\n• ".join(feature["appointment_types"])
            return f"📅 Appointment System:\n\n{feature['description']}\n\nTypes:\n• {types}\n\n✅ {feature['fees']}\n\nAccess: {feature['how_to_access']}"
    
    def _get_blockchain_info(self, message):
        """Blockchain technology information"""
        if any(word in message for word in ["secure", "security", "safe"]):
            security = "\n• ".join(BLOCKCHAIN_INFO["security"])
            return f"🔐 Blockchain Security:\n• {security}\n\nYour property data is 100% secure and tamper-proof!"
        
        elif any(word in message for word in ["how", "work"]):
            how = "\n• ".join(BLOCKCHAIN_INFO["how_it_works"])
            return f"🔗 How Blockchain Works:\n• {how}"
        
        else:
            benefits = "\n• ".join(BLOCKCHAIN_INFO["benefits"])
            return f"🔗 Blockchain Technology:\n\n{BLOCKCHAIN_INFO['what_is_it']}\n\n✅ Benefits:\n• {benefits}"
    
    def _get_search_info(self, message):
        """Search functionality information"""
        feature = FEATURES_GUIDE["search_property"]
        options = "\n• ".join(feature["search_options"])
        info = "\n• ".join(feature["what_you_can_see"])
        
        return f"🔍 Property Search:\n\nSearch by:\n• {options}\n\nYou can view:\n• {info}\n\nAccess: {feature['how_to_access']}"
    
    def _get_history_info(self, message):
        """Property history information"""
        feature = FEATURES_GUIDE["property_history"]
        shows = "\n• ".join(feature["what_it_shows"])
        
        return f"📜 Property History:\n\n{feature['description']}\n\nShows:\n• {shows}\n\nAccess: {feature['how_to_access']}"
    
    def _get_login_help(self, message):
        """Login and password help"""
        if any(word in message for word in ["forgot", "reset", "password"]):
            return f"🔐 Password Reset:\n\n{TROUBLESHOOTING['login_issues']['forgot_password']}\n\nFor security reasons, only administrators can manually reset passwords."
        
        else:
            issues = TROUBLESHOOTING['login_issues']
            return f"🔐 Login Help:\n\n• Forgot password: {issues['forgot_password']}\n• Account locked: {issues['account_locked']}\n• Wrong credentials: {issues['wrong_credentials']}"
    
    def _get_roles_info(self, message):
        """User roles and permissions"""
        result = "👥 User Roles in PawParties:\n\n"
        
        for role_key, role_info in USER_ROLES.items():
            can_do = "\n   ✅ ".join(role_info["can_do"][:3])
            result += f"{'🔵' if role_key == 'user' else '🟢' if role_key == 'officer' else '🔴'} {role_info['name']}:\n   ✅ {can_do}\n   ... and more\n\n"
        
        return result.strip()
    
    def _get_system_context(self):
        """Build comprehensive system context for AI from training data"""
        context = f"""You are PawParties AI Assistant, an expert guide for India's Property Registration Blockchain System.

SYSTEM OVERVIEW:
{SYSTEM_OVERVIEW}

USER ROLES:
"""
        for role, info in USER_ROLES.items():
            can_do = ", ".join(info["can_do"][:5])
            context += f"- {info['name']}: Can {can_do}\n"
        
        context += f"""
KEY FEATURES:
"""
        for feature_key, feature in list(FEATURES_GUIDE.items())[:6]:
            context += f"- {feature['name']}: {feature['description']}\n"
        
        context += f"""
FEES:
- Registration: {FEES_STRUCTURE['registration']['amount']}
- Transfer: {FEES_STRUCTURE['transfer']['base_fee']} + stamp duty
- Inheritance: {FEES_STRUCTURE['inheritance']['base_fee']} + stamp duty

BLOCKCHAIN SECURITY:
{BLOCKCHAIN_INFO['what_is_it']}

RESPONSE GUIDELINES:
- Be helpful, professional, and friendly
- Use emojis to make responses engaging 😊
- Provide specific, accurate information from the knowledge base
- Keep answers concise (2-4 sentences) unless user asks for details
- Always guide users to the right feature/page
- If you don't know something, suggest scheduling an appointment with an officer
- Handle spelling mistakes gracefully - understand user intent
"""
        return context

    def _handle_general_question(self, message, intent=None):
        """Handle questions using Gemini AI with full training data context"""
        if self.gemini_client:
            try:
                system_context = self._get_system_context()
                full_prompt = f"""{system_context}

User Intent Detected: {intent or 'general'}
User Question: {message}

Provide a helpful, accurate response based on the knowledge base above. Be specific and actionable."""
                
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=full_prompt
                )
                return response.text
            except Exception as e:
                # Silently fall back to offline responses
                return self._get_fallback_response(message, intent)
        else:
            return self._get_fallback_response(message, intent)
    
    def _get_fallback_response(self, message, intent=None):
        """Enhanced fallback with intent-based responses"""
        message_lower = message.lower()
        
        # Greetings
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'namaste']):
            return "Hello! 👋 Welcome to PawParties Property System. I'm your AI assistant trained on all features. Ask me about registration, transfers, inheritance, fees, appointments, blockchain, or any issues you're facing!"
        
        # Thanks
        if any(word in message_lower for word in ['thank', 'thanks']):
            return "You're very welcome! 😊 I'm here to help anytime you have questions about the property system. Feel free to ask anything!"
        
        # Use intent-based responses if we detected intent
        if intent and intent != "general":
            specific = self._get_specific_answer(message_lower, intent)
            if specific:
                return specific
        
        # Help/General
        return """I'm your PawParties AI Assistant! 🤖 I can help with:

🏠 Property Registration & Transfers
👨‍👩‍👧‍👦 Inheritance Processing  
💰 Fees & Charges
📄 Document Requirements
📅 Appointments & Scheduling
🔍 Property Search & History
🔐 Blockchain & Security
🛠️ Troubleshooting Issues
👥 User Roles & Permissions

Just ask your question - I can understand even if there are spelling mistakes! What would you like to know?"""
