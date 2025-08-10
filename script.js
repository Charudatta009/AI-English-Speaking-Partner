document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const micBtn = document.getElementById('mic-btn');
    
    // Check browser support for speech synthesis
    const synth = window.speechSynthesis;
    let voices = [];
    let recognition;
    
    function populateVoices() {
        voices = synth.getVoices();
        // You can filter voices here if needed
    }
    
    populateVoices();
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = populateVoices;
    }
    
    // Speech recognition setup
    try {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            sendMessage();
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            micBtn.classList.remove('listening');
            addBotMessage("Sorry, I couldn't understand your speech. Please try again or type your message.");
        };
        
        micBtn.addEventListener('click', toggleSpeechRecognition);
    } catch (e) {
        console.error('Speech recognition not supported', e);
        micBtn.style.display = 'none';
    }
    
    function speak(text) {
        if (synth.speaking) {
            synth.cancel();
        }
        
        if (text) {
            const utterance = new SpeechSynthesisUtterance(text);
            
            // Set voice preferences
            const preferredVoice = voices.find(voice => 
                voice.name.includes('English') && 
                voice.lang.includes('en-')
            );
            
            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }
            
            utterance.rate = 0.9; // Slightly slower than normal
            utterance.pitch = 1; // Normal pitch
            utterance.volume = 1; // Full volume
            
            synth.speak(utterance);
        }
    }
    
    function toggleSpeechRecognition() {
        if (micBtn.classList.contains('listening')) {
            recognition.stop();
            micBtn.classList.remove('listening');
            userInput.placeholder = "Type your message here...";
        } else {
            recognition.start();
            micBtn.classList.add('listening');
            userInput.placeholder = "Listening...";
        }
    }
    
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        addUserMessage(message);
        userInput.value = '';
        showTypingIndicator();
        
        // Send to backend
       const API_BASE_URL = "https://ai-english-speaking-partner.onrender.com";
        fetch('`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            hideTypingIndicator();
            addBotMessage(data.response);
            speak(data.response); // Speak the response
            
            if (data.correction) {
                addCorrection(data.correction);
                // Optionally speak the correction too
                // speak("Correction: " + data.correction);
            }
        })
        .catch(error => {
            hideTypingIndicator();
            const errorMsg = "Sorry, I'm having trouble responding. Please try again.";
            addBotMessage(errorMsg);
            speak(errorMsg);
            console.error('Error:', error);
        });
    }
    
    function addUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    function addBotMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    function addCorrection(text) {
        const correctionDiv = document.createElement('div');
        correctionDiv.className = 'correction';
        correctionDiv.textContent = `Correction: ${text}`;
        chatMessages.appendChild(correctionDiv);
        scrollToBottom();
    }
    
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }
    
    function hideTypingIndicator() {
        const typingDiv = document.getElementById('typing-indicator');
        if (typingDiv) {
            typingDiv.remove();
        }
    }
    
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Start conversation with a random question
    fetch('/api/start')
        .then(response => response.json())
        .then(data => {
            addBotMessage(data.response);
            speak(data.response); // Speak the initial message
        });

});
