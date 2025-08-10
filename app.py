from flask import Flask, request, jsonify
from flask_cors import CORS
import random
from datetime import datetime
from textblob import TextBlob  # Lightweight NLP (no model downloads needed)

app = Flask(__name__)
CORS(app)

# Conversation states
CONVERSATION_FLOW = [
    {"stage": "introduction", "prompts": [
        "Hi there! I'm your English practice buddy. What's your name?",
        "Hello! I'm excited to chat with you. How should I call you?",
        "Hey! I'm an AI English coach. What's your name?"
    ]},
    {"stage": "warmup", "prompts": [
        "Nice to meet you, {name}! How's your day going so far?",
        "Great to meet you, {name}! What's something interesting that happened today?",
        "Hello {name}! What brings you to practice English today?"
    ]},
    {"stage": "main", "prompts": [
        "Tell me more about that...",
        "What do you think about {topic}?",
        "How did that make you feel?",
        "Could you describe that in more detail?",
        "What was that experience like for you?"
    ]}
]

conversation_state = {"stage": "introduction", "name": None, "topics": []}

def get_natural_response(user_message):
    # Analyze sentiment and content
    analysis = TextBlob(user_message)
    sentiment = analysis.sentiment.polarity
    words = analysis.words
    
    # Update conversation state
    if conversation_state["stage"] == "introduction":
        # Extract name from "My name is X" or "I'm X" patterns
        if "my name is" in user_message.lower():
            name = user_message.lower().split("my name is")[1].strip().title()
        elif "i'm" in user_message.lower():
            name = user_message.lower().split("i'm")[1].strip().title()
        else:
            name = " ".join([word.capitalize() for word in words[:2]])
        
        conversation_state.update({
            "stage": "warmup",
            "name": name if len(name) > 1 else "Friend"
        })
        return random.choice(CONVERSATION_FLOW[1]["prompts"]).format(name=conversation_state["name"])
    
    elif conversation_state["stage"] == "warmup":
        conversation_state["stage"] = "main"
        # Extract topics for follow-up questions
        nouns = [word for (word, tag) in analysis.tags if tag.startswith('N')]
        conversation_state["topics"] = nouns[:3]
        return random.choice(CONVERSATION_FLOW[2]["prompts"]).format(
            topic=random.choice(conversation_state["topics"]) if conversation_state["topics"] else "that"
        )
    
    else:  # Main conversation
        # Keep track of topics mentioned
        new_nouns = [word for (word, tag) in analysis.tags if tag.startswith('N')]
        conversation_state["topics"].extend(new_nouns)
        
        # Vary responses based on sentiment
        if sentiment > 0.3:
            return "That sounds great! Tell me more..."
        elif sentiment < -0.3:
            return "I see. Would you like to talk more about that?"
        
        return random.choice(CONVERSATION_FLOW[2]["prompts"]).format(
            topic=random.choice(conversation_state["topics"]) if conversation_state["topics"] else "this"
        )

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({
            'response': "I didn't quite catch that. Could you say that again?",
            'correction': None
        })
    
    if conversation_state["stage"] == "introduction":
        response = random.choice(CONVERSATION_FLOW[0]["prompts"])
    else:
        response = get_natural_response(user_message)
    
    return jsonify({
        'response': response,
        'correction': None  # We'll add gentle corrections later
    })

@app.route('/api/start', methods=['GET'])
def start_conversation():
    conversation_state.update({"stage": "introduction", "name": None, "topics": []})
    return jsonify({
        'response': random.choice(CONVERSATION_FLOW[0]["prompts"]),
        'correction': None
    })

if __name__ == '__main__':
    app.run(debug=True)
