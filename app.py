from flask import Flask, request, jsonify
from flask_cors import CORS
from gingerit.gingerit import GingerIt
import re
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
parser = GingerIt()

# Sample conversation starters
CONVERSATION_STARTERS = [
    "Tell me about your hobbies.",
    "What did you do yesterday?",
    "Describe your favorite place to visit.",
    "What's your opinion about technology?",
    "If you could travel anywhere, where would you go?"
]

# Common mistakes and corrections
COMMON_MISTAKES = {
    r'\bhe go\b': 'he goes',
    r'\bshe like\b': 'she likes',
    r'\bthey is\b': 'they are',
    r'\bi has\b': 'I have',
    r'\byou was\b': 'you were'
}

def check_grammar(text):
    try:
        result = parser.parse(text)
        if result['corrections']:
            return result['corrections'][0]['text']
        return None
    except Exception as e:
        print(f"Grammar check error: {e}")
        return None

def check_common_mistakes(text):
    for mistake, correction in COMMON_MISTAKES.items():
        if re.search(mistake, text, re.IGNORECASE):
            return correction
    return None

def generate_response(user_message):
    # Check for grammar and common mistakes
    correction = check_grammar(user_message) or check_common_mistakes(user_message)
    
    # Simple response generation (in a real app, you'd use an LLM)
    responses = [
        "That's interesting! Tell me more about that.",
        "I see. How does that make you feel?",
        "Thanks for sharing that with me.",
        "That's a great point. Can you elaborate?",
        "I understand. What else would you like to talk about?"
    ]
    
    # If the message is very short, ask for more details
    if len(user_message.split()) < 3:
        response = "Could you please say more about that?"
    else:
        response = random.choice(responses)
    
    # If the user asks a question, answer it
    if user_message.endswith('?'):
        response = "That's a good question. I think it depends on the situation."
    
    return {
        'response': response,
        'correction': f"You meant: '{correction}'" if correction else None
    }

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({
            'response': "I didn't receive your message. Please try again.",
            'correction': None
        })
    
    response_data = generate_response(user_message)
    return jsonify(response_data)

@app.route('/api/start', methods=['GET'])
def start_conversation():
    return jsonify({
        'response': random.choice(CONVERSATION_STARTERS),
        'correction': None
    })

if __name__ == '__main__':
    app.run(debug=True)
