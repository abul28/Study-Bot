from fastapi import FastAPI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
import os

load_dotenv()
app = FastAPI()

# Setup LLM
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.1-8b-instant"
)

# Setup MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["studybot"]
collection = db["chats"]

@app.get("/chat")
def chat(user_id: str, message: str):

    previous_chats = list(collection.find({"user_id": user_id}))

    context = ""
    for chat in previous_chats:
        context += f"User: {chat['message']}\nBot: {chat['response']}\n"

    system_prompt = SystemMessage(
        content="You are a helpful AI Study Assistant. Answer only academic and study-related questions clearly."
    )

    final_prompt = context + f"User: {message}"

    response = llm.invoke([system_prompt, HumanMessage(content=final_prompt)])

    collection.insert_one({
        "user_id": user_id,
        "message": message,
        "response": response.content
    })

    return {"response": response.content}
@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Study Bot</title>

<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">

<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Inter', sans-serif;
}

body {
    height: 100vh;
    background: radial-gradient(circle at 20% 20%, #1e1e3f, #0f0f1f 60%);
    display: flex;
    justify-content: center;
    align-items: center;
    color: white;
    overflow: hidden;
}

.background-glow {
    position: absolute;
    width: 500px;
    height: 500px;
    background: #6366f1;
    filter: blur(200px);
    opacity: 0.3;
    border-radius: 50%;
    top: -100px;
    left: -100px;
}

.chat-container {
    position: relative;
    width: 95%;
    max-width: 850px;
    height: 90vh;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(40px);
    border-radius: 30px;
    border: 1px solid rgba(255,255,255,0.1);
    display: flex;
    flex-direction: column;
    box-shadow: 0 30px 80px rgba(0,0,0,0.6);
    overflow: hidden;
}

.header {
    padding: 25px;
    text-align: center;
    font-size: 24px;
    font-weight: 700;
    letter-spacing: 1px;
    background: rgba(255,255,255,0.04);
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.chat-box {
    flex: 1;
    padding: 30px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.message {
    max-width: 70%;
    padding: 15px 20px;
    border-radius: 18px;
    line-height: 1.6;
    font-size: 14px;
    animation: fadeIn 0.4s ease;
}

.user {
    align-self: flex-end;
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    box-shadow: 0 10px 30px rgba(99,102,241,0.4);
}

.bot {
    align-self: flex-start;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.1);
}

.input-area {
    display: flex;
    padding: 20px;
    gap: 15px;
    background: rgba(255,255,255,0.04);
    border-top: 1px solid rgba(255,255,255,0.1);
}

input {
    flex: 1;
    padding: 15px 18px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.08);
    color: white;
    font-size: 14px;
    outline: none;
    transition: 0.3s;
}

input::placeholder {
    color: rgba(255,255,255,0.5);
}

input:focus {
    border: 1px solid #6366f1;
    box-shadow: 0 0 20px rgba(99,102,241,0.6);
}

button {
    padding: 15px 25px;
    border-radius: 14px;
    border: none;
    font-weight: 600;
    font-size: 14px;
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    color: white;
    cursor: pointer;
    transition: 0.3s;
    box-shadow: 0 10px 30px rgba(99,102,241,0.4);
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 15px 40px rgba(99,102,241,0.6);
}

@keyframes fadeIn {
    from {opacity: 0; transform: translateY(10px);}
    to {opacity: 1; transform: translateY(0);}
}

.typing {
    font-size: 12px;
    opacity: 0.6;
    animation: pulse 1.2s infinite;
}

@keyframes pulse {
    0% {opacity: 0.3;}
    50% {opacity: 1;}
    100% {opacity: 0.3;}
}
</style>
</head>

<body>

<div class="background-glow"></div>

<div class="chat-container">
    <div class="header">🚀 AI Study Assistant</div>
    <div class="chat-box" id="chatBox"></div>

    <div class="input-area">
        <input type="text" id="message" placeholder="Ask anything academic..." />
        <button onclick="sendMessage()">Send</button>
    </div>
</div>

<script>
const chatBox = document.getElementById("chatBox");

function addMessage(text, type) {
    const msg = document.createElement("div");
    msg.className = "message " + type;
    msg.innerText = text;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById("message");
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, "user");
    input.value = "";

    const typing = document.createElement("div");
    typing.className = "typing";
    typing.innerText = "AI is thinking...";
    chatBox.appendChild(typing);
    chatBox.scrollTop = chatBox.scrollHeight;

    const res = await fetch(`/chat?user_id=1&message=${encodeURIComponent(message)}`);
    const data = await res.json();

    chatBox.removeChild(typing);
    addMessage(data.response, "bot");
}
</script>

</body>
</html>
"""