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
<title>AI Study Bot</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {
    margin: 0;
    font-family: 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #1e1e2f, #2a2a45);
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    color: white;
}

.chat-wrapper {
    width: 95%;
    max-width: 700px;
    height: 90vh;
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    overflow: hidden;
}

.header {
    padding: 20px;
    text-align: center;
    font-size: 22px;
    font-weight: 600;
    background: rgba(255,255,255,0.05);
}

.chat-box {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.message {
    max-width: 75%;
    padding: 12px 16px;
    border-radius: 15px;
    line-height: 1.5;
    animation: fadeIn 0.3s ease-in-out;
}

.user {
    align-self: flex-end;
    background: #4f46e5;
}

.bot {
    align-self: flex-start;
    background: rgba(255,255,255,0.1);
}

.input-area {
    display: flex;
    padding: 15px;
    background: rgba(255,255,255,0.05);
}

input {
    flex: 1;
    padding: 12px;
    border-radius: 10px;
    border: none;
    outline: none;
    font-size: 14px;
}

button {
    margin-left: 10px;
    padding: 12px 18px;
    border-radius: 10px;
    border: none;
    background: #6366f1;
    color: white;
    cursor: pointer;
    transition: 0.3s;
}

button:hover {
    background: #4f46e5;
}

@keyframes fadeIn {
    from {opacity: 0; transform: translateY(5px);}
    to {opacity: 1; transform: translateY(0);}
}

.typing {
    font-size: 12px;
    opacity: 0.6;
}
</style>
</head>
<body>

<div class="chat-wrapper">
    <div class="header">📚 AI Study Bot</div>
    <div class="chat-box" id="chatBox"></div>

    <div class="input-area">
        <input type="text" id="message" placeholder="Ask your study question..." />
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