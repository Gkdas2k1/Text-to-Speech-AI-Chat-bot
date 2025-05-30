from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM 
from flask_cors import CORS

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, async_mode='eventlet')

# Load FLAN-T5
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large")
tokenizer.pad_token = tokenizer.eos_token

def generate_response(prompt):
    
    try:
        print(f"📥 Prompt: {prompt}")
        inputs = tokenizer(prompt, return_tensors='pt', padding=True, truncation=True)
        output = model.generate(
            **inputs,
            max_length=512,                # 🔼 increased token limit
            #temperature=0.8,                # 🔄 slightly more expressive
            #top_p=0.95,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
            do_sample = False
        )
        response = tokenizer.decode(output[0], skip_special_tokens=True)
        print(f"📤 Response: {response}")
        return response
    except Exception as e:
        print(f"❗ Generation error: {e}")
        return "I'm sorry, I couldn't process that."

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f"✅ Client connected: {request.sid}")
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"❌ Client disconnected: {request.sid}")

@socketio.on('topic')
def handle_topic(data):
    try:
        topic = data.get('text', '').strip()
        if not topic:
            raise ValueError("Empty topic text")

        print(f"📝 Topic received: {topic}")

        summary = generate_response(f"Write a comprehensive explanation about: {topic}. Cover origin, usage, examples, and impacts. At least 100 words.")
        question = generate_response(f"Suggest a good first question to start a conversation about: {topic}")

        emit('bot_response', {'text': summary, 'type': 'system'})
        emit('bot_response', {'text': question, 'type': 'system'})

    except Exception as e:
        emit('error', {'message': f"Topic handling failed: {str(e)}"})

@socketio.on('voice_answer')
def handle_voice_answer(data):
    try:
        text = data.get('audio', '').strip()
        if not text:
            raise ValueError("No text from client")

        print(f"🗣 User said: {text}")

        # Better prompt
        if text.endswith('?'):
            prompt = f"Write a long, in-depth answer to the question: {text}. Include background, examples, and implications."
        else:
            prompt = f"Write a comprehensive explanation about: {text}. Cover origin, usage, examples, and impacts. At least 300 words."

        ai_response = generate_response(prompt)

        emit('bot_response', {'text': ai_response, 'type': 'text'})

    except Exception as e:
        emit('error', {'message': f"Voice processing failed: {str(e)}"})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)