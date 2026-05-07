from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from chatbot import create_chatbot_agent
from langchain_core.messages import HumanMessage, AIMessage
import uuid

import os
import json

app = Flask(__name__)
CORS(app)

import tempfile

if os.environ.get('VERCEL_ENV') or os.environ.get('VERCEL'):
    SESSION_FILE = '/tmp/chat_sessions.json'
else:
    SESSION_FILE = 'chat_sessions.json'

def load_sessions():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_sessions(data):
    with open(SESSION_FILE, 'w') as f:
        json.dump(data, f)

# Create a single agent instance to reuse
global_agent = create_chatbot_agent()

@app.after_request
def add_header(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Content-Security-Policy'] = "frame-ancestors *"
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message')
    session_id = data.get('session_id')
    frontend_history = data.get('history')
    
    if not session_id:
        session_id = str(uuid.uuid4())
        
    chat_history = []
    
    if frontend_history is not None:
        # Use stateless history provided by frontend
        for msg in frontend_history:
            if msg['type'] == 'human':
                chat_history.append(HumanMessage(content=msg['content']))
            elif msg['type'] == 'ai':
                chat_history.append(AIMessage(content=msg['content']))
        
        # We don't need to load from local file if frontend provided it
        sessions_data = {session_id: frontend_history}
    else:
        # Fallback to local storage (ephemeral on Vercel)
        sessions_data = load_sessions()
        
        if session_id not in sessions_data:
            sessions_data[session_id] = []
            
        for msg in sessions_data[session_id]:
            if msg['type'] == 'human':
                chat_history.append(HumanMessage(content=msg['content']))
            elif msg['type'] == 'ai':
                chat_history.append(AIMessage(content=msg['content']))
            
    try:
        response = global_agent.invoke({
            "input": user_input,
            "chat_history": chat_history
        })
        
        output = response['output']
        buttons = []
        
        import re
        button_match = re.search(r'\[\[(.*?)\]\]', output)
        if button_match:
            button_str = button_match.group(1)
            buttons = [b.strip() for b in button_str.split(',')]
            output = re.sub(r'\[\[.*?\]\]', '', output).strip()
        
        # Save to history
        sessions_data[session_id].append({"type": "human", "content": user_input})
        sessions_data[session_id].append({"type": "ai", "content": output})
        
        if len(sessions_data[session_id]) > 20: # keep last 20 messages
            sessions_data[session_id] = sessions_data[session_id][-20:]
            
        save_sessions(sessions_data)
            
        return jsonify({
            "output": output,
            "buttons": buttons,
            "session_id": session_id,
            "history": sessions_data[session_id]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
