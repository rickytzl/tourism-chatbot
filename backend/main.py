from fastapi import FastAPI, Request
from pydantic import BaseModel
import httpx
import os
from fastapi.middleware.cors import CORSMiddleware

from openai import OpenAI
import uvicorn
import openai
import dotenv

dotenv.load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Pydantic Model
class ChatRequest(BaseModel):
    user_id: str
    message: str

# In-memory History Storage
CHAT_HISTORY = {}

# Function to check if message is related to Indonesian tourism
def is_relevant(conversation_history, new_message):
    # Combine the last few messages (both user and assistant) into context
    recent_conversation = ""
    for turn in conversation_history[-3:]:  # Take the last 3 turns or adjust as needed
        recent_conversation += f"User: {turn['user']}\nBot: {turn['bot']}\n\n"
    
    
    # Define the prompt for relevance checking
    prompt = (
        "Context of conversation:\n"
        f"{recent_conversation}\n\n"
        "New message:\n"
        f"{new_message}\n\n"
        "Question: Is the conversation still about tourism in Indonesia? "
        "Answer with 'yes' or 'no' and explain briefly."
    )
    
    # Call OpenAI API to check relevance
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        temperature=0,
        max_tokens=50,
    )
    
    # Get response text
    answer = response.choices[0].message.content.strip().lower()
    
    # Check if the response contains "yes"
    return "yes" in answer


def is_top_10(message):
    prompt = f"Is the following question the same with what's top 10 tourism destinations in Indonesia? Answer with 'yes' or 'no': {message}"
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who only responds with 'yes' or 'no'."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1,
        n=1,
        stop=None,
        temperature=0.0
    )
    answer = response.choices[0].message.content.strip().lower()
    return answer == 'yes'

# Function to store chat history
def store_history(user_id, user_message, bot_response):
    if user_id not in CHAT_HISTORY:
        CHAT_HISTORY[user_id] = []
    CHAT_HISTORY[user_id].append({
        "user": user_message,
        "bot": bot_response
    })

# Function to retrieve chat history
def get_history(user_id):
    return CHAT_HISTORY.get(user_id, [])

# Function to call DeepSeek API
def call_deepseek_api(user_id, prompt):
    messages = get_history(user_id)
    # Prepare messages for context
    chat_context = [{
        "role": "system", 
        "content": "You are a concise assistant specialized in Indonesian tourism. Answer questions briefly and directly with relevant information about Indonesian travel, destinations, culture, or related tourism details. you can only chat with simple maximum of 4 sentence"
    }]

    for msg in messages[-5:]:  # Keep the last 5 messages
        chat_context.append({"role": "user", "content": msg['user']})
        chat_context.append({"role": "assistant", "content": msg['bot']})

    chat_context.append({"role": "user", "content": prompt})
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=chat_context,
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.7
    )

    return response.choices[0].message.content

# API Endpoint
@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    if not is_relevant(get_history(request.user_id), request.message):
        return {"response": "Maaf, saya hanya bisa menjawab tentang pariwisata di Indonesia."}
    
    if is_top_10(request.message):
        top_dest = '''1. Bali\n2. Jakarta\n3. Bromo\n4. Mandalika\n5. Lombok\n6. Borobudur\n 7. Danau Toba \n8. Labuan Bajo\n 9. Likupang \n10. Tanjung Kelayang '''
        return {"response": top_dest, "history": get_history(request.user_id)}
    
    bot_response = call_deepseek_api(request.user_id, request.message)
    store_history(request.user_id, request.message, bot_response)

    return {"response": bot_response, "history": get_history(request.user_id)}

# Health Check
@app.get("/")
def read_root():
    return {"message": "Tourism Chat API is running!"}

# Run the FastAPI server
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, workers=1)