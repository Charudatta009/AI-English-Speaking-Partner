from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import random
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Conversation memory
conversation_history = []

# Coaching knowledge base
COACHING_MODES = {
    'pronunciation': {
        'prompts': [
            "Repeat after me: 'She sells seashells by the seashore'",
            "Say this 3 times: 'The big black bug bit the big black bear'",
            "Try this tongue twister: 'Peter Piper picked a peck of pickled peppers'"
        ],
        'feedback': {
            'good': "Excellent pronunciation! Let's try something more challenging.",
            'average': "Good attempt! Try to focus on the {sounds} sounds.",
            'poor': "Let's slow down. Break it into syllables: {breakdown}"
        }
    },
    'fluency': {
        'prompts': [
            "Describe your favorite movie without stopping for 1 minute",
            "Tell me what you did yesterday in detail",
            "Explain your job/hobbies to me as if I know nothing about it"
        ],
        'feedback': {
            'good': "Great flow! You're speaking very naturally.",
            'average': "Good job! Try to use more connecting words like 'however' or 'therefore'.",
            'poor': "Don't worry about mistakes. Focus on keeping the conversation going."
        }
    },
    'grammar': {
        'prompts': [
            "Tell me about your future plans using correct tenses",
            "Describe your childhood using past tense",
            "Explain what you're doing right now in present continuous"
        ],
        'feedback': {
            'good': "Perfect grammar usage! You've mastered this tense.",
            'average': "Good effort! Remember the rule: {grammar_rule}",
            'poor': "Let's review: {correct_example}"
        }
    }
}

# Error patterns with corrections
ERROR_PATTERNS = {
    r'\b(i)\b': 'I',  # Capitalize I
    r'\b(he|she|it) (go|like|want)\b': r'\1 \2s',
    r'\bdon\'t has\b': "don't have",
    r'\byesterday i (go|eat|see)\b': r'yesterday I \1ed',
    r'\bmore better\b': 'better'
}

def analyze_speech(text):
    # Calculate speech metrics
    word_count = len(text.split())
    unique_words = len(set(text.lower().split()))
    lexical_diversity = unique_words / word_count if word_count > 0 else 0
    
    # Detect errors
    corrections = []
    for pattern, fix in ERROR_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            corrected = re.sub(pattern, fix, text, flags=re.IGNORECASE)
            if corrected != text:
                corrections.append(corrected)
    
    return {
        'word_count': word_count,
        'lexical_diversity': lexical_diversity,
        'corrections': corrections
    }

def generate_coaching_response(user_message):
    analysis = analyze_speech(user_message)
    conversation_history.append({
        'time': datetime.now().isoformat(),
        'user': user_message,
        'analysis': analysis
    })
    
    # Determine coaching mode based on conversation
    current_mode = None
    if len(conversation_history) > 1:
        last_ai = conversation_history[-2]['ai'] if 'ai' in conversation_history[-2] else None
        if last_ai and 'mode' in last_ai:
            current_mode = last_ai['mode']
    
    # Generate coaching response
    if current_mode and current_mode in COACHING_MODES:
        # Provide feedback on previous attempt
        if len(analysis['corrections']) > 3:
            feedback = COACHING_MODES[current_mode]['feedback']['poor']
            if current_mode == 'pronunciation':
                feedback = feedback.format(breakdown="...")  # Add actual breakdown
        elif len(analysis['corrections']) > 0:
            feedback = COACHING_MODES[current_mode]['feedback']['average']
            if current_mode == 'grammar':
                feedback = feedback.format(grammar_rule="Present simple: I work, he works")
        else:
            feedback = COACHING_MODES[current_mode]['feedback']['good']
        
        # Suggest next practice
        next_prompt = random.choice(COACHING_MODES[current_mode]['prompts'])
        
        return {
            'response': f"{feedback} Now let's try this: {next_prompt}",
            'correction': analysis['corrections'][0] if analysis['corrections'] else None,
            'mode': current_mode
        }
    else:
        # Start a new coaching session
        if "pronunciation" in user_message.lower():
            mode = 'pronunciation'
        elif "fluency" in user_message.lower() or "speak faster" in user_message.lower():
            mode = 'fluency'
        elif "grammar" in user_message.lower():
            mode = 'grammar'
        else:
            mode = random.choice(list(COACHING_MODES.keys()))
        
        prompt = random.choice(COACHING_MODES[mode]['prompts'])
        return {
            'response': f"Let's practice {mode}. {prompt}",
            'correction': None,
            'mode': mode
        }

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({
            'response': "I didn't hear anything. Could you please speak up?",
            'correction': None
        })
    
    response = generate_coaching_response(user_message)
    conversation_history[-1]['ai'] = response  # Store AI response in history
    
    return jsonify({
        'response': response['response'],
        'correction': response.get('correction')
    })

@app.route('/api/start', methods=['GET'])
def start_conversation():
    mode = random.choice(list(COACHING_MODES.keys()))
    prompt = random.choice(COACHING_MODES[mode]['prompts'])
    return jsonify({
        'response': f"Let's practice English! We'll focus on {mode}. {prompt}",
        'correction': None
    })

if __name__ == '__main__':
    app.run(debug=True)
