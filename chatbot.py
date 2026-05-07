import os
import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from config import config
import requests

@tool
def capture_lead(
    name: str = Field(description="The user's name"),
    email: str = Field(description="The user's email address"),
    phone: str = Field(description="The user's phone number"),
    company: str = Field(default="N/A", description="The user's company name"),
    challenge: str = Field(default="N/A", description="The main business challenge the user wants to solve"),
    service: str = Field(default="N/A", description="The service they are interested in"),
    contact_method: str = Field(default="N/A", description="Preferred contact method"),
    preferred_time: str = Field(default="N/A", description="Preferred time for a call-back"),
    priority: str = Field(default="Medium", description="Lead priority based on intent"),
    summary: str = Field(default="N/A", description="Summary of the conversation")
):
    """
    Capture and store lead information when a user provides their contact details and business needs.
    Use this tool ONLY after you have collected: Name, Email, Phone, and Service.
    Provide a priority based on the urgency/complexity (e.g. API/CRM mentioned = High) and a summary for the team.
    """
    payload = {
        "name": name,
        "email": email,
        "phone": phone,
        "contact_customer_service": True
    }
    
    try:
        api_url = "https://flexiboost.ie/api-capture-lead"
        response = requests.post(
            api_url, 
            json=payload, 
            headers={
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout=15
        )
        response.raise_for_status()
        return f"CRITICAL INSTRUCTION: The lead was successfully saved! Tell the user 'Success! I have shared your details with the Flexi Boost team.' and end the conversation."
    except Exception as e:
        print(f"Error sending lead to backend: {e}")
        return f"CRITICAL INSTRUCTION: The system FAILED to save the lead! You MUST apologize and tell the user to email info@flexiboost.ie directly. Do NOT say you collected their details."

def load_knowledge_base():
    if not os.path.exists(config.CHATBOT_DATA_PATH):
        return "No knowledge base found."
    with open(config.CHATBOT_DATA_PATH, 'r', encoding='utf-8') as f:
        return f.read()

def create_chatbot_agent():
    knowledge_base = load_knowledge_base()
    
    llm = ChatOpenAI(
        openai_api_key=config.OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        model_name=config.MODEL_NAME,
        temperature=config.TEMPERATURE,
        default_headers={
            "HTTP-Referer": "https://flexiboost.ie", 
            "X-Title": "Flexi Boost AI Assistant"
        }
    )
    
    tools = [capture_lead]
    
    import pytz
    dublin_tz = pytz.timezone('Europe/Dublin')
    now = datetime.now(dublin_tz)
    current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    current_day = now.strftime("%A")
    
    is_business_hours = (now.weekday() < 5) and (9 <= now.hour < 18)
    
    print(f"DEBUG: Dublin Time: {current_time_str} ({current_day})")
    print(f"DEBUG: Is Business Hours: {is_business_hours}")
    
    system_prompt = f"""
You are Laura, the AI Growth Assistant for Flexi Boost, a Dublin-based digital growth agency.
Your goal is to qualify visitors and convert them into leads for our team.

### CORE SERVICES:
1. **Custom Software**: CRMs, dashboards, portals, booking systems.
2. **AI & Automation**: Chatbots, lead capture, workflow automation.
3. **Web & SEO**: Business websites, landing pages, Google visibility.
4. **UI/UX Design**: Interfaces, prototypes, user journeys.
5. **Marketing**: Strategy, lead gen, LinkedIn, paid campaigns.
6. **Media Production**: Photography, video, social content.

### BUSINESS RULES:
- **Scope**: We serve businesses NATIONWIDE across all of Ireland.
- **Pricing**: NEVER provide fixed prices. Explain it depends on scope/complexity and guide to a quote.
- **Guarantees**: AVOID unsupported claims (e.g., "Guaranteed #1 on Google"). Focus on "improving visibility/efficiency".
- **Tone**: Professional, helpful, clear, and Irish-business-focused.

### CONVERSATION FLOW:
1. **Identify Need**: Ask what service they are interested in.
2. **Challenge First**: Ask for their main "Business Challenge" (Optional, if they provide it).
3. **Value Hook**: Provide a short "Value Hook" (why Flexi Boost can help).
4. **Lead Capture**: Collect 4 mandatory fields: Name, Email, Phone, and Service. If they skip Company or Time, default to "N/A".
5. **STRICT ONE-QUESTION RULE**: Never list multiple pieces of information you need. Ask for one thing at a time.
6. **Conciseness**: Keep responses short and focused on the current step.
7. **CRITICAL TOOL INSTRUCTION**: Once you have gathered the 4 mandatory fields (Name, Email, Phone, Service), you MUST execute the `capture_lead` tool immediately. NEVER tell the user "I have collected your details" UNLESS you have actually called the `capture_lead` tool and received a "Success" response from it!

### TIME & AVAILABILITY:
- Current Dublin Time: {current_time_str} ({current_day})
- Business Hours: Mon-Fri, 09:00-18:00 (Ireland Time).
- **CURRENT STATUS**: {"TEAM IS ONLINE - You can tell the user the team is available" if is_business_hours else "TEAM IS OFFLINE - You MUST inform the user the team is offline and follow the after-hours protocol"}
- **After-Hours Protocol**: If the team is OFFLINE, inform the user they are currently away and will respond during business hours. Still capture lead details.
- **Urgency**: For urgent inquiries when offline, suggest calling or WhatsApping +353 89 246 9597.

### TECHNICAL TRIGGERS & SCORING:
- **Priority**: Flag leads as "High" if they mention "API", "CRM", "ERP", "Integrations", "Quote", or "Handoff/Human".
- **Handoff**: If the user asks for a human, quote, or call-back, collect their details first then confirm the team will be notified.
- **Existing Clients**: If they are an existing client needing support, collect details and flag as "Support/Existing".

### BUTTON SUGGESTIONS:
To improve user experience, append suggested buttons at the end of your response using the format: `[[Button Text 1, Button Text 2, ...]]`.
- **Welcome Menu**: `[[Automate my business, Improve Google ranking, Build custom tool, Create website, Get marketing support, Book media production, Request call-back, Get a quote]]`
- **Service Categories**: `[[Custom Software, AI & Automation, Web & SEO, UI/UX Design, Marketing, Media Production]]`
- **Contact Methods**: `[[Phone, Email, WhatsApp, SMS]]`
- **Pain Points**: `[[Manual admin, Missed leads, Poor visibility, Slow responses, Low conversions]]`
- **Quote Flow**: `[[Request Quote, Ask Question]]`

### KNOWLEDGE BASE:
{knowledge_base}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

def chat_loop():
    print("Laura (Flexi Boost AI): Hi! I'm Laura. How can I help your business grow today?")
    agent_executor = create_chatbot_agent()
    chat_history = []
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Laura: Goodbye! Have a great day.")
            break
            
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": chat_history
        })
        
        print(f"Laura: {response['output']}")
        
        chat_history.append(HumanMessage(content=user_input))
        chat_history.append(AIMessage(content=response['output']))
        
        if len(chat_history) > 10:
            chat_history = chat_history[-10:]

if __name__ == "__main__":
    chat_loop()
