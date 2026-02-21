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
<title>AI Study Assistant</title>

<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap" rel="stylesheet">

<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

body {
    height: 100vh;
    background: linear-gradient(145deg, #0f172a, #1e293b);
    display: flex;
    justify-content: center;
    align-items: center;
    color: #e2e8f0;
}

.chat-container {
    width: 95%;
    max-width: 850px;
    height: 92vh;
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(30px);
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,0.08);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: 0 25px 60px rgba(0,0,0,0.6);
}

.header {
    padding: 22px;
    text-align: center;
    font-size: 20px;
    font-weight: 600;
    letter-spacing: 0.5px;
    background: rgba(255,255,255,0.03);
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

.chat-box {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.message {
    max-width: 75%;
    padding: 14px 18px;
    border-radius: 16px;
    line-height: 1.6;
    font-size: 14px;
    word-wrap: break-word;
}

.user {
    align-self: flex-end;
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
}

.bot {
    align-self: flex-start;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
}

.input-area {
    display: flex;
    gap: 12px;
    padding: 18px;
    background: rgba(255,255,255,0.03);
    border-top: 1px solid rgba(255,255,255,0.08);
}

input {
    flex: 1;
    padding: 14px 16px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.05);
    color: white;
    font-size: 14px;
    outline: none;
    transition: 0.3s;
}

input::placeholder {
    color: rgba(255,255,255,0.5);
}

input:focus {
    border: 1px solid #3b82f6;
    box-shadow: 0 0 12px rgba(59,130,246,0.4);
}

button {
    padding: 14px 20px;
    border-radius: 12px;
    border: none;
    font-weight: 600;
    font-size: 14px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    cursor: pointer;
    transition: 0.3s ease;
}

button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(59,130,246,0.4);
}

.typing {
    font-size: 12px;
    opacity: 0.6;
}

/* Mobile Optimization */
@media (max-width: 600px) {
    .chat-container {
        height: 100vh;
        border-radius: 0;
    }

    .header {
        font-size: 18px;
        padding: 18px;
    }

    input {
        font-size: 13px;
    }

    button {
        padding: 12px 16px;
    }
}
</style>
</head>

<body>

<div class="chat-container">
    <div class="header">AI Study Assistant</div>
    <div class="chat-box" id="chatBox"></div>

    <div class="input-area">
        <input type="text" id="message" placeholder="Ask your academic question..." />
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
    typing.innerText = "Generating response...";
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