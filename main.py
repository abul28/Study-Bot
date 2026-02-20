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
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f6f9;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .chat-container {
                background: white;
                width: 400px;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }
            h2 {
                text-align: center;
            }
            input {
                width: 100%;
                padding: 10px;
                margin-top: 10px;
                border-radius: 5px;
                border: 1px solid #ccc;
            }
            button {
                width: 100%;
                padding: 10px;
                margin-top: 10px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:hover {
                background: #0056b3;
            }
            #response {
                margin-top: 15px;
                background: #f1f1f1;
                padding: 10px;
                border-radius: 5px;
                min-height: 50px;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <h2>📚 AI Study Bot</h2>
            <input type="text" id="message" placeholder="Ask a question..." />
            <button onclick="sendMessage()">Send</button>
            <div id="response"></div>
        </div>

        <script>
            async function sendMessage() {
                const message = document.getElementById("message").value;
                const responseBox = document.getElementById("response");
                responseBox.innerHTML = "Thinking...";

                const res = await fetch(`/chat?user_id=1&message=${encodeURIComponent(message)}`);
                const data = await res.json();

                responseBox.innerHTML = data.response;
            }
        </script>
    </body>
    </html>
    """