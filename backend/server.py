from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from emergentintegrations.llm.chat import LlmChat, UserMessage
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'sales-brain-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# LLM Config
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

app = FastAPI(title="Sales Brain API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== MODELS ==============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "admin"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    role: str
    created_at: str

class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: str
    company_id: Optional[str] = None
    customer_type: str = "individual"
    addresses: List[Dict[str, Any]] = []
    preferences: Dict[str, Any] = {}
    tags: List[str] = []
    notes: str = ""

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_id: Optional[str] = None
    customer_type: Optional[str] = None
    addresses: Optional[List[Dict[str, Any]]] = None
    preferences: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class CustomerResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: Optional[str] = None
    phone: str
    company_id: Optional[str] = None
    customer_type: str
    addresses: List[Dict[str, Any]] = []
    preferences: Dict[str, Any] = {}
    purchase_history: List[Dict[str, Any]] = []
    devices: List[Dict[str, Any]] = []
    tags: List[str] = []
    notes: str = ""
    total_spent: float = 0.0
    last_interaction: Optional[str] = None
    created_at: str

class TopicCreate(BaseModel):
    customer_id: str
    topic_type: str
    title: str
    device_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}

class TopicResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    customer_id: str
    topic_type: str
    title: str
    status: str
    device_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}
    created_at: str
    updated_at: str

class MessageCreate(BaseModel):
    conversation_id: str
    topic_id: Optional[str] = None
    content: str
    sender_type: str = "customer"
    message_type: str = "text"
    attachments: List[Dict[str, Any]] = []

class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    conversation_id: str
    topic_id: Optional[str] = None
    content: str
    sender_type: str
    message_type: str
    attachments: List[Dict[str, Any]] = []
    created_at: str

class ConversationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    customer_id: str
    customer_name: str
    customer_phone: str
    channel: str
    status: str
    last_message: Optional[str] = None
    last_message_at: Optional[str] = None
    unread_count: int = 0
    topics: List[TopicResponse] = []
    created_at: str

class ProductCreate(BaseModel):
    name: str
    description: str
    category: str
    sku: str
    base_price: float
    tax_rate: float = 18.0
    stock: int = 0
    images: List[str] = []
    specifications: Dict[str, Any] = {}
    is_active: bool = True

class ProductResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    category: str
    sku: str
    base_price: float
    tax_rate: float
    final_price: float
    stock: int
    images: List[str] = []
    specifications: Dict[str, Any] = {}
    is_active: bool
    created_at: str

class OrderCreate(BaseModel):
    customer_id: str
    conversation_id: Optional[str] = None
    items: List[Dict[str, Any]]
    shipping_address: Dict[str, Any]
    notes: str = ""

class OrderResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    customer_id: str
    customer_name: str
    conversation_id: Optional[str] = None
    items: List[Dict[str, Any]]
    subtotal: float
    tax: float
    total: float
    shipping_address: Dict[str, Any]
    status: str
    payment_status: str
    ticket_id: Optional[str] = None
    notes: str
    created_at: str

class TicketResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    ticket_number: str
    customer_id: str
    customer_name: str
    order_id: Optional[str] = None
    subject: str
    description: str
    priority: str
    status: str
    category: str
    created_at: str

class WhatsAppStatusResponse(BaseModel):
    connected: bool
    phone_number: Optional[str] = None
    qr_code: Optional[str] = None
    status: str

class AIMessageRequest(BaseModel):
    customer_id: str
    conversation_id: str
    message: str

class DashboardStats(BaseModel):
    total_customers: int
    active_conversations: int
    open_topics: int
    pending_orders: int
    total_revenue: float
    recent_conversations: List[Dict[str, Any]]
    top_customers: List[Dict[str, Any]]

# Knowledge Base Models
class KBArticleCreate(BaseModel):
    title: str
    category: str  # faq, policy, procedure, product_info
    content: str
    tags: List[str] = []
    is_active: bool = True

class KBArticleResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    category: str
    content: str
    tags: List[str] = []
    is_active: bool
    created_at: str
    updated_at: str

# Escalation Model
class EscalationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    customer_id: str
    customer_name: str
    conversation_id: str
    reason: str
    message_content: str
    status: str  # pending, reviewed, resolved
    priority: str
    created_at: str

# Conversation Summary Model
class ConversationSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    conversation_id: str
    customer_id: str
    customer_name: str
    date_range: Dict[str, str]
    channel: str
    topics_discussed: List[Dict[str, Any]]
    customer_requests: List[str]
    products_discussed: List[str]
    actions_taken: List[str]
    tickets_created: List[str]
    orders_placed: List[str]
    escalations: List[str]
    pending_followups: List[str]
    summary_text: str
    created_at: str

