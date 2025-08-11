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


from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import re
import random

# Initialize environment
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HF_TOKEN = "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"

# Validate token on startup
if not HF_TOKEN:
    print("Warning: HF_API_TOKEN not found. Using fallback responses.")

conversation_history = []

def query_llm(prompt):
    """Safely query LLM with enhanced error handling"""
    if not HF_TOKEN:
        return None
        
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 100,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json=payload,
            timeout=15  # Increased timeout for Render
        )
        
        # Check for API errors
        if response.status_code == 401:
            print("Invalid Hugging Face token. Check your HF_API_TOKEN.")
            return None
        elif response.status_code == 503:
            print("Model loading... please try again later")
            return None
            
        response.raise_for_status()
        return response.json()[0]['generated_text'].strip('"\'')
    except Exception as e:
        print(f"LLM Error: {str(e)}")
        return None

def generate_response(user_message):
    """Generate response with LLM fallback logic"""
    # Try LLM first if token exists
    if HF_TOKEN:
        prompt = f"""As an English tutor, respond to this naturally:
Student: {user_message}
Rules:
1. Respond in 1-2 sentences
2. Gently correct major errors
3. Ask relevant follow-ups
4. Keep it conversational

Response:"""
        
        llm_response = query_llm(prompt)
        if llm_response:
            return llm_response
    
    # Fallback responses if LLM fails
    fallbacks = [
        "Interesting! Tell me more about that.",
        "How did that make you feel?",
        "Could you explain that in more detail?",
        "What was that experience like for you?"
    ]
    return random.choice(fallbacks)

def get_gentle_correction(text):
    corrections = {
        r'\bi (is|am)\b': 'I am',
        r'\b(he|she) (are)\b': r'\1 is',
        r'\b(we|they) (is)\b': r'\1 are',
        r'\byesterday i (go|eat|see)\b': r'yesterday I \1ed'
    }
    
    if random.random() > 0.7:  # 30% chance to correct
        for pattern, fix in corrections.items():
            if re.search(pattern, text, re.IGNORECASE):
                corrected = re.sub(pattern, fix, text, flags=re.IGNORECASE)
                return f"Note: We usually say '{corrected}'"
    return None

@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').strip()
    
    if not user_message:
        return jsonify({'response': "Could you repeat that?"})
    
    response = generate_response(user_message)
    conversation_history.append(user_message[:100])  # Store truncated message
    
    return jsonify({
        'response': response,
        'correction': get_gentle_correction(user_message)
    })

@app.route('/api/start', methods=['GET'])
def start_conversation():
    conversation_history.clear()
    starters = [
        "Hi! What would you like to practice today?",
        "Hello! Tell me something interesting.",
        "Let's practice English! What's on your mind?"
    ]
    return jsonify({'response': random.choice(starters)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)






