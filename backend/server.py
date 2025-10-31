from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class RephraseRequest(BaseModel):
    text: str
    tone: str = "conversational"  # formal, conversational, academic, creative

class RephraseResponse(BaseModel):
    rephrased_text: str
    original_text: str
    tone: str
    word_count: int
    char_count: int

class HistoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_text: str
    rephrased_text: str
    tone: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HistoryCreate(BaseModel):
    original_text: str
    rephrased_text: str
    tone: str

# Routes
@api_router.get("/")
async def root():
    return {"message": "TextHumanizer API"}

@api_router.post("/rephrase", response_model=RephraseResponse)
async def rephrase_text(request: RephraseRequest):
    try:
        # Get API key from environment
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        # Create tone-specific system message
        tone_prompts = {
            "formal": "You are an expert English writer. Rephrase the user's text into formal, professional, grammatically correct English that sounds natural and polished. Preserve the original meaning and context. Only return the rephrased text, nothing else.",
            "conversational": "You are an expert English writer. Rephrase the user's text into natural, conversational, grammatically correct English that sounds human and friendly. Preserve the original meaning and context. Only return the rephrased text, nothing else.",
            "academic": "You are an expert academic writer. Rephrase the user's text into scholarly, precise, grammatically correct English suitable for academic papers. Preserve the original meaning and context. Only return the rephrased text, nothing else.",
            "creative": "You are a creative writer. Rephrase the user's text into engaging, expressive, grammatically correct English with a creative flair. Preserve the original meaning and context. Only return the rephrased text, nothing else."
        }
        
        system_message = tone_prompts.get(request.tone, tone_prompts["conversational"])
        
        # Initialize LLM chat
        chat = LlmChat(
            api_key=api_key,
            session_id=str(uuid.uuid4()),
            system_message=system_message
        ).with_model("openai", "gpt-5")
        
        # Create user message
        user_message = UserMessage(text=request.text)
        
        # Get response from LLM
        response = await chat.send_message(user_message)
        
        # Calculate stats
        word_count = len(response.split())
        char_count = len(response)
        
        return RephraseResponse(
            rephrased_text=response,
            original_text=request.text,
            tone=request.tone,
            word_count=word_count,
            char_count=char_count
        )
    except Exception as e:
        logger.error(f"Error rephrasing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to rephrase text: {str(e)}")

@api_router.post("/history", response_model=HistoryItem)
async def save_history(input: HistoryCreate):
    try:
        history_obj = HistoryItem(**input.model_dump())
        doc = history_obj.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        _ = await db.history.insert_one(doc)
        return history_obj
    except Exception as e:
        logger.error(f"Error saving history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save history")

@api_router.get("/history", response_model=List[HistoryItem])
async def get_history():
    try:
        history_items = await db.history.find({}, {"_id": 0}).sort("timestamp", -1).to_list(50)
        for item in history_items:
            if isinstance(item['timestamp'], str):
                item['timestamp'] = datetime.fromisoformat(item['timestamp'])
        return history_items
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")

@api_router.delete("/history/{history_id}")
async def delete_history_item(history_id: str):
    try:
        result = await db.history.delete_one({"id": history_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="History item not found")
        return {"message": "History item deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete history")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()