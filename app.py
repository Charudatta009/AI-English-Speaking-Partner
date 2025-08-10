# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import random
# from datetime import datetime
# from textblob import TextBlob  # Lightweight NLP (no model downloads needed)

# app = Flask(__name__)
# CORS(app)

# # Conversation states
# CONVERSATION_FLOW = [
#     {"stage": "introduction", "prompts": [
#         "Hi there! I'm your English practice buddy. What's your name?",
#         "Hello! I'm excited to chat with you. How should I call you?",
#         "Hey! I'm an AI English coach. What's your name?"
#     ]},
#     {"stage": "warmup", "prompts": [
#         "Nice to meet you, {name}! How's your day going so far?",
#         "Great to meet you, {name}! What's something interesting that happened today?",
#         "Hello {name}! What brings you to practice English today?"
#     ]},
#     {"stage": "main", "prompts": [
#         "Tell me more about that...",
#         "What do you think about {topic}?",
#         "How did that make you feel?",
#         "Could you describe that in more detail?",
#         "What was that experience like for you?"
#     ]}
# ]

# conversation_state = {"stage": "introduction", "name": None, "topics": []}

# def get_natural_response(user_message):
#     # Analyze sentiment and content
#     analysis = TextBlob(user_message)
#     sentiment = analysis.sentiment.polarity
#     words = analysis.words
    
#     # Update conversation state
#     if conversation_state["stage"] == "introduction":
#         # Extract name from "My name is X" or "I'm X" patterns
#         if "my name is" in user_message.lower():
#             name = user_message.lower().split("my name is")[1].strip().title()
#         elif "i'm" in user_message.lower():
#             name = user_message.lower().split("i'm")[1].strip().title()
#         else:
#             name = " ".join([word.capitalize() for word in words[:2]])
        
#         conversation_state.update({
#             "stage": "warmup",
#             "name": name if len(name) > 1 else "Friend"
#         })
#         return random.choice(CONVERSATION_FLOW[1]["prompts"]).format(name=conversation_state["name"])
    
#     elif conversation_state["stage"] == "warmup":
#         conversation_state["stage"] = "main"
#         # Extract topics for follow-up questions
#         nouns = [word for (word, tag) in analysis.tags if tag.startswith('N')]
#         conversation_state["topics"] = nouns[:3]
#         return random.choice(CONVERSATION_FLOW[2]["prompts"]).format(
#             topic=random.choice(conversation_state["topics"]) if conversation_state["topics"] else "that"
#         )
    
#     else:  # Main conversation
#         # Keep track of topics mentioned
#         new_nouns = [word for (word, tag) in analysis.tags if tag.startswith('N')]
#         conversation_state["topics"].extend(new_nouns)
        
#         # Vary responses based on sentiment
#         if sentiment > 0.3:
#             return "That sounds great! Tell me more..."
#         elif sentiment < -0.3:
#             return "I see. Would you like to talk more about that?"
        
#         return random.choice(CONVERSATION_FLOW[2]["prompts"]).format(
#             topic=random.choice(conversation_state["topics"]) if conversation_state["topics"] else "this"
#         )

# @app.route('/api/chat', methods=['POST'])
# def chat():
#     data = request.get_json()
#     user_message = data.get('message', '').strip()
    
#     if not user_message:
#         return jsonify({
#             'response': "I didn't quite catch that. Could you say that again?",
#             'correction': None
#         })
    
#     if conversation_state["stage"] == "introduction":
#         response = random.choice(CONVERSATION_FLOW[0]["prompts"])
#     else:
#         response = get_natural_response(user_message)
    
#     return jsonify({
#         'response': response,
#         'correction': None  # We'll add gentle corrections later
#     })

# @app.route('/api/start', methods=['GET'])
# def start_conversation():
#     conversation_state.update({"stage": "introduction", "name": None, "topics": []})
#     return jsonify({
#         'response': random.choice(CONVERSATION_FLOW[0]["prompts"]),
#         'correction': None
#     })

# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, request, jsonify, session
from flask_cors import CORS
import random
from textblob import TextBlob
from datetime import datetime
from flask_session import Session
from dotenv import load_dotenv
import os
import secrets

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS with credentials support
CORS(app, supports_credentials=True, origins=[
    "http://localhost:3000",  # For development
    "https://your-frontend-domain.com"  # For production
])

