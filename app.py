from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from chatbot import create_chatbot_agent
from langchain_core.messages import HumanMessage, AIMessage
import uuid

import os
import json
import requests

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

global_agent = None

def get_agent():
    global global_agent
    if global_agent is None:
        global_agent = create_chatbot_agent()
    return global_agent

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
        agent = get_agent()
        response = agent.invoke({
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

VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN', 'flexiboost_whatsapp_secret')
WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')

def send_whatsapp_message(to, text):
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print("Missing WhatsApp credentials")
        return
        
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if mode and token:
            if mode == 'subscribe' and token == VERIFY_TOKEN:
                return challenge, 200
            else:
                return 'Forbidden', 403
        return 'Bad Request', 400

    elif request.method == 'POST':
        body = request.json
        if body and body.get('object'):
            if body.get('entry') and body['entry'][0].get('changes') and body['entry'][0]['changes'][0].get('value').get('messages'):
                message_info = body['entry'][0]['changes'][0]['value']['messages'][0]
                
                # Check if it's a valid text message
                if 'text' not in message_info:
                    return 'OK', 200
                    
                phone_number = message_info['from']
                message_body = message_info['text']['body']
                
                # Use phone_number as session_id for WhatsApp users
                session_id = f"wa_{phone_number}"
                
                sessions_data = load_sessions()
                if session_id not in sessions_data:
                    sessions_data[session_id] = []
                    
                chat_history = []
                for msg in sessions_data[session_id]:
                    if msg['type'] == 'human':
                        chat_history.append(HumanMessage(content=msg['content']))
                    elif msg['type'] == 'ai':
                        chat_history.append(AIMessage(content=msg['content']))
                        
                try:
                    agent = get_agent()
                    response = agent.invoke({
                        "input": message_body,
                        "chat_history": chat_history
                    })
                    
                    output = response['output']
                    import re
                    # Remove buttons from output for WhatsApp since it's text-based
                    output = re.sub(r'\[\[.*?\]\]', '', output).strip()
                    
                    # Save to history
                    sessions_data[session_id].append({"type": "human", "content": message_body})
                    sessions_data[session_id].append({"type": "ai", "content": output})
                    
                    if len(sessions_data[session_id]) > 20:
                        sessions_data[session_id] = sessions_data[session_id][-20:]
                        
                    save_sessions(sessions_data)
                    
                    # Send response back to WhatsApp
                    send_whatsapp_message(phone_number, output)
                    
                except Exception as e:
                    print(f"Error generating response: {e}")
            return 'OK', 200
        return 'Not Found', 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
