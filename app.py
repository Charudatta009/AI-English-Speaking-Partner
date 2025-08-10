from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import random

app = Flask(__name__)
CORS(app)

# Enhanced conversation starters
CONVERSATION_STARTERS = [
    "What are your favorite hobbies?",
    "Can you describe what you did yesterday?",
    "Tell me about your favorite place to visit.",
    "How do you feel about modern technology?",
    "If you could travel anywhere in the world, where would you go?"
]

# Expanded common mistakes dictionary
COMMON_MISTAKES = {
    r'\b(I|you|we|they) is\b': r'\1 are',
    r'\b(he|she|it) are\b': r'\1 is',
    r'\b(I|you|we|they) was\b': r'\1 were',
    r'\b(he|she|it) were\b': r'\1 was',
    r'\bhe go\b': 'he goes',
    r'\bshe like\b': 'she likes',
    r'\bthey is\b': 'they are',
    r'\bi has\b': 'I have',
    r'\byou was\b': 'you were',
    r'\bdon\'t has\b': "don't have",
    r'\bdoesn\'t has\b': "doesn't have"
}

def check_grammar(text):
    corrections = []
    for mistake, correction in COMMON_MISTAKES.items():
        if re.search(mistake, text, re.IGNORECASE):
            corrected = re.sub(mistake, correction, text, flags=re.IGNORECASE)
            corrections.append(corrected)
    
    if corrections:
        return corrections[0]  # Return the first correction found
    return None

def generate_response(user_message):
    correction = check_grammar(user_message)
    
    # Enhanced response generation
    if len(user_message.split()) < 3:
        response = "Could you expand on that a bit more?"
    elif user_message.endswith('?'):
        response = random.choice([
            "That's an interesting question. What do you think about it yourself?",
            "I'd love to hear your thoughts on that first.",
            "There are different perspectives on that. What's your view?"
        ])
    else:
        response = random.choice([
            "That's quite interesting. Could you tell me more?",
            "I appreciate you sharing that. What else is on your mind?",
            "Thanks for sharing. How did that make you feel?",
            "That's a good point. Can you elaborate further?"
        ])
    
    return {
        'response': response,
        'correction': f"Suggested correction: '{correction}'" if correction else None
    }

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({
            'response': "I didn't receive your message. Could you please try again?",
            'correction': None
        })
    
    return jsonify(generate_response(user_message))

@app.route('/api/start', methods=['GET'])
def start_conversation():
    return jsonify({
        'response': random.choice(CONVERSATION_STARTERS),
        'correction': None
    })

if __name__ == '__main__':
    app.run(debug=True)