# ============== AUTH HELPERS ==============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== KNOWLEDGE BASE HELPERS ==============

async def get_kb_context():
    """Fetch all active KB articles for AI context"""
    articles = await db.knowledge_base.find({"is_active": True}, {"_id": 0}).to_list(100)
    kb_text = ""
    for article in articles:
        kb_text += f"\n[{article['category'].upper()}] {article['title']}:\n{article['content']}\n"
    return kb_text

async def search_kb(query: str):
    """Search KB for relevant articles"""
    articles = await db.knowledge_base.find({
        "is_active": True,
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"content": {"$regex": query, "$options": "i"}},
            {"tags": {"$in": [query.lower()]}}
        ]
    }, {"_id": 0}).to_list(10)
    return articles

# ============== CONVERSATION SUMMARY HELPERS ==============

async def generate_conversation_summary(conversation_id: str):
    """Generate a structured summary for a conversation"""
    conv = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    if not conv:
        return None
    
    messages = await db.messages.find({"conversation_id": conversation_id}, {"_id": 0}).sort("created_at", 1).to_list(1000)
    topics = await db.topics.find({"conversation_id": conversation_id}, {"_id": 0}).to_list(100)
    
    if not messages:
        return None
    
    # Extract key information
    customer_requests = []
    products_discussed = []
    actions_taken = []
    
    for msg in messages:
        if msg["sender_type"] == "customer":
            customer_requests.append(msg["content"][:100])
        elif msg["sender_type"] == "ai":
            actions_taken.append(f"AI responded: {msg['content'][:50]}...")
    
    # Get related tickets and orders
    tickets = await db.tickets.find({"customer_id": conv["customer_id"]}, {"_id": 0, "ticket_number": 1}).to_list(10)
    orders = await db.orders.find({"conversation_id": conversation_id}, {"_id": 0, "id": 1}).to_list(10)
    escalations = await db.escalations.find({"conversation_id": conversation_id}, {"_id": 0, "reason": 1}).to_list(10)
    
    # Build summary
    first_msg_time = messages[0]["created_at"] if messages else None
    last_msg_time = messages[-1]["created_at"] if messages else None
    
    summary_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    summary = {
        "id": summary_id,
        "conversation_id": conversation_id,
        "customer_id": conv["customer_id"],
        "customer_name": conv["customer_name"],
        "date_range": {"start": first_msg_time, "end": last_msg_time},
        "channel": conv.get("channel", "whatsapp"),
        "topics_discussed": [{"title": t["title"], "type": t["topic_type"], "status": t["status"]} for t in topics],
        "customer_requests": customer_requests[:5],
        "products_discussed": products_discussed,
        "actions_taken": actions_taken[:5],
        "tickets_created": [t["ticket_number"] for t in tickets],
        "orders_placed": [o["id"][:8] for o in orders],
        "escalations": [e["reason"] for e in escalations],
        "pending_followups": [t["title"] for t in topics if t["status"] in ["open", "in_progress"]],
        "summary_text": f"Conversation with {conv['customer_name']} covering {len(topics)} topics with {len(messages)} messages.",
        "created_at": now
    }
    
    # Store summary
    await db.conversation_summaries.update_one(
        {"conversation_id": conversation_id},
        {"$set": summary},
        upsert=True
    )
    
    return summary

# ============== ESCALATION HELPERS ==============

async def create_escalation(customer_id: str, conversation_id: str, reason: str, message_content: str, priority: str = "medium"):
    """Create an escalation for human review"""
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    
    escalation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    escalation = {
        "id": escalation_id,
        "customer_id": customer_id,
        "customer_name": customer["name"] if customer else "Unknown",
        "conversation_id": conversation_id,
        "reason": reason,
        "message_content": message_content,
        "status": "pending",
        "priority": priority,
        "created_at": now
    }
    
    await db.escalations.insert_one(escalation)
    
    # Log for notification (ready for WhatsApp integration)
    logger.info(f"ESCALATION: {reason} - Customer: {customer['name'] if customer else 'Unknown'} - Priority: {priority}")
    
    return escalation

# ============== HEALTH CHECK ==============

