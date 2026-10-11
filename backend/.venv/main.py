
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Spectrum Support AI",
    description="AI-powered internet service support system",
    version="0.1.0"
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return {
        "message": "Welcome to Spectrum Support AI",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    return {
        "user_message": request.message,
        "response": f"You said: {request.message}"
    }
