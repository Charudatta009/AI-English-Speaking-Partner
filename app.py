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
from textblob import TextBlob
import random
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Hugging Face Inference API (Free tier)
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HF_TOKEN = os.getenv('HF_API_TOKEN')

# Conversation memory
conversation_history = []

def query_llm(prompt):
    """Get LLM suggestions for more natural responses"""
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 80,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        return response.json()[0]['generated_text'].strip('"\'')
    except:
        return None

def generate_response(user_message):
    """Generate human-like response with LLM assistance"""
    # Analyze user input
    analysis = TextBlob(user_message)
    nouns = [word for (word, tag) in analysis.tags if tag.startswith('N')]
    verbs = [word for (word, tag) in analysis.tags if tag.startswith('V')]
    
    # Store conversation context
    context = {
        'last_user_message': user_message,
        'topics': nouns[:3],
        'actions': verbs[:2],
        'history': conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
    }
    
    # Create LLM prompt for natural response
    llm_prompt = f"""You're an English conversation partner. The student said:
"{user_message}"

Respond naturally while:
1. Continuing the conversation flow
2. Showing genuine interest
3. Keeping response under 2 sentences
4. Using {context['topics']} if relevant

Response:"""
    
    # Get LLM suggestion (fallback to rules if API fails)
    llm_response = query_llm(llm_prompt)
    
    if llm_response:
        return llm_response
    
    # Fallback rules
    responses = [
        f"That's interesting! What do you like about {random.choice(nouns) if nouns else 'that'}?",
        "I see. Could you tell me more about that?",
        "What was that experience like for you?",
        "How did that make you feel?",
        "That's fascinating! What else have you been up to?"
    ]
    return random.choice(responses)

@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').strip()
    
    if not user_message:
        return jsonify({'response': "I didn't catch that. Could you repeat?"})
    
    # Generate response
    response = generate_response(user_message)
    
    # Store conversation
    conversation_history.append({
        'user': user_message,
        'bot': response,
        'time': datetime.now().isoformat()
    })
    
    # Keep last 5 exchanges
    if len(conversation_history) > 5:
        conversation_history.pop(0)
    
    return jsonify({
        'response': response,
        'correction': get_gentle_correction(user_message)
    })

def get_gentle_correction(text):
    """Provide occasional corrections"""
    common_mistakes = {
        r'\bi (is|am)\b': 'I am',
        r'\b(he|she) (are)\b': r'\1 is',
        r'\b(we|they) (is)\b': r'\1 are',
        r'\byesterday i (go|eat|see)\b': r'yesterday I \1ed'
    }
    
    if random.random() > 0.7:  # 30% chance to correct
        for pattern, fix in common_mistakes.items():
            if re.search(pattern, text, re.IGNORECASE):
                corrected = re.sub(pattern, fix, text, flags=re.IGNORECASE)
                return f"Just to note: we usually say '{corrected}'"
    return None

@app.route('/api/start', methods=['GET'])
def start_conversation():
    conversation_history.clear()
    starters = [
        "Hey there! What's on your mind today?",
        "Hi! What would you like to chat about?",
        "Hello! What's something interesting that happened recently?"
    ]
    return jsonify({'response': random.choice(starters)})

if __name__ == '__main__':
    app.run(debug=True)

# if __name__ == '__main__':
#     app.run(debug=True)