@api_router.get("/")
async def root():
    return {"message": "Sales Brain API is running", "status": "healthy"}

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user.email,
        "password": hash_password(user.password),
        "name": user.name,
        "role": user.role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    token = create_token(user_id, user.email)
    return {"token": token, "user": {"id": user_id, "email": user.email, "name": user.name, "role": user.role}}

@api_router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        created_at=user["created_at"]
    )

# ============== KNOWLEDGE BASE ROUTES ==============

@api_router.get("/kb", response_model=List[KBArticleResponse])
async def get_kb_articles(category: Optional[str] = None, search: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"is_active": True}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]
    
    articles = await db.knowledge_base.find(query, {"_id": 0}).to_list(100)
    return [KBArticleResponse(**a) for a in articles]

@api_router.post("/kb", response_model=KBArticleResponse)
async def create_kb_article(article: KBArticleCreate, user: dict = Depends(get_current_user)):
    article_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    article_doc = {
        "id": article_id,
        **article.model_dump(),
        "created_at": now,
        "updated_at": now
    }
    await db.knowledge_base.insert_one(article_doc)
    return KBArticleResponse(**article_doc)

@api_router.put("/kb/{article_id}", response_model=KBArticleResponse)
async def update_kb_article(article_id: str, article: KBArticleCreate, user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    result = await db.knowledge_base.update_one(
        {"id": article_id},
        {"$set": {**article.model_dump(), "updated_at": now}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    updated = await db.knowledge_base.find_one({"id": article_id}, {"_id": 0})
    return KBArticleResponse(**updated)

@api_router.delete("/kb/{article_id}")
async def delete_kb_article(article_id: str, user: dict = Depends(get_current_user)):
    result = await db.knowledge_base.delete_one({"id": article_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Article deleted"}

# ============== ESCALATIONS ROUTES ==============

@api_router.get("/escalations", response_model=List[EscalationResponse])
async def get_escalations(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    escalations = await db.escalations.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [EscalationResponse(**e) for e in escalations]

@api_router.put("/escalations/{escalation_id}/status")
async def update_escalation_status(escalation_id: str, status: str, user: dict = Depends(get_current_user)):
    if status not in ["pending", "reviewed", "resolved"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    result = await db.escalations.update_one({"id": escalation_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return {"message": "Status updated"}

# ============== CONVERSATION SUMMARIES ROUTES ==============

@api_router.get("/summaries", response_model=List[ConversationSummaryResponse])
async def get_summaries(customer_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    summaries = await db.conversation_summaries.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [ConversationSummaryResponse(**s) for s in summaries]

@api_router.post("/summaries/generate/{conversation_id}")
async def generate_summary(conversation_id: str, user: dict = Depends(get_current_user)):
    summary = await generate_conversation_summary(conversation_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return summary

# ============== CUSTOMERS ROUTES ==============

@api_router.get("/customers", response_model=List[CustomerResponse])
async def get_customers(search: Optional[str] = None, customer_type: Optional[str] = None, limit: int = 50, skip: int = 0, user: dict = Depends(get_current_user)):
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    if customer_type:
        query["customer_type"] = customer_type
    
    customers = await db.customers.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return [CustomerResponse(**c) for c in customers]

@api_router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerResponse(**customer)

@api_router.post("/customers", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, user: dict = Depends(get_current_user)):
    existing = await db.customers.find_one({"phone": customer.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Customer with this phone already exists")
    
    customer_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    customer_doc = {
        "id": customer_id,
        **customer.model_dump(),
        "purchase_history": [],
        "devices": [],
        "total_spent": 0.0,
        "last_interaction": None,
        "created_at": now
    }
    await db.customers.insert_one(customer_doc)
    return CustomerResponse(**customer_doc)

@api_router.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: str, update: CustomerUpdate, user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.customers.update_one({"id": customer_id}, {"$set": update_data})
    
    updated = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    return CustomerResponse(**updated)

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, user: dict = Depends(get_current_user)):
    result = await db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted"}

# ============== CONVERSATIONS & TOPICS ==============

@api_router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(status: Optional[str] = None, limit: int = 50, skip: int = 0, user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    
    conversations = await db.conversations.find(query, {"_id": 0}).sort("last_message_at", -1).skip(skip).limit(limit).to_list(limit)
    
    result = []
    for conv in conversations:
        topics = await db.topics.find({"conversation_id": conv["id"]}, {"_id": 0}).to_list(100)
        conv["topics"] = [TopicResponse(**t) for t in topics]
        result.append(ConversationResponse(**conv))
    
    return result

@api_router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, user: dict = Depends(get_current_user)):
    conv = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    topics = await db.topics.find({"conversation_id": conversation_id}, {"_id": 0}).to_list(100)
    conv["topics"] = [TopicResponse(**t) for t in topics]
    return ConversationResponse(**conv)

@api_router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(conversation_id: str, limit: int = 100, user: dict = Depends(get_current_user)):
    messages = await db.messages.find({"conversation_id": conversation_id}, {"_id": 0}).sort("created_at", 1).limit(limit).to_list(limit)
    return [MessageResponse(**m) for m in messages]

@api_router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(conversation_id: str, message: MessageCreate, user: dict = Depends(get_current_user)):
    conv = await db.conversations.find_one({"id": conversation_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    msg_doc = {
        "id": msg_id,
        "conversation_id": conversation_id,
        "topic_id": message.topic_id,
        "content": message.content,
        "sender_type": message.sender_type,
        "message_type": message.message_type,
        "attachments": message.attachments,
        "created_at": now
    }
    await db.messages.insert_one(msg_doc)
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"last_message": message.content, "last_message_at": now}}
    )
    
    return MessageResponse(**msg_doc)

@api_router.post("/topics", response_model=TopicResponse)
async def create_topic(topic: TopicCreate, user: dict = Depends(get_current_user)):
    conv = await db.conversations.find_one({"customer_id": topic.customer_id})
    if not conv:
        customer = await db.customers.find_one({"id": topic.customer_id}, {"_id": 0})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conv = {
            "id": conv_id,
            "customer_id": topic.customer_id,
            "customer_name": customer["name"],
            "customer_phone": customer["phone"],
            "channel": "whatsapp",
            "status": "active",
            "last_message": None,
            "last_message_at": now,
            "unread_count": 0,
            "created_at": now
        }
        await db.conversations.insert_one(conv)
    
    topic_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    topic_doc = {
        "id": topic_id,
        "conversation_id": conv["id"],
        **topic.model_dump(),
        "status": "open",
        "created_at": now,
        "updated_at": now
    }
    await db.topics.insert_one(topic_doc)
    return TopicResponse(**topic_doc)

@api_router.put("/topics/{topic_id}/status")
async def update_topic_status(topic_id: str, status: str, user: dict = Depends(get_current_user)):
    if status not in ["open", "in_progress", "resolved", "escalated"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.topics.update_one(
        {"id": topic_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Topic not found")
    return {"message": "Status updated"}

# ============== ENHANCED AI CHAT ==============

@api_router.post("/ai/chat")
async def ai_chat(request: AIMessageRequest, user: dict = Depends(get_current_user)):
    """Process customer message with AI using enhanced guidelines"""
    try:
        # STEP 1: Load customer context (Context-First Rule)
        customer = await db.customers.find_one({"id": request.customer_id}, {"_id": 0})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # STEP 2: Load open topics
        topics = await db.topics.find(
            {"customer_id": request.customer_id, "status": {"$in": ["open", "in_progress"]}},
            {"_id": 0}
        ).to_list(10)
        
        # STEP 3: Load recent messages (check for unanswered questions)
        recent_messages = await db.messages.find(
            {"conversation_id": request.conversation_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(20).to_list(20)
        
        # Check for last AI question that may need answering
        last_ai_question = None
        for msg in recent_messages:
            if msg["sender_type"] == "ai" and "?" in msg["content"]:
                last_ai_question = msg["content"]
                break
        
        # STEP 4: Consult Knowledge Base
        kb_context = await get_kb_context()
        
        # STEP 5: Check for escalation triggers (Authority Boundary Rule)
        msg_lower = request.message.lower()
        escalation_triggers = ["discount", "urgent", "complaint", "manager", "refund", "free", "special price", "exception", "promise", "guarantee delivery"]
        needs_authority_escalation = any(trigger in msg_lower for trigger in escalation_triggers)
        
        if needs_authority_escalation:
            escalation_reason = "Customer request requires human authority (discount/delivery/exception)"
            await create_escalation(
                customer_id=request.customer_id,
                conversation_id=request.conversation_id,
                reason=escalation_reason,
                message_content=request.message,
                priority="high"
            )
        
        # STEP 6: Build enhanced AI context
        context = f"""You are a friendly sales assistant. KEEP REPLIES SHORT like WhatsApp messages (1-3 sentences max).

CUSTOMER INFO:
Name: {customer.get('name')} | Phone: {customer.get('phone')} | Spent: ₹{customer.get('total_spent', 0)}
Addresses: {json.dumps(customer.get('addresses', []))}
Devices: {json.dumps(customer.get('devices', []))}

OPEN TOPICS: {', '.join([t['title'] for t in topics]) if topics else 'None'}
LAST QUESTION ASKED: {last_ai_question or 'None'}

KNOWLEDGE BASE:
{kb_context if kb_context else "No KB loaded."}

STRICT RULES:
1. NEVER ask for info you already have
2. NEVER offer discounts or delivery promises - say "Let me check and get back"
3. If unsure, say "Let me verify this for you"
4. Be helpful, brief, human-like
5. No emojis, no robotic language

RECENT CHAT:
{chr(10).join([f"{'Customer' if m['sender_type'] == 'customer' else 'You'}: {m['content']}" for m in reversed(recent_messages[-5:])])}

Customer says: {request.message}

Reply briefly (1-3 sentences):"""

        # Initialize LLM
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"conv-{request.conversation_id}",
            system_message=context
        ).with_model("openai", "gpt-5.2")
        
        user_msg = UserMessage(text=request.message)
        response = await chat.send_message(user_msg)
        
        # Detect multiple topics
        detected_topics = []
        topic_keywords = {
            "product_inquiry": ["price", "cost", "buy", "purchase", "want", "need", "interested", "available"],
            "service_request": ["repair", "fix", "broken", "not working", "slow", "issue", "problem", "damage"],
            "support": ["help", "how to", "guide", "explain", "what is", "setup", "configure"],
            "order": ["order", "delivery", "ship", "track", "status"]
        }
        
        for topic_type, words in topic_keywords.items():
            if any(word in msg_lower for word in words):
                detected_topics.append(topic_type)
        
        # Check if KB couldn't answer (flag for research)
        kb_insufficient = "Let me check" in response or "connect you with" in response
        
        return {
            "response": response,
            "detected_topics": detected_topics,
            "needs_escalation": needs_authority_escalation,
            "kb_insufficient": kb_insufficient,
            "customer_context": {
                "name": customer.get("name"),
                "open_topics": len(topics),
                "total_spent": customer.get("total_spent", 0)
            }
        }
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}")
        # Escalate on error
        await create_escalation(
            customer_id=request.customer_id,
            conversation_id=request.conversation_id,
            reason=f"AI Error: {str(e)}",
            message_content=request.message,
            priority="high"
        )
        return {
            "response": "I apologize, but I'm having trouble processing your request. Let me connect you with our team right away.",
            "detected_topics": [],
            "needs_escalation": True,
            "error": str(e)
        }

# ============== PRODUCTS ==============

@api_router.get("/products", response_model=List[ProductResponse])
async def get_products(category: Optional[str] = None, search: Optional[str] = None, is_active: bool = True, limit: int = 50, skip: int = 0, user: dict = Depends(get_current_user)):
    query = {"is_active": is_active}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}}
        ]
    
    products = await db.products.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    result = []
    for p in products:
        p["final_price"] = p["base_price"] * (1 + p["tax_rate"] / 100)
        result.append(ProductResponse(**p))
    return result

@api_router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, user: dict = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product["final_price"] = product["base_price"] * (1 + product["tax_rate"] / 100)
    return ProductResponse(**product)

@api_router.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, user: dict = Depends(get_current_user)):
    product_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    product_doc = {"id": product_id, **product.model_dump(), "created_at": now}
    await db.products.insert_one(product_doc)
    product_doc["final_price"] = product_doc["base_price"] * (1 + product_doc["tax_rate"] / 100)
    return ProductResponse(**product_doc)

@api_router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, product: ProductCreate, user: dict = Depends(get_current_user)):
    existing = await db.products.find_one({"id": product_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.products.update_one({"id": product_id}, {"$set": product.model_dump()})
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    updated["final_price"] = updated["base_price"] * (1 + updated["tax_rate"] / 100)
    return ProductResponse(**updated)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, user: dict = Depends(get_current_user)):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}

# ============== ORDERS ==============

@api_router.get("/orders", response_model=List[OrderResponse])
async def get_orders(status: Optional[str] = None, customer_id: Optional[str] = None, limit: int = 50, skip: int = 0, user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    orders = await db.orders.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [OrderResponse(**o) for o in orders]

@api_router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, user: dict = Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(**order)

@api_router.post("/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate, user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one({"id": order.customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    subtotal = sum(item["price"] * item["quantity"] for item in order.items)
    tax = subtotal * 0.18
    total = subtotal + tax
    
    order_id = str(uuid.uuid4())
    ticket_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    ticket_doc = {
        "id": ticket_id,
        "ticket_number": f"TKT-{datetime.now().strftime('%Y%m%d')}-{ticket_id[:6].upper()}",
        "customer_id": order.customer_id,
        "customer_name": customer["name"],
        "order_id": order_id,
        "subject": f"New Order - {customer['name']}",
        "description": f"Order placed with {len(order.items)} items. Total: ₹{total:.2f}",
        "priority": "medium",
        "status": "open",
        "category": "order",
        "created_at": now
    }
    await db.tickets.insert_one(ticket_doc)
    
    order_doc = {
        "id": order_id,
        "customer_id": order.customer_id,
        "customer_name": customer["name"],
        "conversation_id": order.conversation_id,
        "items": order.items,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "shipping_address": order.shipping_address,
        "status": "pending",
        "payment_status": "pending",
        "ticket_id": ticket_id,
        "notes": order.notes,
        "created_at": now
    }
    await db.orders.insert_one(order_doc)
    
    await db.customers.update_one(
        {"id": order.customer_id},
        {"$push": {"purchase_history": {"order_id": order_id, "total": total, "date": now}}, "$inc": {"total_spent": total}}
    )
    
    return OrderResponse(**order_doc)

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, user: dict = Depends(get_current_user)):
    valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    result = await db.orders.update_one({"id": order_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Status updated"}

# ============== TICKETS ==============

@api_router.get("/tickets", response_model=List[TicketResponse])
async def get_tickets(status: Optional[str] = None, limit: int = 50, skip: int = 0, user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    tickets = await db.tickets.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return [TicketResponse(**t) for t in tickets]

@api_router.put("/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, status: str, user: dict = Depends(get_current_user)):
    valid_statuses = ["open", "in_progress", "resolved", "closed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    result = await db.tickets.update_one({"id": ticket_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Status updated"}

# ============== WHATSAPP ==============

whatsapp_state = {"connected": False, "phone_number": None, "qr_code": None, "status": "disconnected"}

@api_router.get("/whatsapp/status", response_model=WhatsAppStatusResponse)
async def get_whatsapp_status(user: dict = Depends(get_current_user)):
    if not whatsapp_state["connected"]:
        whatsapp_state["qr_code"] = f"whatsapp://qr/{uuid.uuid4()}"
        whatsapp_state["status"] = "waiting_for_scan"
    return WhatsAppStatusResponse(**whatsapp_state)

@api_router.post("/whatsapp/connect")
async def connect_whatsapp(user: dict = Depends(get_current_user)):
    whatsapp_state["connected"] = True
    whatsapp_state["phone_number"] = "+91 98765 43210"
    whatsapp_state["status"] = "connected"
    whatsapp_state["qr_code"] = None
    return {"message": "WhatsApp connected successfully", "status": whatsapp_state}

@api_router.post("/whatsapp/disconnect")
async def disconnect_whatsapp(user: dict = Depends(get_current_user)):
    whatsapp_state["connected"] = False
    whatsapp_state["phone_number"] = None
    whatsapp_state["status"] = "disconnected"
    return {"message": "WhatsApp disconnected"}

@api_router.post("/whatsapp/simulate-message")
async def simulate_whatsapp_message(phone: str, message: str, user: dict = Depends(get_current_user)):
    if not whatsapp_state["connected"]:
        raise HTTPException(status_code=400, detail="WhatsApp not connected")
    
    customer = await db.customers.find_one({"phone": phone}, {"_id": 0})
    if not customer:
        customer_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        customer = {
            "id": customer_id, "name": f"WhatsApp User ({phone})", "phone": phone,
            "customer_type": "individual", "addresses": [], "preferences": {},
            "purchase_history": [], "devices": [], "tags": ["whatsapp"], "notes": "",
            "total_spent": 0.0, "last_interaction": now, "created_at": now
        }
        await db.customers.insert_one(customer)
    
    conv = await db.conversations.find_one({"customer_id": customer["id"]})
    if not conv:
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conv = {
            "id": conv_id, "customer_id": customer["id"], "customer_name": customer["name"],
            "customer_phone": phone, "channel": "whatsapp", "status": "active",
            "last_message": message, "last_message_at": now, "unread_count": 1, "created_at": now
        }
        await db.conversations.insert_one(conv)
    else:
        await db.conversations.update_one(
            {"id": conv["id"]},
            {"$set": {"last_message": message, "last_message_at": datetime.now(timezone.utc).isoformat()}, "$inc": {"unread_count": 1}}
        )
    
    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    msg_doc = {"id": msg_id, "conversation_id": conv["id"], "content": message, "sender_type": "customer", "message_type": "text", "attachments": [], "created_at": now}
    await db.messages.insert_one(msg_doc)
    
    return {"message": "Message received", "customer_id": customer["id"], "conversation_id": conv["id"], "message_id": msg_id}

# ============== DASHBOARD ==============

@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    total_customers = await db.customers.count_documents({})
    active_conversations = await db.conversations.count_documents({"status": "active"})
    open_topics = await db.topics.count_documents({"status": {"$in": ["open", "in_progress"]}})
    pending_orders = await db.orders.count_documents({"status": "pending"})
    pending_escalations = await db.escalations.count_documents({"status": "pending"})
    
    orders = await db.orders.find({"payment_status": "paid"}, {"_id": 0, "total": 1}).to_list(1000)
    total_revenue = sum(o.get("total", 0) for o in orders)
    
    recent_convs = await db.conversations.find({}, {"_id": 0}).sort("last_message_at", -1).limit(5).to_list(5)
    top_customers = await db.customers.find({}, {"_id": 0, "id": 1, "name": 1, "total_spent": 1}).sort("total_spent", -1).limit(5).to_list(5)
    
    return DashboardStats(
        total_customers=total_customers,
        active_conversations=active_conversations,
        open_topics=open_topics,
        pending_orders=pending_orders,
        total_revenue=total_revenue,
        recent_conversations=recent_convs,
        top_customers=top_customers
    )

# ============== SETTINGS ==============

@api_router.get("/settings")
async def get_settings(user: dict = Depends(get_current_user)):
    settings = await db.settings.find_one({"type": "global"}, {"_id": 0})
    if not settings:
        settings = {
            "type": "global",
            "business_name": "Sales Brain",
            "escalation_phone": "+91 98765 43210",
            "follow_up_days": 3,
            "ai_enabled": True,
            "auto_reply": True,
            "inactivity_summary_minutes": 30
        }
        await db.settings.insert_one(settings)
    return settings

@api_router.put("/settings")
async def update_settings(settings: Dict[str, Any], user: dict = Depends(get_current_user)):
    await db.settings.update_one({"type": "global"}, {"$set": settings}, upsert=True)
    return {"message": "Settings updated"}

# ============== SEED DATA ==============

@api_router.post("/seed")
async def seed_data():
    existing = await db.customers.count_documents({})
    if existing > 0:
        return {"message": "Database already seeded"}
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Sample KB articles
    kb_articles = [
        {"id": str(uuid.uuid4()), "title": "Return Policy", "category": "policy", "content": "Returns accepted within 7 days of purchase with original packaging. Refund processed within 5-7 business days.", "tags": ["return", "refund"], "is_active": True, "created_at": now, "updated_at": now},
        {"id": str(uuid.uuid4()), "title": "Delivery Timelines", "category": "policy", "content": "Standard delivery: 3-5 business days. Express delivery: 1-2 business days. Same-day delivery available in select cities.", "tags": ["delivery", "shipping"], "is_active": True, "created_at": now, "updated_at": now},
        {"id": str(uuid.uuid4()), "title": "Warranty Information", "category": "policy", "content": "All Apple products come with 1-year manufacturer warranty. Extended warranty available for purchase.", "tags": ["warranty", "apple"], "is_active": True, "created_at": now, "updated_at": now},
        {"id": str(uuid.uuid4()), "title": "Screen Repair Process", "category": "procedure", "content": "1. Bring device to store 2. Diagnostic check (30 mins) 3. Quote provided 4. Repair (1-3 hours) 5. Quality check 6. Pickup", "tags": ["repair", "screen"], "is_active": True, "created_at": now, "updated_at": now},
        {"id": str(uuid.uuid4()), "title": "Payment Methods", "category": "faq", "content": "We accept: Cash, Credit/Debit Cards, UPI, Net Banking, EMI options available on purchases above ₹10,000", "tags": ["payment", "emi"], "is_active": True, "created_at": now, "updated_at": now},
    ]
    await db.knowledge_base.insert_many(kb_articles)
    
    # Sample customers
    customers = [
        {"id": str(uuid.uuid4()), "name": "Rahul Sharma", "email": "rahul@example.com", "phone": "+91 98765 12345", "customer_type": "individual", "addresses": [{"type": "home", "address": "123 MG Road, Bangalore 560001"}], "preferences": {"communication": "whatsapp", "language": "english"}, "purchase_history": [], "devices": [{"type": "iPhone 14 Pro", "purchased": "2023-06-15"}], "tags": ["premium", "apple-user"], "notes": "Prefers evening calls", "total_spent": 125000, "last_interaction": now, "created_at": now},
        {"id": str(uuid.uuid4()), "name": "Priya Patel", "email": "priya@techcorp.com", "phone": "+91 87654 32109", "customer_type": "employee", "company_id": None, "addresses": [{"type": "office", "address": "Tech Park, Whitefield, Bangalore"}], "preferences": {"communication": "email"}, "purchase_history": [], "devices": [{"type": "MacBook Pro M2", "purchased": "2024-01-10"}], "tags": ["corporate"], "notes": "", "total_spent": 250000, "last_interaction": now, "created_at": now},
        {"id": str(uuid.uuid4()), "name": "Amit Kumar", "email": "amit.k@gmail.com", "phone": "+91 76543 21098", "customer_type": "individual", "addresses": [{"type": "home", "address": "45 Gandhi Nagar, Delhi 110031"}], "preferences": {}, "purchase_history": [], "devices": [], "tags": ["new"], "notes": "", "total_spent": 0, "last_interaction": None, "created_at": now}
    ]
    await db.customers.insert_many(customers)
    
    # Sample products
    products = [
        {"id": str(uuid.uuid4()), "name": "iPhone 15 Pro Max", "description": "Latest Apple flagship with A17 Pro chip", "category": "Smartphones", "sku": "IPHONE-15-PRO-MAX", "base_price": 159900, "tax_rate": 18, "stock": 25, "images": [], "specifications": {"storage": "256GB", "color": "Natural Titanium"}, "is_active": True, "created_at": now},
        {"id": str(uuid.uuid4()), "name": "AirPods Pro 2nd Gen", "description": "Active Noise Cancellation, Adaptive Audio", "category": "Audio", "sku": "AIRPODS-PRO-2", "base_price": 24900, "tax_rate": 18, "stock": 50, "images": [], "specifications": {"type": "In-ear", "anc": True}, "is_active": True, "created_at": now},
        {"id": str(uuid.uuid4()), "name": "MacBook Air M3", "description": "Supercharged by M3 chip", "category": "Laptops", "sku": "MBA-M3-256", "base_price": 114900, "tax_rate": 18, "stock": 15, "images": [], "specifications": {"storage": "256GB", "ram": "8GB"}, "is_active": True, "created_at": now},
        {"id": str(uuid.uuid4()), "name": "Screen Repair Service", "description": "Professional screen replacement for iPhones", "category": "Services", "sku": "SVC-SCREEN-REPAIR", "base_price": 8999, "tax_rate": 18, "stock": 999, "images": [], "specifications": {"warranty": "90 days"}, "is_active": True, "created_at": now}
    ]
    await db.products.insert_many(products)
    
    # Sample conversation
    conv_id = str(uuid.uuid4())
    conv = {"id": conv_id, "customer_id": customers[0]["id"], "customer_name": customers[0]["name"], "customer_phone": customers[0]["phone"], "channel": "whatsapp", "status": "active", "last_message": "I want to buy AirPods Pro", "last_message_at": now, "unread_count": 1, "created_at": now}
    await db.conversations.insert_one(conv)
    
    messages = [
        {"id": str(uuid.uuid4()), "conversation_id": conv_id, "content": "Hi, I'm interested in buying new AirPods", "sender_type": "customer", "message_type": "text", "attachments": [], "created_at": now},
        {"id": str(uuid.uuid4()), "conversation_id": conv_id, "content": "Hello Rahul! Great choice. Are you looking for AirPods Pro 2nd Gen or the regular AirPods 3rd Gen?", "sender_type": "ai", "message_type": "text", "attachments": [], "created_at": now},
        {"id": str(uuid.uuid4()), "conversation_id": conv_id, "content": "I want to buy AirPods Pro", "sender_type": "customer", "message_type": "text", "attachments": [], "created_at": now}
    ]
    await db.messages.insert_many(messages)
    
    topic = {"id": str(uuid.uuid4()), "conversation_id": conv_id, "customer_id": customers[0]["id"], "topic_type": "product_inquiry", "title": "AirPods Pro Purchase", "status": "open", "device_info": None, "metadata": {"product": "AirPods Pro 2nd Gen"}, "created_at": now, "updated_at": now}
    await db.topics.insert_one(topic)
    
    return {"message": "Database seeded successfully", "customers": len(customers), "products": len(products), "kb_articles": len(kb_articles)}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