# Configure server-side sessions
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour session lifetime
Session(app)

# Conversation states
CONVERSATION_FLOW = {
    "introduction": [
        "Hi there! I'm your English practice buddy. What's your name?",
        "Hello! I'm excited to chat with you. How should I call you?",
        "Hey! I'm an AI English coach. What's your name?"
    ],
    "warmup": [
        "Nice to meet you, {name}! How's your day going so far?",
        "Great to meet you, {name}! What's something interesting that happened today?",
        "Hello {name}! What brings you to practice English today?"
    ],
    "main": [
        "Tell me more about that...",
        "What do you think about {topic}?",
        "How did that make you feel?",
        "Could you describe that in more detail?",
        "What was that experience like for you?"
    ]
}

@app.before_request
def initialize_session():
    """Initialize session variables if they don't exist"""
    if 'conversation_stage' not in session:
        session['conversation_stage'] = "introduction"
        session['user_name'] = None
        session['topics'] = []
        session['previous_responses'] = []

def get_natural_response(user_message):
    """Generate context-aware responses"""
    analysis = TextBlob(user_message)
    
    # Handle introduction stage
    if session['conversation_stage'] == "introduction":
        # Extract name from message
        name = extract_name(user_message)
        session['user_name'] = name if name else "Friend"
        session['conversation_stage'] = "warmup"
        response = random.choice(CONVERSATION_FLOW["warmup"]).format(name=session['user_name'])
    
    # Handle warmup stage
    elif session['conversation_stage'] == "warmup":
        session['conversation_stage'] = "main"
        nouns = extract_nouns(analysis)
        session['topics'] = nouns[:3]
        response = random.choice(CONVERSATION_FLOW["main"]).format(
            topic=random.choice(session['topics']) if session['topics'] else "that"
        )
    
    # Main conversation stage
    else:
        nouns = extract_nouns(analysis)
        session['topics'].extend(nouns)
        
        # Avoid repeating recent responses
        available_responses = [
            r for r in CONVERSATION_FLOW["main"] 
            if r not in session['previous_responses'][-2:]
        ]
        
        response = random.choice(available_responses or CONVERSATION_FLOW["main"]).format(
            topic=random.choice(session['topics']) if session['topics'] else "this"
        )
    
    # Store recent responses to avoid repetition
    session['previous_responses'] = (session.get('previous_responses', []) + [response])[-5:]
    
    return response

def extract_name(text):
    """Extract name from common patterns"""
    text = text.lower()
    if "my name is" in text:
        return text.split("my name is")[1].strip().title()
    elif "i'm" in text:
        return text.split("i'm")[1].strip().title()
    elif "name is" in text:
        return text.split("name is")[1].strip().title()
    return None

def extract_nouns(analysis):
    """Extract nouns from text analysis"""
    return [word for (word, tag) in analysis.tags if tag.startswith('N')]

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with session persistence"""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({
            'response': "I didn't quite catch that. Could you say that again?",
            'correction': None
        })
    
    response = get_natural_response(user_message)
    return jsonify({
        'response': response,
        'correction': get_gentle_correction(user_message)
    })

def get_gentle_correction(text):
    """Provide occasional gentle corrections"""
    common_mistakes = {
        r'\bi (is|am)\b': 'I am',
        r'\b(he|she) (are)\b': r'\1 is',
        r'\b(we|they) (is)\b': r'\1 are',
        r'\bdon\'t has\b': "don't have"
    }
    
    # Only correct 30% of the time to avoid interrupting flow
    if random.random() < 0.3:
        for pattern, correction in common_mistakes.items():
            if re.search(pattern, text, re.IGNORECASE):
                corrected = re.sub(pattern, correction, text, flags=re.IGNORECASE)
                if corrected.lower() != text.lower():
                    return f"Just a small note: we usually say '{corrected}'"
    return None

@app.route('/api/start', methods=['GET'])
def start_conversation():
    """Reset conversation state"""
    session.clear()
    session['conversation_stage'] = "introduction"
    return jsonify({
        'response': random.choice(CONVERSATION_FLOW["introduction"]),
        'correction': None
    })

if __name__ == '__main__':
    app.run(debug=True)
