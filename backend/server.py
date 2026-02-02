from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
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
import asyncio
import requests

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
    payment_preferences: Dict[str, Any] = {}  # Card, UPI, Bank Transfer preferences
    purchase_history: List[Dict[str, Any]] = []
    devices: List[Dict[str, Any]] = []
    tags: List[str] = []
    notes: str = ""  # Legacy single note
    notes_history: List[Dict[str, Any]] = []  # Multiple notes with timestamps
    invoices: List[Dict[str, Any]] = []  # Uploaded invoice files
    ai_insights: Dict[str, Any] = {}  # AI-collected data from chats
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
    status: str  # active, escalated, waiting_for_owner, resolved
    last_message: Optional[str] = None
    last_message_at: Optional[str] = None
    unread_count: int = 0
    topics: List[TopicResponse] = []
    created_at: str
    # Status tracking fields
    escalated_at: Optional[str] = None
    escalation_reason: Optional[str] = None
    sla_deadline: Optional[str] = None  # When owner must respond by
    sla_reminders_sent: int = 0

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
    escalation_code: str  # Human-readable code like ESC01, ESC02
    customer_id: str
    customer_name: str
    customer_phone: Optional[str] = None
    conversation_id: Optional[str] = None
    reason: str
    message_content: str
    status: str  # pending_owner_reply, owner_replied, resolved, marked_irrelevant
    priority: str
    sla_deadline: Optional[str] = None
    sla_reminders_sent: int = 0
    owner_reply: Optional[str] = None
    formatted_reply: Optional[str] = None
    kb_article_id: Optional[str] = None  # Linked KB article if any
    relevance: str = "relevant"  # relevant, irrelevant
    created_at: str
    resolved_at: Optional[str] = None

# Unanswered Question Response (for dashboard)
class UnansweredQuestionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    escalation_code: str
    customer_name: str
    customer_phone: str
    question: str
    reason: str
    status: str
    relevance: str
    conversation_count: int = 1
    created_at: str
    sla_deadline: Optional[str] = None
    is_overdue: bool = False
    linked_kb_id: Optional[str] = None
    linked_kb_title: Optional[str] = None

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

# Excluded Numbers Model (Silent Monitoring)
class ExcludedNumberCreate(BaseModel):
    phone: str
    tag: str = "other"  # dealer, vendor, internal, other
    reason: str = ""
    is_temporary: bool = False

# KB Article Create Model (for unanswered questions)
class KbArticleCreateRequest(BaseModel):
    title: str
    content: str
    category: str = "FAQ"
    tags: List[str] = []

class ExcludedNumberResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    phone: str
    tag: str
    reason: str
    is_temporary: bool
    created_at: str
    created_by: str

# Lead Injection Model
class LeadInjectionCreate(BaseModel):
    customer_name: str
    phone: str
    product_interest: str
    notes: str = ""

class LeadInjectionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    customer_id: str
    customer_name: str
    phone: str
    product_interest: str
    conversation_id: str
    topic_id: str
    outbound_message_sent: bool
    status: str  # pending, in_progress, completed, escalated
    notes: str
    created_at: str
    created_by: str

# Auto-Messaging Models
class AutoMessageTemplate(BaseModel):
    trigger_type: str  # no_response, order_confirmed, payment_received, ticket_created, ticket_resolved, ai_uncertain
    message_template: str
    is_enabled: bool = True
    delay_hours: int = 0  # Delay before sending (for follow-ups)

class AutoMessageSettings(BaseModel):
    max_messages_per_topic: int = 3
    cooldown_hours: int = 24  # Min hours between auto-messages to same customer
    dnd_start_hour: int = 21  # 9 PM
    dnd_end_hour: int = 9     # 9 AM
    no_response_days: int = 2  # Days before no-response follow-up
    auto_messaging_enabled: bool = True

class ScheduledMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    customer_id: str
    customer_phone: str
    conversation_id: str
    topic_id: Optional[str]
    trigger_type: str
    message: str
    scheduled_for: str
    status: str  # pending, sent, cancelled
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

async def generate_escalation_code() -> str:
    """Generate a unique human-readable escalation code like ESC01, ESC02, etc."""
    # Find the highest existing code number
    latest = await db.escalations.find_one(
        {"escalation_code": {"$exists": True}},
        {"escalation_code": 1, "_id": 0},
        sort=[("created_at", -1)]
    )
    
    if latest and latest.get("escalation_code"):
        try:
            # Extract number from ESC01, ESC02, etc.
            code = latest["escalation_code"]
            num = int(code.replace("ESC", ""))
            return f"ESC{num + 1:02d}"
        except:
            pass
    
    # Count existing escalations as fallback
    count = await db.escalations.count_documents({})
    return f"ESC{count + 1:02d}"

def parse_escalation_code_from_message(message: str) -> tuple:
    """Parse escalation code from owner reply message.
    
    Expected formats:
    - "ESC01: Here's the answer..."
    - "ESC01 Here's the answer..."
    - "esc01: answer"
    
    Returns: (escalation_code, actual_reply) or (None, original_message)
    """
    import re
    
    # Pattern: ESC followed by digits, optionally followed by : or space
    pattern = r'^(ESC\d+)[:\s]+(.+)$'
    match = re.match(pattern, message.strip(), re.IGNORECASE)
    
    if match:
        code = match.group(1).upper()
        reply = match.group(2).strip()
        return (code, reply)
    
    return (None, message)

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

# ============== AI INSIGHTS EXTRACTION ==============

async def extract_and_store_ai_insights(customer_id: str, message: str, ai_response: str):
    """Extract insights from customer messages and store them.
    
    Collects: product interests, preferences, budget mentions, issues, sentiments
    """
    try:
        # Get current insights
        customer = await db.customers.find_one({"id": customer_id}, {"_id": 0, "ai_insights": 1})
        current_insights = customer.get("ai_insights", {}) if customer else {}
        
        # Initialize structure
        if "product_interests" not in current_insights:
            current_insights["product_interests"] = []
        if "mentioned_issues" not in current_insights:
            current_insights["mentioned_issues"] = []
        if "preferences" not in current_insights:
            current_insights["preferences"] = {}
        if "interaction_count" not in current_insights:
            current_insights["interaction_count"] = 0
        
        # Update interaction count
        current_insights["interaction_count"] += 1
        current_insights["last_interaction"] = datetime.now(timezone.utc).isoformat()
        
        # Simple keyword extraction for product interests
        message_lower = message.lower()
        product_keywords = [
            "iphone", "ipad", "mac", "macbook", "airpods", "apple watch", 
            "imac", "mac mini", "mac pro", "samsung", "dell", "hp", "lenovo",
            "laptop", "desktop", "monitor", "printer", "keyboard", "mouse"
        ]
        
        for keyword in product_keywords:
            if keyword in message_lower and keyword not in current_insights["product_interests"]:
                current_insights["product_interests"].append(keyword)
        
        # Detect budget mentions
        import re
        budget_pattern = r'budget.*?(\d+[,\d]*)|(\d+[,\d]*)\s*(k|lakh|lac|rupee|rs)'
        budget_match = re.search(budget_pattern, message_lower)
        if budget_match:
            current_insights["preferences"]["budget_mentioned"] = True
            current_insights["preferences"]["last_budget_mention"] = message[:100]
        
        # Detect issue mentions
        issue_keywords = ["broken", "not working", "repair", "fix", "problem", "issue", "help", "error", "stuck", "slow"]
        for keyword in issue_keywords:
            if keyword in message_lower:
                if keyword not in current_insights["mentioned_issues"]:
                    current_insights["mentioned_issues"].append(keyword)
                current_insights["preferences"]["needs_support"] = True
                break
        
        # Detect preferences
        if "urgent" in message_lower or "asap" in message_lower or "fast" in message_lower:
            current_insights["preferences"]["urgency"] = "high"
        if "delivery" in message_lower:
            current_insights["preferences"]["interested_in_delivery"] = True
        if "emi" in message_lower or "installment" in message_lower:
            current_insights["preferences"]["interested_in_emi"] = True
        
        # Store updated insights
        await db.customers.update_one(
            {"id": customer_id},
            {"$set": {"ai_insights": current_insights}}
        )
        
    except Exception as e:
        logger.error(f"Error extracting AI insights: {e}")

# ============== EXCLUDED NUMBERS HELPERS ==============

async def is_number_excluded(phone: str) -> bool:
    """Check if a phone number is in the exclusion list"""
    # Normalize phone number - remove all non-digits
    normalized = phone.replace("+", "").replace(" ", "").replace("-", "")
    if len(normalized) > 10:
        normalized = normalized[-10:]  # Get last 10 digits
    
    # Also create patterns for common phone formats
    # This will match stored phones with different formatting
    excluded = await db.excluded_numbers.find_one({
        "$or": [
            {"phone": {"$regex": normalized}},
            {"phone": {"$regex": normalized[-10:] if len(normalized) >= 10 else normalized}},
            {"phone": phone}
        ]
    })
    return excluded is not None

async def get_excluded_number_info(phone: str) -> Optional[Dict]:
    """Get exclusion info for a number"""
    normalized = phone.replace("+", "").replace(" ", "").replace("-", "")
    if len(normalized) > 10:
        normalized = normalized[-10:]
    
    return await db.excluded_numbers.find_one({
        "$or": [
            {"phone": {"$regex": normalized}},
            {"phone": {"$regex": normalized[-10:] if len(normalized) >= 10 else normalized}},
            {"phone": phone}
        ]
    }, {"_id": 0})

# ============== OWNER COMMAND PARSING ==============

def parse_lead_injection_command(message: str) -> Optional[Dict]:
    """Parse owner lead injection command - FLEXIBLE FORMAT PARSER
    
    Supported Formats:
    - "lead inject iPhone 17 Foram 9969528677"
    - "lead inject CKM - 9820983978 AirPods Pro"
    - "lead inject Rahul 9876543210 MacBook Air M3"
    - "lead inject iPhone 17\nForam 9969528677" (Product on line 1, Name+Phone on line 2)
    - "Lead: Name - Number - Product"
    """
    import re
    
    # Check if this is a lead inject message
    if not re.search(r'lead\s*inject', message, re.IGNORECASE):
        if not re.search(r'(customer\s+name|lead\s*:)', message, re.IGNORECASE):
            return None
    
    # Extract phone number (mandatory)
    phone_match = re.search(r'(\d{10,12})', message)
    if not phone_match:
        return None
    
    phone = phone_match.group(1)
    
    # Product keywords to identify what is a product vs name
    product_keywords = ['iphone', 'macbook', 'ipad', 'airpods', 'watch', 'pro', 'max', 'air', 'mini', 'apple', 'samsung', 'pixel', 'galaxy']
    
    customer_name = "Unknown"
    product_interest = "General Inquiry"
    
    # Remove "lead inject" prefix
    clean_msg = re.sub(r'lead\s*inject\s*', '', message, flags=re.IGNORECASE).strip()
    
    # Split by lines first - this helps with multi-line formats
    lines = [l.strip() for l in clean_msg.split('\n') if l.strip()]
    
    if len(lines) >= 2:
        # Multi-line format - analyze each line
        phone_line_idx = -1
        for i, line in enumerate(lines):
            if phone in line:
                phone_line_idx = i
                break
        
        if phone_line_idx >= 0:
            phone_line = lines[phone_line_idx]
            other_lines = [l for i, l in enumerate(lines) if i != phone_line_idx]
            
            # Extract name from the phone line (word before or after phone)
            name_before = re.search(r'([A-Za-z]+)\s*[-]?\s*' + phone, phone_line)
            name_after = re.search(phone + r'\s*[-]?\s*([A-Za-z]+)', phone_line)
            
            if name_before:
                customer_name = name_before.group(1).capitalize()
            elif name_after:
                customer_name = name_after.group(1).capitalize()
            
            # Product is likely in the other lines
            for line in other_lines:
                if any(kw in line.lower() for kw in product_keywords) or re.search(r'\d', line):
                    product_interest = line
                    break
            
            # If no product found in other lines, check phone line for remaining text
            if product_interest == "General Inquiry" and other_lines:
                product_interest = ' '.join(other_lines)
    else:
        # Single line format - normalized
        normalized = ' '.join(clean_msg.split())
        
        phone_pos = normalized.find(phone)
        before_phone = normalized[:phone_pos].strip(' -') if phone_pos > 0 else ""
        after_phone = normalized[phone_pos + len(phone):].strip(' -') if phone_pos >= 0 else normalized
        
        # Check for name immediately adjacent to phone
        name_before_match = re.search(r'([A-Za-z]+)\s*$', before_phone)
        name_after_match = re.search(r'^([A-Za-z]+)', after_phone)
        
        before_is_product = any(kw in before_phone.lower() for kw in product_keywords) or re.search(r'\d', before_phone)
        after_is_product = any(kw in after_phone.lower() for kw in product_keywords) or re.search(r'\d', after_phone)
        
        if before_is_product and name_after_match:
            product_interest = before_phone
            customer_name = name_after_match.group(1).capitalize()
        elif after_is_product and name_before_match:
            customer_name = name_before_match.group(1).capitalize()
            product_interest = after_phone
        elif before_phone and after_phone:
            # Default: first part with products is product, other is name
            if before_is_product:
                product_interest = before_phone
                customer_name = after_phone.split()[0].capitalize() if after_phone else "Unknown"
            else:
                customer_name = before_phone.split()[-1].capitalize() if before_phone else "Unknown"
                product_interest = after_phone if after_phone else "General Inquiry"
        elif before_phone:
            # Name at start, product after
            words = before_phone.split()
            if len(words) >= 2 and not any(kw in words[0].lower() for kw in product_keywords):
                customer_name = words[0].capitalize()
                product_interest = ' '.join(words[1:])
            else:
                product_interest = before_phone
        elif after_phone:
            product_interest = after_phone
    
    # Final cleanup
    product_interest = re.sub(r'^(a|an|the)\s+', '', product_interest, flags=re.IGNORECASE).strip()
    if not product_interest:
        product_interest = "General Inquiry"
    
    return {
        "customer_name": customer_name if customer_name else "Unknown",
        "phone": phone,
        "product_interest": product_interest
    }

# ============== AI AUTO-REPLY HELPERS ==============

async def generate_ai_reply(customer_id: str, conversation_id: str, message: str, retry_count: int = 0) -> str:
    """Generate AI reply for a customer message - STRICT FLOW CONTROL SYSTEM"""
    try:
        import re
        
        # Load customer context
        customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
        if not customer:
            return None
        
        # Load settings
        settings = await db.settings.find_one({"type": "global"}, {"_id": 0})
        ai_instructions = settings.get("ai_instructions", "") if settings else ""
        business_name = settings.get("business_name", "NeoStore") if settings else "NeoStore"
        
        # ========== LOAD AI BEHAVIOR POLICY ==========
        ai_policy = await get_ai_policy_config()
        policy_enabled = ai_policy.get("enabled", True)
        global_rules = ai_policy.get("global_rules", {})
        states_config = ai_policy.get("states", {})
        response_rules = ai_policy.get("response_rules", {})
        fallback_rules = ai_policy.get("fallback", {})
        system_triggers = ai_policy.get("system_triggers", {})
        
        # Log policy scan
        logger.info(f"AI Policy Scan - Enabled: {policy_enabled}, Topics: {len(global_rules.get('allowed_topics', []))}, States: {len(states_config)}, Response Rules: {len(response_rules)}")
        
        # ========== STEP 1: CONTEXT FETCH ==========
        # Fetch customer profile with ALL 360° data
        addresses = customer.get('addresses', [])
        addresses_str = "\n".join([
            f"  - {addr.get('type', 'Address').title()}: {addr.get('address', addr.get('full_address', 'N/A'))}"
            for addr in addresses
        ]) if addresses else "  No addresses on file"
        
        devices = customer.get('devices', [])
        devices_str = ", ".join([d.get('model', d.get('type', '')) for d in devices[:5]]) if devices else "None"
        
        payment_prefs = customer.get('payment_preferences', {})
        payment_str = f"Preferred: {payment_prefs.get('preferred_method', 'Not set')}, UPI: {payment_prefs.get('upi_id', 'N/A')}"
        
        customer_profile = f"""
=== CUSTOMER 360° PROFILE ===
Name: {customer.get('name', 'Unknown')}
Phone: {customer.get('phone', 'Unknown')}
Email: {customer.get('email', 'Not set')}
Type: {customer.get('customer_type', 'individual')}
Company: {customer.get('company', 'N/A')}
Tags: {', '.join(customer.get('tags', [])) or 'None'}

**SAVED ADDRESSES:**
{addresses_str}

**DEVICES OWNED:**
{devices_str}

**PAYMENT INFO:**
{payment_str}

**NOTES:**
{customer.get('notes', 'No notes')[:300]}

**AI INSIGHTS:**
{customer.get('ai_insights', {}).get('summary', 'No insights yet')}
"""
        
        # Fetch past enquiries (conversation history)
        past_messages = await db.messages.find(
            {"conversation_id": conversation_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(20).to_list(20)
        
        conversation_history = "\n".join([
            f"{'Customer' if m.get('sender_type') == 'customer' else 'Assistant'}: {m.get('content', '')[:150]}"
            for m in reversed(past_messages)
        ]) if past_messages else "No previous messages"
        
        # ========== STEP 2: KNOWLEDGE LOOKUP ==========
        # Search KB
        kb_articles = await db.knowledge_base.find(
            {"is_active": True}, 
            {"_id": 0, "title": 1, "content": 1, "category": 1}
        ).to_list(50)
        kb_content = "\n\n".join([
            f"[{kb.get('category', 'general').upper()}] {kb['title']}:\n{kb['content'][:500]}"
            for kb in kb_articles
        ]) if kb_articles else ""
        
        # Search Products (Excel/Database)
        products = await db.products.find(
            {"is_active": True},
            {"_id": 0, "name": 1, "base_price": 1, "category": 1, "sku": 1}
        ).to_list(200)
        product_catalog = "\n".join([
            f"• {p['name']}: Rs.{p.get('base_price', 0):,.0f}"
            for p in products
        ]) if products else ""
        
        # Check if we have ANY verified sources
        has_kb = len(kb_articles) > 0
        has_products = len(products) > 0
        source_verified = has_kb or has_products
        
        # ========== PRE-CHECK: Detect conversation state using POLICY ==========
        simple_message = message.strip().lower()
        
        # Get state triggers from policy
        greeting_state = states_config.get("GREETING", {})
        closure_state = states_config.get("CLOSURE", {})
        
        # Pure greetings (from policy or defaults)
        pure_greetings = greeting_state.get("triggers", ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "hii", "hiii", "hlo", "helo"])
        is_pure_greeting = simple_message in pure_greetings
        
        # Closure triggers (from policy or defaults)
        closure_triggers = closure_state.get("triggers", ["thanks", "thank you", "ok", "okay", "bye", "goodbye"])
        is_closure_message = simple_message in closure_triggers
        closure_templates = closure_state.get("templates", {})
        
        # ========== DETECT CONFIRMATION AFTER "LET ME CHECK" ==========
        # If last AI message was "let me check pricing" and customer says "sure/ok/yes", ESCALATE immediately
        confirmation_words = ["sure", "ok", "okay", "yes", "yeah", "yep", "go ahead", "please", "please do", "alright", "fine", "pricing"]
        is_confirmation = simple_message in confirmation_words or any(w in simple_message for w in confirmation_words)
        
        last_ai_message = ""
        if past_messages:
            for m in past_messages:  # Already sorted desc
                if m.get('sender_type') == 'ai':
                    last_ai_message = m.get('content', '').lower()
                    break
        
        # Check if last AI message indicated "checking" something
        checking_patterns = ["let me check", "allow me a moment", "checking", "i'll confirm", "will get back", "need to verify"]
        ai_was_checking = any(p in last_ai_message for p in checking_patterns)
        
        if is_confirmation and ai_was_checking:
            logger.info(f"Customer confirmed after AI checking - escalating immediately")
            # Escalate now
            await escalate_to_owner(customer, conversation_history, message, f"Customer confirmed - needs pricing/info")
            return "Got it! Let me get that information for you - will update shortly."
        
        # Check if this is the FIRST message or a fresh greeting
        is_first_message = len(past_messages) == 0
        
        # For pure greetings, we should NOT load conversation history context
        # This prevents the AI from referencing old topics (policy enforcement)
        if is_pure_greeting and greeting_state.get("enabled", True):
            forbidden = greeting_state.get("forbidden_actions", [])
            if "past_context_reference" in forbidden:
                conversation_history = "[Fresh greeting - do not reference past topics]"
        
        # Check for pending escalation for this customer
        pending_escalation = await db.escalations.find_one(
            {"customer_id": customer_id, "status": "pending_owner_reply"},
            {"_id": 0}
        )
        
        # ========== STEP 3: DECISION LOGIC ==========
        # Build context about pending escalation if any
        pending_context = ""
        if pending_escalation:
            pending_context = f"""
=== PENDING ESCALATION ===
There is already a pending question waiting for owner response:
- Code: {pending_escalation.get('escalation_code', 'N/A')}
- Question: "{pending_escalation.get('customer_message', '')[:100]}"
- Status: Waiting for owner to respond

If customer asks follow-up about this, acknowledge that you are still waiting for the answer.
Do NOT create another escalation for the same topic.
"""
        
        # ========== BUILD DYNAMIC PROMPT FROM POLICY ==========
        # Extract all policy parameters
        allowed_topics = global_rules.get("allowed_topics", ["apple_products", "apple_repairs", "it_products", "it_services"])
        disallowed_behaviors = global_rules.get("disallowed_behavior", [])
        scope_message = global_rules.get("scope_message", "I can help with Apple products, repairs, and IT services.")
        
        # Response rules from policy
        greeting_limit = response_rules.get("greeting_limit", "once_per_conversation")
        question_limit = response_rules.get("question_limit", "one_at_a_time")
        max_response_length = response_rules.get("max_response_length", 150)
        tone = response_rules.get("tone", "friendly_professional")
        language = response_rules.get("language", "english_hinglish")
        emoji_usage = response_rules.get("emoji_usage", "minimal")
        
        # State configurations from policy
        intent_state = states_config.get("INTENT_COLLECTION", {})
        action_state = states_config.get("ACTION", {})
        escalation_state = states_config.get("ESCALATION", {})
        
        # Build disallowed behaviors string
        disallowed_str = "\n".join([f"- NEVER: {b.replace('_', ' ')}" for b in disallowed_behaviors]) if disallowed_behaviors else ""
        
        # Build state rules from policy
        greeting_response = greeting_state.get("response_template", "Hi! How can I help you today?")
        greeting_forbidden = greeting_state.get("forbidden_actions", [])
        intent_clarification = intent_state.get("clarification_template", "Got it. Could you tell me more?")
        action_sales = action_state.get("sales_flow", {})
        action_repair = action_state.get("repair_flow", {})
        escalation_placeholder = escalation_state.get("placeholder_message", "Let me check and get back to you.")
        
        # Fallback rules from policy
        unclear_fallback = fallback_rules.get("unclear_data", {}).get("template", "Could you please explain a bit more?")
        out_of_scope_fallback = fallback_rules.get("out_of_scope", {}).get("template", scope_message)
        
        system_prompt = f"""You are CHARU - a real person chatting on WhatsApp. NOT a bot.

=== AI BEHAVIOR POLICY (SCAN ALL BEFORE REPLYING) ===

**POLICY STATUS:** {"ENFORCED" if policy_enabled else "DISABLED"}

**ALLOWED TOPICS (ONLY talk about these):**
{chr(10).join([f"- {t.replace('_', ' ').title()}" for t in allowed_topics])}

**DISALLOWED BEHAVIORS:**
{disallowed_str if disallowed_str else "- None specified"}

**RESPONSE CONSTRAINTS:**
- Greeting: {greeting_limit}
- Questions: {question_limit}
- Max length: {max_response_length} characters
- Tone: {tone.replace('_', ' ')}
- Language: {language.replace('_', '/')}
- Emojis: {emoji_usage}

=== CONVERSATION STATES (DETECT & FOLLOW) ===

**CURRENT MESSAGE:** "{message}"
**FIRST MESSAGE:** {"Yes" if is_first_message else "No"}
**PREVIOUS CONTEXT:** {len(past_messages)} messages in history

**STATE 1: GREETING** (Enabled: {greeting_state.get("enabled", True)})
Triggers: {', '.join(greeting_state.get("triggers", ["hi", "hello"]))}
Response: "{greeting_response}"
Forbidden: {', '.join(greeting_forbidden) if greeting_forbidden else "None"}

**STATE 2: INTENT COLLECTION** (Enabled: {intent_state.get("enabled", True)})
Triggers: {', '.join(intent_state.get("triggers", ["need", "want", "looking"]))}
Clarification: "{intent_clarification}"
Rules: Ask ONE question at a time, wait for response

**STATE 3: ACTION** (Enabled: {action_state.get("enabled", True)})
Sales: Mention delivery only if asked = {action_sales.get("mention_delivery_only_if_asked", True)}
Repairs: Ask one field at a time = {action_repair.get("ask_one_field_at_a_time", True)}
Required repair fields: {', '.join(action_repair.get("required_fields", ["device_model", "issue_description"]))}

**STATE 4: CLOSURE** (Enabled: {closure_state.get("enabled", True)})
Triggers: {', '.join(closure_state.get("triggers", ["thanks", "bye"]))}

**STATE 5: ESCALATION** (Enabled: {escalation_state.get("enabled", True)})
Placeholder: "{escalation_placeholder}"
Notify owner: {escalation_state.get("notify_owner", True)}

=== FALLBACK RESPONSES ===
- Unclear data: "{unclear_fallback}"
- Out of scope: "{out_of_scope_fallback}"

=== STRICT RULES (ENFORCED) ===
1. NEVER greet more than once ({greeting_limit})
2. NEVER reference past topics on fresh greeting
3. NEVER mention delivery unless customer asks
4. NEVER guess prices - use catalog or say ESCALATE_REQUIRED
5. NEVER ask multiple questions at once
6. Keep replies under {max_response_length} characters
7. Sound human, {tone.replace('_', ' ')}, not robotic
8. NEVER ask customer for SKU, product code, item code, model number, or part number - customers don't know these
9. If customer says "sure", "ok", "yes", "pricing" after you said "let me check" - say ESCALATE_REQUIRED
10. CHECK CUSTOMER 360° PROFILE FIRST - if address exists, use it! Don't ask for info you already have
11. If customer asks "send to my office/home", check SAVED ADDRESSES and confirm the address you have

=== SCOPE LOCK ===
OUT OF SCOPE MESSAGE: "{scope_message}"

=== VERIFIED DATA SOURCES ===

**PRODUCT CATALOG:**
{product_catalog if product_catalog else "[No products loaded]"}

**KNOWLEDGE BASE:**
{kb_content if kb_content else "[No KB articles loaded]"}

=== CUSTOMER CONTEXT ===
{customer_profile}

=== CONVERSATION HISTORY ===
{conversation_history}

{f"=== BUSINESS RULES ==={chr(10)}{ai_instructions}" if ai_instructions else ""}
{pending_context}

=== INSTRUCTION ===
1. First, identify which STATE this message belongs to
2. Check if the answer exists in PRODUCT CATALOG or KB
3. Apply all POLICY CONSTRAINTS
4. If info not found, output ONLY: "ESCALATE_REQUIRED"
5. Generate a {tone.replace('_', ' ')} response under {max_response_length} chars

Your reply:"""

        # Generate response
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"conv-{conversation_id}",
            system_message="You are Charu - a friendly store owner chatting on WhatsApp. Keep replies short (1-2 lines), sound human, be warm. Never sound like a bot."
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=system_prompt))
        
        # ========== STEP 3: RESPONSE VALIDATION ==========
        if not response or len(response.strip()) == 0:
            if retry_count < 1:
                return await generate_ai_reply(customer_id, conversation_id, message, retry_count + 1)
            await escalate_to_owner(customer, conversation_history, message, "AI returned empty response")
            return "Let me check this and get back to you."
        
        # Check for ESCALATE_REQUIRED or similar patterns
        needs_escalation = False
        escalation_reason = ""
        
        # Direct escalation markers
        escalation_markers = ["ESCALATE_REQUIRED", "ESCALATE:", "NOT_FOUND:"]
        for marker in escalation_markers:
            if marker in response.upper():
                needs_escalation = True
                escalation_reason = f"Query: {message[:60]}"
                break
        
        # Forbidden phrases that indicate guessing (BLOCK these)
        forbidden_patterns = [
            r"\bi think\b",
            r"\busually\b",
            r"\bestimated\b",
            r"\bmost likely\b",
            r"\bbased on experience\b",
            r"\byou can consider\b",
            r"\bprobably\b",
            r"\bmight be\b",
            r"\bcould be around\b",
            r"\bapproximately\b",
            r"\bsku\b",
            r"\bproduct code\b",
            r"\bitem code\b",
            r"\bmodel number\b",
            r"\bpart number\b"
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, response.lower()):
                logger.warning(f"AI used forbidden phrase, blocking response")
                needs_escalation = True
                escalation_reason = f"AI attempted guess for: {message[:50]}"
                break
        
        # Info-not-found patterns
        not_found_patterns = [
            r"we do not have",
            r"not in our (list|catalog|database)",
            r"no pricing",
            r"i('ll| will) need to check",
            r"let me (check|verify|confirm)",
            r"could not find",
            r"not available",
            r"do not have .* information"
        ]
        
        for pattern in not_found_patterns:
            if re.search(pattern, response.lower()):
                needs_escalation = True
                escalation_reason = f"Missing info: {message[:50]}"
                break
        
        # ========== STEP 4: ESCALATE OR RESPOND (POLICY-DRIVEN) ==========
        if needs_escalation:
            # Check if this is a pure greeting - NEVER escalate (policy)
            if is_pure_greeting and greeting_state.get("enabled", True):
                logger.info(f"Pure greeting detected (policy), not escalating: {message}")
                return greeting_state.get("response_template", "Hi! How can I help you today?")
            
            # Check if this is a closure message - handle with templates (policy)
            if is_closure_message and closure_state.get("enabled", True):
                logger.info(f"Closure message detected (policy): {message}")
                # Find matching template
                for trigger, response in closure_templates.items():
                    if trigger in simple_message:
                        return response
                return "Okay! Let me know if you need anything else."
            
            # Check if there is already a pending escalation for this customer
            if pending_escalation:
                escalation_state = states_config.get("ESCALATION", {})
                logger.info(f"Skipping escalation - already pending: {pending_escalation.get('escalation_code')}")
                return escalation_state.get("placeholder_message", "Still checking on that for you - will update shortly!")
            
            logger.info(f"ESCALATING: {escalation_reason}")
            
            # Update conversation status
            await db.conversations.update_one(
                {"id": conversation_id},
                {"$set": {
                    "status": "escalated",
                    "escalated_at": datetime.now(timezone.utc).isoformat(),
                    "escalation_reason": escalation_reason
                }}
            )
            
            # Send escalation to owner
            await escalate_to_owner(customer, conversation_history, message, escalation_reason)
            
            # ONLY allowed response when escalating
            return "Let me check this and get back to you."
        
        # Update conversation status to FOUND
        await db.conversations.update_one(
            {"id": conversation_id},
            {"$set": {"status": "active", "last_ai_response": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Extract and store AI insights from this conversation
        await extract_and_store_ai_insights(customer_id, message, response)
        
        return response
        
    except Exception as e:
        logger.error(f"AI reply error: {e}")
        
        # RETRY: Try once more
        if retry_count < 1:
            logger.info("Retrying AI response after error...")
            return await generate_ai_reply(customer_id, conversation_id, message, retry_count + 1)
        
        # ESCALATE: Notify owner
        try:
            customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
            recent_msgs = await db.messages.find({"conversation_id": conversation_id}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
            history = "\n".join([f"{'Customer' if m.get('sender_type') == 'customer' else 'AI'}: {m.get('content', '')[:100]}" for m in reversed(recent_msgs)])
            await escalate_to_owner(customer, history, message, str(e))
        except:
            pass
        
        return "Let me check on that and get back to you shortly."


async def escalate_to_owner(customer: dict, conversation_history: str, customer_message: str, error_reason: str):
    """Notify owner via WhatsApp when AI cannot respond - with unique escalation ID"""
    try:
        # Get owner phone from settings (check both "global" and "owner" types)
        settings = await db.settings.find_one({"type": "global"}, {"_id": 0})
        if not settings:
            settings = await db.settings.find_one({"type": "owner"}, {"_id": 0})
        
        owner_phone = settings.get("owner_phone") if settings else None
        
        if not owner_phone:
            logger.warning("No owner phone configured for escalation")
            return
        
        # Generate unique escalation code
        escalation_code = await generate_escalation_code()
        
        # Build escalation message with summary
        customer_name = customer.get("name", "Unknown") if customer else "Unknown"
        customer_phone = customer.get("phone", "Unknown") if customer else "Unknown"
        customer_id = customer.get("id") if customer else None
        
        # Create a brief summary instead of raw history
        history_lines = conversation_history.split("\n")[-6:]  # Last 6 messages
        summary = "\n".join(history_lines) if history_lines else "New conversation"
        
        # NEW: Escalation message with unique code
        escalation_msg = f"""*{escalation_code}* - Need Your Input

*Customer:* {customer_name}
*Phone:* {customer_phone}

*Their Question:*
"{customer_message}"

*Quick Context:*
{summary}

---
Reply with: *{escalation_code}: your answer*
Example: {escalation_code}: Yes, we have it in stock"""

        # Send to owner
        await send_whatsapp_message(owner_phone, escalation_msg)
        
        # Calculate SLA deadline (30 minutes from now)
        now = datetime.now(timezone.utc)
        sla_deadline = (now + timedelta(minutes=30)).isoformat()
        escalation_id = str(uuid.uuid4())
        
        # Get conversation_id if available
        conv = await db.conversations.find_one({"customer_id": customer_id}, {"_id": 0, "id": 1}) if customer_id else None
        conversation_id = conv.get("id") if conv else None
        
        # Store escalation for tracking with SLA info and unique code
        await db.escalations.insert_one({
            "id": escalation_id,
            "escalation_code": escalation_code,
            "customer_id": customer_id,
            "customer_phone": customer_phone,
            "customer_name": customer_name,
            "conversation_id": conversation_id,
            "reason": error_reason,
            "customer_message": customer_message,
            "status": "pending_owner_reply",
            "priority": "medium",
            "sla_deadline": sla_deadline,
            "sla_reminders_sent": 0,
            "relevance": "relevant",
            "created_at": now.isoformat()
        })
        
        # Also update the conversation with escalation status
        if customer_id:
            await db.conversations.update_one(
                {"customer_id": customer_id},
                {"$set": {
                    "status": "waiting_for_owner",
                    "escalated_at": now.isoformat(),
                    "escalation_reason": error_reason,
                    "current_escalation_code": escalation_code,
                    "sla_deadline": sla_deadline,
                    "sla_reminders_sent": 0
                }}
            )
        
        logger.info(f"Escalation {escalation_code} sent to owner for customer: {customer_phone}, SLA deadline: {sla_deadline}")
        
    except Exception as e:
        logger.error(f"Failed to escalate to owner: {e}")

async def send_whatsapp_message(phone: str, message: str) -> bool:
    """Send a WhatsApp message via the WhatsApp service"""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: requests.post(
                f"{WA_SERVICE_URL}/send",
                json={"phone": phone, "message": message},
                timeout=30
            )
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {e}")
        return False

# ============== AUTO-MESSAGING HELPERS ==============

# Default message templates
DEFAULT_TEMPLATES = {
    "no_response": "Just checking in - let me know if you need any help with {topic}.",
    "partial_conversation": "Sharing a quick reminder - I was waiting for your response on {topic}.",
    "price_shared": "Let me know if you'd like me to proceed or need any clarification on the pricing.",
    "order_confirmed": "Thanks for confirming your order! I'm sharing the payment details below. Total: Rs.{amount}",
    "payment_received": "Payment received [OK] We will update you once the order is processed.",
    "order_completed": "Your order has been completed. Let us know if you need anything else!",
    "ticket_created": "We've created a support ticket for this. Ticket ID: #{ticket_id}",
    "ticket_updated": "Quick update - your ticket #{ticket_id} is now being worked on.",
    "ticket_resolved": "This issue has been resolved. Please let us know if you face it again.",
    "ai_uncertain": "Let me check this and get back to you shortly.",
    "human_takeover": "I'm personally looking into this for you."
}

async def get_auto_message_settings() -> dict:
    """Get auto-messaging settings"""
    settings = await db.auto_message_settings.find_one({"type": "global"}, {"_id": 0})
    if not settings:
        settings = {
            "type": "global",
            "max_messages_per_topic": 3,
            "cooldown_hours": 24,
            "dnd_start_hour": 21,
            "dnd_end_hour": 9,
            "no_response_days": 2,
            "auto_messaging_enabled": True,
            "templates": DEFAULT_TEMPLATES
        }
        await db.auto_message_settings.insert_one(settings.copy())
        # Remove _id if it was added
        settings.pop("_id", None)
    return settings

async def can_send_auto_message(customer_id: str, topic_id: str = None) -> tuple:
    """Check if we can send an auto-message (respects anti-spam rules)"""
    settings = await get_auto_message_settings()
    
    if not settings.get("auto_messaging_enabled", True):
        return False, "Auto-messaging disabled"
    
    # Check if number is excluded
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0, "phone": 1})
    if customer and await is_number_excluded(customer.get("phone", "")):
        return False, "Number is excluded"
    
    # Check DND window
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    dnd_start = settings.get("dnd_start_hour", 21)
    dnd_end = settings.get("dnd_end_hour", 9)
    
    if dnd_start > dnd_end:  # Spans midnight
        if current_hour >= dnd_start or current_hour < dnd_end:
            return False, "Do Not Disturb hours"
    else:
        if dnd_start <= current_hour < dnd_end:
            return False, "Do Not Disturb hours"
    
    # Check cooldown (last auto-message to this customer)
    cooldown_hours = settings.get("cooldown_hours", 24)
    cutoff = (now - timedelta(hours=cooldown_hours)).isoformat()
    recent_auto = await db.auto_messages_sent.find_one({
        "customer_id": customer_id,
        "sent_at": {"$gte": cutoff}
    })
    if recent_auto:
        return False, f"Cooldown period ({cooldown_hours}h)"
    
    # Check max messages per topic
    if topic_id:
        max_per_topic = settings.get("max_messages_per_topic", 3)
        topic_count = await db.auto_messages_sent.count_documents({
            "topic_id": topic_id,
            "customer_id": customer_id
        })
        if topic_count >= max_per_topic:
            return False, f"Max messages reached for topic ({max_per_topic})"
    
    return True, "OK"

async def send_auto_message(
    customer_id: str,
    conversation_id: str,
    trigger_type: str,
    template_vars: dict = None,
    topic_id: str = None
) -> dict:
    """Send an auto-message based on trigger type"""
    
    # Check if we can send
    can_send, reason = await can_send_auto_message(customer_id, topic_id)
    if not can_send:
        logger.info(f"Auto-message blocked: {reason} - Customer: {customer_id}")
        return {"sent": False, "reason": reason}
    
    # Get settings and template
    settings = await get_auto_message_settings()
    templates = settings.get("templates", DEFAULT_TEMPLATES)
    template = templates.get(trigger_type, "")
    
    if not template:
        return {"sent": False, "reason": "No template for trigger type"}
    
    # Format message with variables
    message = template
    if template_vars:
        for key, value in template_vars.items():
            message = message.replace("{" + key + "}", str(value))
    
    # Get customer phone
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer or not customer.get("phone"):
        return {"sent": False, "reason": "Customer phone not found"}
    
    phone = customer["phone"].replace(" ", "").replace("-", "")
    
    # Send via WhatsApp
    sent = await send_whatsapp_message(phone, message)
    
    if sent:
        now = datetime.now(timezone.utc).isoformat()
        
        # Log the auto-message
        await db.auto_messages_sent.insert_one({
            "id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "conversation_id": conversation_id,
            "topic_id": topic_id,
            "trigger_type": trigger_type,
            "message": message,
            "sent_at": now
        })
        
        # Also save as a regular message
        msg_id = str(uuid.uuid4())
        await db.messages.insert_one({
            "id": msg_id,
            "conversation_id": conversation_id,
            "content": message,
            "sender_type": "system",
            "message_type": "auto",
            "trigger_type": trigger_type,
            "attachments": [],
            "created_at": now
        })
        
        # Update conversation
        await db.conversations.update_one(
            {"id": conversation_id},
            {"$set": {"last_message": message, "last_message_at": now}}
        )
        
        logger.info(f"Auto-message sent: {trigger_type} - Customer: {customer_id}")
        return {"sent": True, "message_id": msg_id, "message": message}
    
    return {"sent": False, "reason": "WhatsApp send failed"}

async def schedule_follow_up(
    customer_id: str,
    conversation_id: str,
    topic_id: str,
    trigger_type: str,
    delay_hours: int,
    template_vars: dict = None
):
    """Schedule a follow-up message for later"""
    settings = await get_auto_message_settings()
    templates = settings.get("templates", DEFAULT_TEMPLATES)
    template = templates.get(trigger_type, "")
    
    message = template
    if template_vars:
        for key, value in template_vars.items():
            message = message.replace("{" + key + "}", str(value))
    
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        return None
    
    now = datetime.now(timezone.utc)
    scheduled_for = (now + timedelta(hours=delay_hours)).isoformat()
    
    scheduled_id = str(uuid.uuid4())
    await db.scheduled_messages.insert_one({
        "id": scheduled_id,
        "customer_id": customer_id,
        "customer_phone": customer.get("phone", ""),
        "conversation_id": conversation_id,
        "topic_id": topic_id,
        "trigger_type": trigger_type,
        "message": message,
        "scheduled_for": scheduled_for,
        "status": "pending",
        "created_at": now.isoformat()
    })
    
    logger.info(f"Follow-up scheduled: {trigger_type} - Customer: {customer_id} - In {delay_hours}h")
    return scheduled_id

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

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.post("/auth/reset-admin")
async def reset_admin_password():
    """Emergency endpoint to reset admin password - REMOVE IN PRODUCTION"""
    try:
        hashed = hash_password("admin123")
        # First delete any existing user to avoid conflicts
        await db.users.delete_many({"email": "ck@motta.in"})
        # Create fresh user
        user_id = str(uuid.uuid4())
        await db.users.insert_one({
            "id": user_id,
            "email": "ck@motta.in",
            "password": hashed,
            "name": "Charu",
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return {"message": "Admin user recreated with password admin123", "email": "ck@motta.in", "user_id": user_id}
    except Exception as e:
        return {"error": str(e)}

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

# ============== KB SCRAPE & IMPORT ==============

class WebScrapeRequest(BaseModel):
    url: str
    title: Optional[str] = None
    category: str = "general"

@api_router.post("/kb/scrape-url")
async def scrape_website_to_kb(data: WebScrapeRequest, user: dict = Depends(get_current_user)):
    """Scrape content from a website URL and add to Knowledge Base"""
    from bs4 import BeautifulSoup
    
    try:
        # Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(data.url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up multiple newlines
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Limit content length (keep first 10000 chars)
        if len(text) > 10000:
            text = text[:10000] + "\n\n[Content truncated...]"
        
        # Get title from page if not provided
        title = data.title or soup.title.string if soup.title else data.url
        
        # Create KB article
        article_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        article = {
            "id": article_id,
            "title": title[:200],
            "category": data.category,
            "content": text,
            "tags": ["scraped", "web"],
            "is_active": True,
            "source_url": data.url,
            "created_at": now,
            "updated_at": now
        }
        
        await db.knowledge_base.insert_one(article)
        
        return {
            "success": True,
            "article_id": article_id,
            "title": title[:200],
            "content_length": len(text),
            "message": f"Successfully scraped and added to KB"
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@api_router.post("/kb/upload-excel")
async def upload_excel_to_kb(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload Excel/CSV file to add multiple KB articles or products
    
    Supports multiple formats:
    1. KB Articles: title, content, category, tags
    2. Products: name, price, category, description
    3. Apple Price List: Part Number, Description, ALP Inc VAT
    """
    import pandas as pd
    import io
    import zipfile
    import re
    
    filename = file.filename.lower()
    if not filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) or CSV (.csv) files are allowed")
    
    try:
        contents = await file.read()
        
        if not contents or len(contents) < 10:
            raise HTTPException(status_code=400, detail="File is empty or too small")
        
        df = None
        
        # Try to read the file with different methods
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            # Method 1: Try standard pandas
            try:
                df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
                if df.empty or len(df.columns) == 0:
                    df = None
            except Exception as e1:
                logger.info(f"Standard read failed: {e1}")
                df = None
            
            # Method 2: For strict conformance XLSX (like Apple price lists)
            if df is None or df.empty:
                try:
                    df = parse_strict_xlsx(io.BytesIO(contents))
                    logger.info(f"Strict XLSX parser succeeded: {len(df) if df is not None else 0} rows")
                except Exception as e2:
                    logger.error(f"Strict XLSX parser failed: {e2}")
                    raise HTTPException(status_code=400, detail=f"Cannot read file. Please save it as CSV and try again.")
        
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="File has no data rows")
        
        # Convert column names to lowercase for easier matching
        df.columns = [str(col).lower().strip() for col in df.columns]
        original_cols = list(df.columns)
        
        logger.info(f"Excel upload - Columns found: {original_cols[:10]}, Rows: {len(df)}")
        
        now = datetime.now(timezone.utc).isoformat()
        added_count = 0
        
        # DETECT FORMAT: Apple Price List (Part Number, Description, ALP Inc VAT)
        if 'part number' in df.columns and 'description' in df.columns:
            logger.info("Detected Apple Price List format")
        
        # Check if this is a KB upload or Product upload
        if 'title' in df.columns and 'content' in df.columns:
            # KB Articles upload
            for _, row in df.iterrows():
                title = str(row.get('title', '')).strip() if pd.notna(row.get('title')) else ''
                content = str(row.get('content', '')).strip() if pd.notna(row.get('content')) else ''
                
                if not title or not content:
                    continue
                
                article = {
                    "id": str(uuid.uuid4()),
                    "title": title[:200],
                    "category": str(row.get('category', 'general')).strip().lower() if pd.notna(row.get('category')) else 'general',
                    "content": content,
                    "tags": [t.strip() for t in str(row.get('tags', '')).split(',') if t.strip()] if pd.notna(row.get('tags')) else [],
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now
                }
                await db.knowledge_base.insert_one(article)
                added_count += 1
            
            return {
                "success": True,
                "type": "knowledge_base",
                "added": added_count,
                "message": f"Added {added_count} KB articles"
            }
        
        # Products upload - handle Apple format and standard format
        elif ('part number' in df.columns and 'description' in df.columns) or ('name' in df.columns):
            # Map Apple columns if present
            name_col = 'description' if 'description' in df.columns else 'name'
            sku_col = 'part number' if 'part number' in df.columns else 'sku'
            
            # Find price column
            price_col = None
            for col in ['alp inc vat', 'alp', 'price', 'base_price', 'mrp', 'cost']:
                if col in df.columns:
                    price_col = col
                    break
            
            # Find category column
            cat_col = None
            for col in ['solutions & offerings', 'solutions &amp; offerings', 'category']:
                if col in df.columns:
                    cat_col = col
                    break
            
            for _, row in df.iterrows():
                name = str(row.get(name_col, '')).strip() if pd.notna(row.get(name_col)) else ''
                if not name or name.lower() == 'nan' or len(name) < 3:
                    continue
                
                # Get price
                price = 0
                if price_col and pd.notna(row.get(price_col)):
                    try:
                        price_val = str(row.get(price_col)).replace(',', '').replace('Rs.', '').replace('$', '').strip()
                        price = float(price_val) if price_val and price_val != 'nan' else 0
                    except:
                        price = 0
                
                # Get category
                category = 'general'
                if cat_col and pd.notna(row.get(cat_col)):
                    cat_val = str(row.get(cat_col)).strip()
                    if cat_val and cat_val.lower() != 'nan':
                        category = cat_val
                
                # Get SKU
                sku = str(uuid.uuid4())[:8]
                if sku_col and pd.notna(row.get(sku_col)):
                    sku_val = str(row.get(sku_col)).strip()
                    if sku_val and sku_val.lower() != 'nan':
                        sku = sku_val
                
                product = {
                    "id": str(uuid.uuid4()),
                    "name": name[:200],
                    "description": "",
                    "category": category,
                    "sku": sku,
                    "base_price": price,
                    "tax_rate": 18,
                    "final_price": price * 1.18 if price > 0 else 0,
                    "stock": 0,
                    "images": [],
                    "specifications": {},
                    "is_active": True,
                    "created_at": now
                }
                await db.products.insert_one(product)
                added_count += 1
            
            return {
                "success": True,
                "type": "products",
                "added": added_count,
                "message": f"Added {added_count} products"
            }
        
        else:
            available_cols = ', '.join(original_cols[:10])
            raise HTTPException(
                status_code=400, 
                detail=f"Excel must have columns: [title, content] for KB or [name/description, price] for products. Found: {available_cols}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process Excel: {str(e)}")

def parse_strict_xlsx(file_bytes):
    """Parse strict conformance XLSX files that openpyxl cannot handle (like Apple price lists)"""
    import zipfile
    import re
    import pandas as pd
    import io
    
    with zipfile.ZipFile(file_bytes, 'r') as z:
        # Read shared strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            content = z.read('xl/sharedStrings.xml').decode('utf-8')
            # Extract all <t> tags content
            strings = re.findall(r'<t[^>]*>([^<]*)</t>', content)
            shared_strings = [s.replace('&amp;', '&') for s in strings]
        
        if not shared_strings:
            return None
        
        # Find header row indices
        headers = ['Marketing Flag', 'NPI', 'Reprice Indicator', 'Part Number', 'UPC/EAN', 
                   'Description', 'SAP Part Description', 'ALP Inc VAT', 'Solutions & Offerings']
        header_lower = [h.lower() for h in headers]
        
        # Find where headers are in shared strings
        header_indices = {}
        for i, s in enumerate(shared_strings):
            s_clean = s.replace('&amp;', '&').lower()
            if s_clean in header_lower:
                header_indices[s_clean] = i
        
        # Read the actual sheet data
        if 'xl/worksheets/sheet1.xml' not in z.namelist():
            return None
        
        sheet_content = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
        
        # Parse rows - find data rows (after headers)
        rows_data = []
        row_pattern = re.compile(r'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>', re.DOTALL)
        cell_pattern = re.compile(r'<c[^>]*r="([A-Z]+)\d+"[^>]*(?:t="([^"]*)")?[^>]*>(?:<v>([^<]*)</v>)?', re.DOTALL)
        
        for row_match in row_pattern.finditer(sheet_content):
            row_num = int(row_match.group(1))
            row_content = row_match.group(2)
            
            # Skip first 10 rows (metadata)
            if row_num <= 10:
                continue
            
            cells = {}
            for cell_match in cell_pattern.finditer(row_content):
                col_letter = cell_match.group(1)
                cell_type = cell_match.group(2)
                cell_value = cell_match.group(3)
                
                if cell_value:
                    if cell_type == 's' and cell_value.isdigit():
                        # Shared string reference
                        idx = int(cell_value)
                        if idx < len(shared_strings):
                            cells[col_letter] = shared_strings[idx]
                    else:
                        cells[col_letter] = cell_value
            
            if cells:
                rows_data.append(cells)
        
        # Convert to DataFrame with proper column mapping
        # A=Marketing Flag, B=NPI, C=Reprice, D=Part Number, E=UPC, F=Description, G=SAP, H=ALP, I=Solutions
        col_mapping = {'A': 'marketing flag', 'B': 'npi', 'C': 'reprice indicator', 
                      'D': 'part number', 'E': 'upc/ean', 'F': 'description',
                      'G': 'sap part description', 'H': 'alp inc vat', 'I': 'solutions & offerings'}
        
        df_data = []
        for row in rows_data:
            mapped_row = {}
            for col, header in col_mapping.items():
                mapped_row[header] = row.get(col, '')
            df_data.append(mapped_row)
        
        if df_data:
            return pd.DataFrame(df_data)
        
        return None

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

# ============== SLA TIMER & REMINDERS ==============

@api_router.post("/escalations/check-sla")
async def check_sla_and_send_reminders(user: dict = Depends(get_current_user)):
    """Check pending escalations and send reminders for those past SLA deadline.
    This endpoint can be called periodically (e.g., every 5-10 mins) or on-demand.
    
    Sends reminders to owner via WhatsApp + updates dashboard status.
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    
    # Find all pending escalations
    pending = await db.escalations.find(
        {"status": "pending_owner_reply"},
        {"_id": 0}
    ).to_list(100)
    
    # Get owner phone
    settings = await db.settings.find_one({"type": "global"}, {"_id": 0})
    owner_phone = settings.get("owner_phone", "") if settings else ""
    
    reminders_sent = []
    overdue_count = 0
    
    for esc in pending:
        sla_deadline = esc.get("sla_deadline")
        if not sla_deadline:
            continue
        
        # Check if past SLA deadline
        try:
            deadline_dt = datetime.fromisoformat(sla_deadline.replace('Z', '+00:00'))
            if now > deadline_dt:
                overdue_count += 1
                reminders_count = esc.get("sla_reminders_sent", 0)
                
                # Send reminder if less than 3 reminders sent and at least 10 mins since last
                if reminders_count < 3:
                    customer_name = esc.get("customer_name", "Unknown")
                    customer_message = esc.get("customer_message", "")[:100]
                    time_overdue = int((now - deadline_dt).total_seconds() / 60)
                    
                    reminder_msg = f"""[REMINDER] *SLA REMINDER #{reminders_count + 1}*

Customer *{customer_name}* is waiting!

Q: Their question:
"{customer_message}"

Time Overdue by: {time_overdue} minutes

Just reply with your answer - I will format and send it."""

                    # Send WhatsApp reminder to owner
                    if owner_phone:
                        await send_whatsapp_message(owner_phone, reminder_msg)
                    
                    # Update escalation
                    await db.escalations.update_one(
                        {"id": esc["id"]},
                        {"$set": {
                            "sla_reminders_sent": reminders_count + 1,
                            "last_reminder_at": now_iso
                        }}
                    )
                    
                    # Update conversation status
                    if esc.get("customer_id"):
                        await db.conversations.update_one(
                            {"customer_id": esc["customer_id"]},
                            {"$set": {
                                "sla_reminders_sent": reminders_count + 1,
                                "status": "waiting_for_owner"
                            }}
                        )
                    
                    reminders_sent.append({
                        "escalation_id": esc["id"],
                        "customer_name": customer_name,
                        "time_overdue_mins": time_overdue
                    })
                    
                    logger.info(f"SLA reminder sent for {customer_name} - Overdue by {time_overdue} mins")
        except Exception as e:
            logger.error(f"Error processing SLA for escalation {esc.get('id')}: {e}")
            continue
    
    return {
        "checked_at": now_iso,
        "total_pending": len(pending),
        "overdue_count": overdue_count,
        "reminders_sent": reminders_sent
    }

@api_router.get("/escalations/pending-sla")
async def get_pending_sla_escalations(user: dict = Depends(get_current_user)):
    """Get all pending escalations with their SLA status for dashboard display"""
    now = datetime.now(timezone.utc)
    
    pending = await db.escalations.find(
        {"status": "pending_owner_reply"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    result = []
    for esc in pending:
        sla_deadline = esc.get("sla_deadline")
        is_overdue = False
        minutes_remaining = None
        minutes_overdue = None
        
        if sla_deadline:
            try:
                deadline_dt = datetime.fromisoformat(sla_deadline.replace('Z', '+00:00'))
                if now > deadline_dt:
                    is_overdue = True
                    minutes_overdue = int((now - deadline_dt).total_seconds() / 60)
                else:
                    minutes_remaining = int((deadline_dt - now).total_seconds() / 60)
            except:
                pass
        
        result.append({
            "id": esc.get("id"),
            "customer_id": esc.get("customer_id"),
            "customer_name": esc.get("customer_name"),
            "customer_phone": esc.get("customer_phone"),
            "customer_message": esc.get("customer_message"),
            "reason": esc.get("reason"),
            "created_at": esc.get("created_at"),
            "sla_deadline": sla_deadline,
            "sla_reminders_sent": esc.get("sla_reminders_sent", 0),
            "is_overdue": is_overdue,
            "minutes_remaining": minutes_remaining,
            "minutes_overdue": minutes_overdue
        })
    
    return result

# ============== UNANSWERED QUESTIONS ROUTES ==============

@api_router.get("/unanswered-questions")
async def get_unanswered_questions(status: Optional[str] = None, relevance: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get all unanswered questions (pending escalations) for the dashboard.
    
    Filters:
    - status: pending_owner_reply, resolved, marked_irrelevant
    - relevance: relevant, irrelevant
    """
    now = datetime.now(timezone.utc)
    
    # Build query - default to pending questions
    query = {}
    if status and status != "all":
        query["status"] = status
    elif not status:
        query["status"] = "pending_owner_reply"  # Default: only pending
    # If status == "all", do not add status filter
    
    if relevance and relevance != "all":
        query["relevance"] = relevance
    
    escalations = await db.escalations.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    result = []
    for esc in escalations:
        # Calculate if overdue
        sla_deadline = esc.get("sla_deadline")
        is_overdue = False
        if sla_deadline:
            try:
                deadline_dt = datetime.fromisoformat(sla_deadline.replace('Z', '+00:00'))
                is_overdue = now > deadline_dt
            except:
                pass
        
        # Get linked KB article info if any
        linked_kb_id = esc.get("kb_article_id")
        linked_kb_title = None
        if linked_kb_id:
            kb_article = await db.kb_articles.find_one({"id": linked_kb_id}, {"_id": 0, "title": 1})
            if kb_article:
                linked_kb_title = kb_article.get("title")
        
        result.append({
            "id": esc.get("id"),
            "escalation_code": esc.get("escalation_code", "ESC??"),
            "customer_name": esc.get("customer_name", "Unknown"),
            "customer_phone": esc.get("customer_phone", ""),
            "question": esc.get("customer_message", ""),
            "reason": esc.get("reason", "AI could not answer"),
            "status": esc.get("status", "pending_owner_reply"),
            "relevance": esc.get("relevance", "relevant"),
            "conversation_count": 1,  # Could be enhanced to count related messages
            "created_at": esc.get("created_at"),
            "sla_deadline": sla_deadline,
            "is_overdue": is_overdue,
            "linked_kb_id": linked_kb_id,
            "linked_kb_title": linked_kb_title
        })
    
    return result

@api_router.put("/unanswered-questions/{question_id}/relevance")
async def mark_question_relevance(question_id: str, relevance: str, user: dict = Depends(get_current_user)):
    """Mark a question as relevant or irrelevant.
    
    Irrelevant questions will not trigger future escalations for similar queries.
    """
    if relevance not in ["relevant", "irrelevant"]:
        raise HTTPException(status_code=400, detail="Invalid relevance value. Use 'relevant' or 'irrelevant'")
    
    update_data = {
        "relevance": relevance,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user["name"]
    }
    
    if relevance == "irrelevant":
        update_data["status"] = "marked_irrelevant"
    
    result = await db.escalations.update_one(
        {"id": question_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return {"message": f"Question marked as {relevance}"}

@api_router.post("/unanswered-questions/{question_id}/add-kb-article")
async def add_kb_article_for_question(question_id: str, data: KbArticleCreateRequest, user: dict = Depends(get_current_user)):
    """Create a new KB article to answer this question.
    
    This will:
    1. Create a new KB article with the provided content
    2. Link it to this question
    3. Mark the question as resolved
    
    Future similar questions will be answered using this KB article.
    """
    # Get the question
    question = await db.escalations.find_one({"id": question_id}, {"_id": 0})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Create KB article
    article_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    article = {
        "id": article_id,
        "title": data.title,
        "content": data.content,
        "category": data.category,
        "tags": data.tags + [question.get("customer_message", "")[:50]],  # Add question text as tag
        "source": "unanswered_question",
        "source_question_id": question_id,
        "created_at": now,
        "created_by": user["name"],
        "updated_at": now
    }
    
    await db.kb_articles.insert_one(article)
    
    # Link KB article to the question and mark as resolved
    await db.escalations.update_one(
        {"id": question_id},
        {"$set": {
            "kb_article_id": article_id,
            "status": "resolved",
            "resolved_at": now,
            "resolved_by": user["name"],
            "resolution_type": "kb_article_created"
        }}
    )
    
    # Update conversation status if linked
    if question.get("customer_id"):
        await db.conversations.update_one(
            {"customer_id": question["customer_id"]},
            {"$set": {
                "status": "active",
                "escalated_at": None,
                "escalation_reason": None
            }}
        )
    
    logger.info(f"KB article created for unanswered question: {article_id}")
    return {
        "message": "KB article created and linked",
        "article_id": article_id,
        "question_id": question_id
    }

@api_router.post("/unanswered-questions/{question_id}/link-kb-article/{kb_article_id}")
async def link_existing_kb_article(question_id: str, kb_article_id: str, user: dict = Depends(get_current_user)):
    """Link an existing KB article to this question.
    
    This marks the question as resolved and ensures future similar questions
    are answered using the linked KB article.
    """
    # Verify the KB article exists
    kb_article = await db.kb_articles.find_one({"id": kb_article_id}, {"_id": 0})
    if not kb_article:
        raise HTTPException(status_code=404, detail="KB article not found")
    
    # Get the question
    question = await db.escalations.find_one({"id": question_id}, {"_id": 0})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Link and resolve
    await db.escalations.update_one(
        {"id": question_id},
        {"$set": {
            "kb_article_id": kb_article_id,
            "status": "resolved",
            "resolved_at": now,
            "resolved_by": user["name"],
            "resolution_type": "kb_article_linked"
        }}
    )
    
    # Update conversation status if linked
    if question.get("customer_id"):
        await db.conversations.update_one(
            {"customer_id": question["customer_id"]},
            {"$set": {
                "status": "active",
                "escalated_at": None,
                "escalation_reason": None
            }}
        )
    
    logger.info(f"KB article {kb_article_id} linked to question {question_id}")
    return {
        "message": "KB article linked to question",
        "article_id": kb_article_id,
        "article_title": kb_article.get("title"),
        "question_id": question_id
    }

@api_router.post("/unanswered-questions/{question_id}/link-excel-data")
async def link_excel_data_to_question(question_id: str, search_query: str, user: dict = Depends(get_current_user)):
    """Search uploaded Excel/KB data for an answer and link it to this question.
    
    This searches through:
    1. Uploaded Excel files (price lists, etc.)
    2. Existing KB articles
    3. Product catalog
    
    And suggests or automatically links the best match.
    """
    # Get the question
    question = await db.escalations.find_one({"id": question_id}, {"_id": 0})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    customer_message = question.get("customer_message", "")
    search_term = search_query or customer_message
    
    # Search in KB articles
    kb_results = await db.kb_articles.find(
        {"$or": [
            {"title": {"$regex": search_term, "$options": "i"}},
            {"content": {"$regex": search_term, "$options": "i"}},
            {"tags": {"$regex": search_term, "$options": "i"}}
        ]},
        {"_id": 0}
    ).limit(5).to_list(5)
    
    # Search in products
    product_results = await db.products.find(
        {"$or": [
            {"name": {"$regex": search_term, "$options": "i"}},
            {"description": {"$regex": search_term, "$options": "i"}},
            {"sku": {"$regex": search_term, "$options": "i"}}
        ]},
        {"_id": 0}
    ).limit(5).to_list(5)
    
    # Search in Excel uploads (stored in kb_uploads collection)
    excel_results = await db.kb_uploads.find(
        {"$or": [
            {"data.name": {"$regex": search_term, "$options": "i"}},
            {"data.description": {"$regex": search_term, "$options": "i"}},
            {"data.model": {"$regex": search_term, "$options": "i"}}
        ]},
        {"_id": 0}
    ).limit(5).to_list(5)
    
    return {
        "question_id": question_id,
        "search_query": search_term,
        "kb_articles": kb_results,
        "products": product_results,
        "excel_data": excel_results,
        "total_results": len(kb_results) + len(product_results) + len(excel_results)
    }

# ============== EXCLUDED NUMBERS ROUTES (Silent Monitoring) ==============

@api_router.get("/excluded-numbers", response_model=List[ExcludedNumberResponse])
async def get_excluded_numbers(tag: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get all excluded numbers"""
    query = {}
    if tag:
        query["tag"] = tag
    numbers = await db.excluded_numbers.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [ExcludedNumberResponse(**n) for n in numbers]

@api_router.post("/excluded-numbers", response_model=ExcludedNumberResponse)
async def add_excluded_number(data: ExcludedNumberCreate, user: dict = Depends(get_current_user)):
    """Add a number to exclusion list (silent monitoring)"""
    # Check if already excluded
    existing = await is_number_excluded(data.phone)
    if existing:
        raise HTTPException(status_code=400, detail="Number already excluded")
    
    number_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    doc = {
        "id": number_id,
        "phone": data.phone,
        "tag": data.tag,
        "reason": data.reason,
        "is_temporary": data.is_temporary,
        "created_at": now,
        "created_by": user["name"]
    }
    await db.excluded_numbers.insert_one(doc)
    logger.info(f"Number excluded: {data.phone} - Tag: {data.tag} - By: {user['name']}")
    return ExcludedNumberResponse(**doc)

@api_router.delete("/excluded-numbers/{number_id}")
async def remove_excluded_number(number_id: str, user: dict = Depends(get_current_user)):
    """Remove a number from exclusion list"""
    result = await db.excluded_numbers.delete_one({"id": number_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Number not found")
    logger.info(f"Number exclusion removed: {number_id}")
    return {"message": "Number removed from exclusion list"}

@api_router.get("/excluded-numbers/check/{phone}")
async def check_excluded_number(phone: str, user: dict = Depends(get_current_user)):
    """Check if a specific number is excluded"""
    is_excluded = await is_number_excluded(phone)
    info = await get_excluded_number_info(phone) if is_excluded else None
    return {
        "phone": phone,
        "is_excluded": is_excluded,
        "info": info
    }

# ============== LEAD INJECTION ROUTES (Owner-Initiated Leads) ==============

@api_router.get("/leads", response_model=List[LeadInjectionResponse])
async def get_leads(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get all injected leads"""
    query = {}
    if status:
        query["status"] = status
    leads = await db.lead_injections.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [LeadInjectionResponse(**lead) for lead in leads]

@api_router.post("/leads/inject", response_model=LeadInjectionResponse)
async def inject_lead(data: LeadInjectionCreate, user: dict = Depends(get_current_user)):
    """
    Owner-initiated lead injection.
    Creates customer, conversation, topic and sends first outbound message.
    """
    now = datetime.now(timezone.utc).isoformat()
    
    # Normalize phone
    phone = data.phone.replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        if len(phone) == 10:
            phone = "+91" + phone
        elif phone.startswith("91") and len(phone) == 12:
            phone = "+" + phone
    phone_formatted = f"{phone[:3]} {phone[3:8]} {phone[8:]}" if len(phone) >= 13 else phone
    
    # Step 1: Create or find customer
    existing_customer = await db.customers.find_one({"phone": {"$regex": phone[-10:]}}, {"_id": 0})
    
    if existing_customer:
        customer = existing_customer
        customer_id = customer["id"]
        logger.info(f"Lead injection: Found existing customer {customer['name']}")
    else:
        customer_id = str(uuid.uuid4())
        customer = {
            "id": customer_id,
            "name": data.customer_name,
            "phone": phone_formatted,
            "customer_type": "individual",
            "addresses": [],
            "preferences": {"communication": "whatsapp"},
            "purchase_history": [],
            "devices": [],
            "tags": ["lead", "owner-injected"],
            "notes": f"Lead injected by {user['name']}: {data.product_interest}",
            "total_spent": 0.0,
            "last_interaction": now,
            "created_at": now
        }
        await db.customers.insert_one(customer)
        logger.info(f"Lead injection: Created new customer {data.customer_name}")
    
    # Step 2: Create conversation
    conv_id = str(uuid.uuid4())
    conv = {
        "id": conv_id,
        "customer_id": customer_id,
        "customer_name": customer["name"],
        "customer_phone": customer["phone"],
        "channel": "whatsapp",
        "status": "active",
        "last_message": None,
        "last_message_at": now,
        "unread_count": 0,
        "source": "owner-injected",
        "created_at": now
    }
    await db.conversations.insert_one(conv)
    
    # Step 3: Create topic
    topic_id = str(uuid.uuid4())
    topic = {
        "id": topic_id,
        "conversation_id": conv_id,
        "customer_id": customer_id,
        "topic_type": "product_inquiry",
        "title": f"Interest in {data.product_interest}",
        "status": "open",
        "device_info": None,
        "metadata": {"product": data.product_interest, "source": "owner-injected"},
        "created_at": now,
        "updated_at": now
    }
    await db.topics.insert_one(topic)
    
    # Step 4: Generate and send outbound message
    # Find product details
    product = await db.products.find_one(
        {"name": {"$regex": data.product_interest, "$options": "i"}, "is_active": True},
        {"_id": 0}
    )
    
    if product:
        outbound_msg = f"Hi {customer['name'].split()[0]}! This is from the store. I understand you are interested in the {product['name']}. It is available at Rs.{product['base_price']:,.0f}. Would you like me to share more details about specifications and availability?"
    else:
        outbound_msg = f"Hi {customer['name'].split()[0]}! This is from the store. I understand you are interested in {data.product_interest}. I'd be happy to help you with the details. What specifically would you like to know?"
    
    # Send via WhatsApp
    message_sent = await send_whatsapp_message(phone, outbound_msg)
    
    if message_sent:
        # Store the outbound message
        msg_id = str(uuid.uuid4())
        msg_doc = {
            "id": msg_id,
            "conversation_id": conv_id,
            "topic_id": topic_id,
            "content": outbound_msg,
            "sender_type": "ai",
            "message_type": "text",
            "attachments": [],
            "created_at": now
        }
        await db.messages.insert_one(msg_doc)
        
        # Update conversation
        await db.conversations.update_one(
            {"id": conv_id},
            {"$set": {"last_message": outbound_msg, "last_message_at": now}}
        )
        logger.info(f"Lead injection: Outbound message sent to {phone}")
    else:
        logger.warning(f"Lead injection: Failed to send outbound message to {phone}")
    
    # Step 5: Create lead injection record
    lead_id = str(uuid.uuid4())
    lead = {
        "id": lead_id,
        "customer_id": customer_id,
        "customer_name": customer["name"],
        "phone": phone,
        "product_interest": data.product_interest,
        "conversation_id": conv_id,
        "topic_id": topic_id,
        "outbound_message_sent": message_sent,
        "status": "in_progress" if message_sent else "pending",
        "notes": data.notes,
        "created_at": now,
        "created_by": user["name"]
    }
    await db.lead_injections.insert_one(lead)
    
    return LeadInjectionResponse(**lead)

@api_router.put("/leads/{lead_id}/status")
async def update_lead_status(lead_id: str, status: str, user: dict = Depends(get_current_user)):
    """Update lead status"""
    if status not in ["pending", "in_progress", "completed", "escalated"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    result = await db.lead_injections.update_one({"id": lead_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
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

# ============== CUSTOMER 360-degree VIEW ==============

@api_router.get("/customers/{customer_id}/360")
async def get_customer_360(customer_id: str, user: dict = Depends(get_current_user)):
    """Get comprehensive 360-degree view of a customer with all related data"""
    
    # Get customer base data
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get all conversations for this customer
    conversations = await db.conversations.find(
        {"customer_id": customer_id}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get all topics (active and resolved)
    topics = await db.topics.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Separate active vs resolved topics
    active_topics = [t for t in topics if t.get("status") in ["open", "in_progress"]]
    resolved_topics = [t for t in topics if t.get("status") in ["resolved", "closed"]]
    
    # Get all orders
    orders = await db.orders.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get all tickets
    tickets = await db.tickets.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Get escalations
    escalations = await db.escalations.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Get recent messages (last 20 across all conversations)
    conv_ids = [c["id"] for c in conversations]
    recent_messages = []
    if conv_ids:
        recent_messages = await db.messages.find(
            {"conversation_id": {"$in": conv_ids}},
            {"_id": 0}
        ).sort("created_at", -1).limit(20).to_list(20)
    
    # Get auto-messages sent to this customer
    auto_messages = await db.auto_messages_sent.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("sent_at", -1).limit(10).to_list(10)
    
    # Get lead injection info if any
    lead_info = await db.lead_injections.find_one(
        {"customer_id": customer_id},
        {"_id": 0}
    )
    
    # Check if number is excluded
    is_excluded = await is_number_excluded(customer.get("phone", ""))
    exclusion_info = await get_excluded_number_info(customer.get("phone", "")) if is_excluded else None
    
    # Calculate statistics - use customer.total_spent as source of truth (includes historical data)
    total_orders = len(orders)
    total_spent = customer.get("total_spent", 0)  # Use stored total from customer record
    pending_orders = len([o for o in orders if o.get("status") in ["pending", "processing"]])
    completed_orders = len([o for o in orders if o.get("status") == "delivered"])
    
    # Build 360-degree response
    return {
        "customer": customer,
        "statistics": {
            "total_orders": total_orders,
            "total_spent": total_spent,
            "pending_orders": pending_orders,
            "completed_orders": completed_orders,
            "active_topics": len(active_topics),
            "resolved_topics": len(resolved_topics),
            "total_conversations": len(conversations),
            "open_tickets": len([t for t in tickets if t.get("status") in ["open", "in_progress"]]),
            "escalations": len(escalations)
        },
        "active_topics": active_topics[:10],
        "resolved_topics": resolved_topics[:10],
        "orders": orders[:10],
        "tickets": tickets[:10],
        "escalations": escalations[:5],
        "recent_messages": recent_messages,
        "auto_messages": auto_messages,
        "lead_info": lead_info,
        "is_excluded": is_excluded,
        "exclusion_info": exclusion_info,
        "conversations": conversations[:5]
    }

@api_router.put("/customers/{customer_id}/notes")
async def update_customer_notes(customer_id: str, notes: str, user: dict = Depends(get_current_user)):
    """Update customer internal notes (legacy single note)"""
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$set": {"notes": notes, "last_interaction": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Notes updated"}

@api_router.post("/customers/{customer_id}/notes")
async def add_customer_note(customer_id: str, content: str, user: dict = Depends(get_current_user)):
    """Add a new note to customer notes history"""
    note = {
        "id": str(uuid.uuid4()),
        "content": content,
        "created_by": user.get("name", "Admin"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.customers.update_one(
        {"id": customer_id},
        {
            "$push": {"notes_history": note},
            "$set": {"last_interaction": datetime.now(timezone.utc).isoformat()}
        }
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Note added", "note": note}

@api_router.delete("/customers/{customer_id}/notes/{note_id}")
async def delete_customer_note(customer_id: str, note_id: str, user: dict = Depends(get_current_user)):
    """Delete a note from customer notes history"""
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$pull": {"notes_history": {"id": note_id}}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Note deleted"}

@api_router.put("/customers/{customer_id}/details")
async def update_customer_details(customer_id: str, data: Dict[str, Any], user: dict = Depends(get_current_user)):
    """Update customer details (name, email, phone, company, type, payment preferences)"""
    allowed_fields = ["name", "email", "phone", "company_id", "customer_type", "payment_preferences"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data["last_interaction"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer details updated"}

@api_router.post("/customers/{customer_id}/addresses")
async def add_customer_address(customer_id: str, address: Dict[str, Any], user: dict = Depends(get_current_user)):
    """Add a new address to customer"""
    address["id"] = str(uuid.uuid4())
    address["created_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$push": {"addresses": address}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Address added", "address": address}

@api_router.put("/customers/{customer_id}/addresses/{address_id}")
async def update_customer_address(customer_id: str, address_id: str, address: Dict[str, Any], user: dict = Depends(get_current_user)):
    """Update a customer address"""
    result = await db.customers.update_one(
        {"id": customer_id, "addresses.id": address_id},
        {"$set": {"addresses.$": {**address, "id": address_id, "updated_at": datetime.now(timezone.utc).isoformat()}}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer or address not found")
    return {"message": "Address updated"}

@api_router.delete("/customers/{customer_id}/addresses/{address_id}")
async def delete_customer_address(customer_id: str, address_id: str, user: dict = Depends(get_current_user)):
    """Delete a customer address"""
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$pull": {"addresses": {"id": address_id}}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Address deleted"}

@api_router.post("/customers/{customer_id}/invoices")
async def upload_customer_invoice(customer_id: str, file: UploadFile, description: str = "", user: dict = Depends(get_current_user)):
    """Upload an invoice file for customer"""
    import base64
    
    # Read file content
    content = await file.read()
    
    # Store as base64 (for small files) or save to disk
    invoice = {
        "id": str(uuid.uuid4()),
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "description": description,
        "data": base64.b64encode(content).decode('utf-8'),  # Store as base64
        "uploaded_by": user.get("name", "Admin"),
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$push": {"invoices": invoice}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {"message": "Invoice uploaded", "invoice_id": invoice["id"], "filename": invoice["filename"]}

@api_router.get("/customers/{customer_id}/invoices/{invoice_id}")
async def get_customer_invoice(customer_id: str, invoice_id: str, user: dict = Depends(get_current_user)):
    """Get a specific invoice file"""
    import base64
    from fastapi.responses import Response
    
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0, "invoices": 1})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    invoices = customer.get("invoices", [])
    invoice = next((i for i in invoices if i.get("id") == invoice_id), None)
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    content = base64.b64decode(invoice["data"])
    return Response(
        content=content,
        media_type=invoice.get("content_type", "application/octet-stream"),
        headers={"Content-Disposition": f"attachment; filename={invoice['filename']}"}
    )

@api_router.delete("/customers/{customer_id}/invoices/{invoice_id}")
async def delete_customer_invoice(customer_id: str, invoice_id: str, user: dict = Depends(get_current_user)):
    """Delete an invoice"""
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$pull": {"invoices": {"id": invoice_id}}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Invoice deleted"}

@api_router.get("/customers/{customer_id}/ai-insights")
async def get_customer_ai_insights(customer_id: str, user: dict = Depends(get_current_user)):
    """Get AI-collected insights about customer"""
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0, "ai_insights": 1, "name": 1})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer.get("ai_insights", {})

@api_router.put("/customers/{customer_id}/ai-insights")
async def update_customer_ai_insights(customer_id: str, insights: Dict[str, Any], user: dict = Depends(get_current_user)):
    """Manually update AI insights (or called by AI)"""
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$set": {"ai_insights": insights}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "AI insights updated"}

@api_router.put("/customers/{customer_id}/tags")
async def update_customer_tags(customer_id: str, tags: List[str], user: dict = Depends(get_current_user)):
    """Update customer tags"""
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$set": {"tags": tags}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Tags updated"}

@api_router.post("/customers/{customer_id}/devices")
async def add_customer_device(customer_id: str, device: Dict[str, Any], user: dict = Depends(get_current_user)):
    """Add a device to customer device list"""
    result = await db.customers.update_one(
        {"id": customer_id},
        {"$push": {"devices": {**device, "added_at": datetime.now(timezone.utc).isoformat()}}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Device added"}

@api_router.delete("/customers/{customer_id}/devices/{device_index}")
async def remove_customer_device(customer_id: str, device_index: int, user: dict = Depends(get_current_user)):
    """Remove a device from customer device list by index"""
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    devices = customer.get("devices", [])
    if 0 <= device_index < len(devices):
        devices.pop(device_index)
        await db.customers.update_one({"id": customer_id}, {"$set": {"devices": devices}})
        return {"message": "Device removed"}
    else:
        raise HTTPException(status_code=400, detail="Invalid device index")

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
Name: {customer.get('name')} | Phone: {customer.get('phone')} | Spent: Rs.{customer.get('total_spent', 0)}
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
        
        # Check if KB could not answer (flag for research)
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

@api_router.post("/products/bulk-upload")
async def bulk_upload_products(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    """Upload products from Excel/CSV file
    Expected columns: name, sku, category, base_price, description (optional)
    """
    import pandas as pd
    import io
    
    try:
        contents = await file.read()
        
        # Determine file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="File must be .csv, .xlsx, or .xls")
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')
        
        # Validate required columns
        required = ['name', 'sku', 'category', 'base_price']
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(missing)}")
        
        now = datetime.now(timezone.utc).isoformat()
        products_to_insert = []
        updated_count = 0
        
        for _, row in df.iterrows():
            product_data = {
                "name": str(row['name']).strip(),
                "sku": str(row['sku']).strip(),
                "category": str(row['category']).strip(),
                "base_price": float(row['base_price']),
                "description": str(row.get('description', '')).strip() if pd.notna(row.get('description')) else "",
                "variants": [],
                "images": [],
                "specifications": {},
                "is_active": True,
                "updated_at": now
            }
            
            # Check if product exists (by SKU)
            existing = await db.products.find_one({"sku": product_data["sku"]})
            if existing:
                await db.products.update_one({"sku": product_data["sku"]}, {"$set": product_data})
                updated_count += 1
            else:
                product_data["id"] = str(uuid.uuid4())
                product_data["created_at"] = now
                products_to_insert.append(product_data)
        
        if products_to_insert:
            await db.products.insert_many(products_to_insert)
        
        return {
            "success": True,
            "inserted": len(products_to_insert),
            "updated": updated_count,
            "total": len(df)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

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
        "description": f"Order placed with {len(order.items)} items. Total: Rs.{total:.2f}",
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
    
    # AUTO-MESSAGE: Order confirmed + Ticket created
    conv = await db.conversations.find_one({"id": order.conversation_id}, {"_id": 0})
    if conv:
        # Send order confirmation
        await send_auto_message(
            customer_id=order.customer_id,
            conversation_id=order.conversation_id,
            trigger_type="order_confirmed",
            template_vars={"amount": f"{total:,.2f}"}
        )
        # Send ticket created notification
        await send_auto_message(
            customer_id=order.customer_id,
            conversation_id=order.conversation_id,
            trigger_type="ticket_created",
            template_vars={"ticket_id": ticket_doc["ticket_number"]}
        )
    
    return OrderResponse(**order_doc)

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, user: dict = Depends(get_current_user)):
    valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    await db.orders.update_one({"id": order_id}, {"$set": {"status": status}})
    
    # AUTO-MESSAGE: Order status updates
    if order.get("conversation_id"):
        if status == "delivered":
            await send_auto_message(
                customer_id=order["customer_id"],
                conversation_id=order["conversation_id"],
                trigger_type="order_completed"
            )
    
    return {"message": "Status updated"}

@api_router.put("/orders/{order_id}/payment")
async def update_order_payment(order_id: str, payment_status: str, user: dict = Depends(get_current_user)):
    """Update payment status and send auto-message"""
    valid_statuses = ["pending", "received", "failed", "refunded"]
    if payment_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid payment status")
    
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    await db.orders.update_one({"id": order_id}, {"$set": {"payment_status": payment_status}})
    
    # AUTO-MESSAGE: Payment received
    if payment_status == "received" and order.get("conversation_id"):
        await send_auto_message(
            customer_id=order["customer_id"],
            conversation_id=order["conversation_id"],
            trigger_type="payment_received"
        )
    
    return {"message": "Payment status updated"}

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
    
    ticket = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    old_status = ticket.get("status", "open")
    await db.tickets.update_one({"id": ticket_id}, {"$set": {"status": status}})
    
    # AUTO-MESSAGE: Ticket status updates
    # Find the customer conversation
    order = await db.orders.find_one({"ticket_id": ticket_id}, {"_id": 0})
    if order and order.get("conversation_id"):
        if status == "in_progress" and old_status != "in_progress":
            await send_auto_message(
                customer_id=ticket["customer_id"],
                conversation_id=order["conversation_id"],
                trigger_type="ticket_updated",
                template_vars={"ticket_id": ticket.get("ticket_number", ticket_id[:8])}
            )
        elif status in ["resolved", "closed"] and old_status not in ["resolved", "closed"]:
            await send_auto_message(
                customer_id=ticket["customer_id"],
                conversation_id=order["conversation_id"],
                trigger_type="ticket_resolved",
                template_vars={"ticket_id": ticket.get("ticket_number", ticket_id[:8])}
            )
    
    return {"message": "Status updated"}

# ============== WHATSAPP (REAL INTEGRATION) ==============

WA_SERVICE_URL = os.environ.get('WA_SERVICE_URL', 'http://localhost:3001')

class WhatsAppIncoming(BaseModel):
    phone: str
    message: str
    timestamp: Optional[int] = None
    messageId: Optional[str] = None
    hasMedia: bool = False
    isHistorical: bool = False  # True = read-only (before connection), False = eligible for AI reply

class WhatsAppConnected(BaseModel):
    phone: str
    connectionTimestamp: int

class WhatsAppSyncMessages(BaseModel):
    phone: str
    chatName: Optional[str] = None
    messages: List[Dict[str, Any]]

# Global: Store the WhatsApp connection timestamp
whatsapp_connection_timestamp = None

@api_router.get("/whatsapp/status")
async def get_whatsapp_status(user: dict = Depends(get_current_user)):
    """Get WhatsApp connection status from Node.js service"""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: requests.get(f"{WA_SERVICE_URL}/status", timeout=5)
        )
        data = response.json()
        return {
            "connected": data.get("connected", False),
            "phone_number": data.get("phone"),
            "qr_code": data.get("qrCode"),
            "status": data.get("connectionStatus", "waiting_for_scan"),
            "sync_progress": data.get("syncProgress", {}),
            "previewMode": data.get("previewMode", False),
            "library": data.get("library", "unknown"),
            "message": data.get("message")
        }
    except Exception as e:
        logger.error(f"WhatsApp status error: {e}")
        return {
            "connected": False,
            "phone_number": None,
            "qr_code": None,
            "status": "service_unavailable",
            "error": str(e),
            "previewMode": False
        }

@api_router.get("/whatsapp/qr")
async def get_whatsapp_qr(user: dict = Depends(get_current_user)):
    """Get QR code for WhatsApp login"""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: requests.get(f"{WA_SERVICE_URL}/qr", timeout=5)
        )
        return response.json()
    except Exception as e:
        return {"error": str(e), "qrCode": None}

@api_router.post("/whatsapp/disconnect")
async def disconnect_whatsapp(user: dict = Depends(get_current_user)):
    """Disconnect WhatsApp session"""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: requests.post(f"{WA_SERVICE_URL}/disconnect", timeout=10)
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@api_router.post("/whatsapp/reconnect")
async def reconnect_whatsapp(user: dict = Depends(get_current_user)):
    """Reconnect WhatsApp (new QR)"""
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: requests.post(f"{WA_SERVICE_URL}/reconnect", timeout=10)
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@api_router.post("/whatsapp/connected")
async def handle_whatsapp_connected(data: WhatsAppConnected):
    """Handle WhatsApp connection notification - stores connection timestamp"""
    global whatsapp_connection_timestamp
    whatsapp_connection_timestamp = data.connectionTimestamp
    logger.info(f"WhatsApp connected. Phone: {data.phone}, Timestamp: {data.connectionTimestamp}")
    
    # Store in settings for persistence
    await db.settings.update_one(
        {"type": "whatsapp"},
        {"$set": {
            "type": "whatsapp",
            "connected_phone": data.phone,
            "connection_timestamp": data.connectionTimestamp,
            "connected_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"success": True, "message": f"Connection timestamp recorded: {data.connectionTimestamp}"}

@api_router.post("/whatsapp/send")
async def api_send_whatsapp_message(phone: str, message: str, user: dict = Depends(get_current_user)):
    """Send message via WhatsApp (API route)"""
    try:
        logger.info(f"Sending WhatsApp message to: {phone}")
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: requests.post(f"{WA_SERVICE_URL}/send", json={"phone": phone, "message": message}, timeout=30)
        )
        result = response.json()
        logger.info(f"WhatsApp send result: {result}")
        return result
    except Exception as e:
        logger.error(f"WhatsApp send error: {str(e)}")
        return {"error": str(e)}

# Helper: Normalize phone number to consistent format
def normalize_phone(phone: str) -> tuple:
    """Normalize phone number and return (clean_digits, formatted_display)"""
    # Remove all non-digits
    clean = ''.join(c for c in phone if c.isdigit())
    
    # If too long, take last 10 digits and prefix with 91
    if len(clean) > 12:
        clean = '91' + clean[-10:]
    # If 10 digits, assume India
    elif len(clean) == 10:
        clean = '91' + clean
    # If does not start with 91, prefix it
    elif not clean.startswith('91') and len(clean) >= 10:
        clean = '91' + clean[-10:]
    
    # Format for display: +91 98765 43210
    if len(clean) >= 12:
        formatted = f"+{clean[:2]} {clean[2:7]} {clean[7:12]}"
    else:
        formatted = f"+{clean}"
    
    return clean, formatted

@api_router.post("/whatsapp/incoming")
async def handle_incoming_whatsapp(data: WhatsAppIncoming):
    """Handle incoming WhatsApp message from Node.js service
    
    This handler:
    1. Checks if message is HISTORICAL (before connection) - read-only, no reply
    2. Checks if number is EXCLUDED (silent monitoring - no reply)
    3. Checks if message is from OWNER with lead injection command
    4. Otherwise, processes normally and sends AI auto-reply
    """
    global whatsapp_connection_timestamp
    
    try:
        # Normalize phone number
        phone, phone_formatted = normalize_phone(data.phone)
        
        now = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Incoming WhatsApp: {phone_formatted}, Historical: {data.isHistorical}, Message: {data.message[:50]}...")
        
        # ========== CHECK 0: Is this a HISTORICAL message? ==========
        if data.isHistorical:
            logger.info(f"HISTORICAL MODE: Message from {phone_formatted} is before connection timestamp - storing without reply")
            
            # Store the message for context but do not trigger any AI response
            # Find or create customer silently
            customer = await db.customers.find_one({"phone": {"$regex": phone[-10:]}}, {"_id": 0})
            if not customer:
                customer_id = str(uuid.uuid4())
                customer = {
                    "id": customer_id,
                    "name": f"WhatsApp {phone_formatted}",
                    "phone": phone_formatted,
                    "customer_type": "individual",
                    "addresses": [],
                    "preferences": {"communication": "whatsapp"},
                    "purchase_history": [],
                    "devices": [],
                    "tags": ["whatsapp", "historical-sync"],
                    "notes": "",
                    "total_spent": 0.0,
                    "last_interaction": now,
                    "created_at": now
                }
                await db.customers.insert_one(customer)
            
            # Find or create conversation
            conv = await db.conversations.find_one({"customer_id": customer["id"]})
            if not conv:
                conv_id = str(uuid.uuid4())
                conv = {
                    "id": conv_id,
                    "customer_id": customer["id"],
                    "customer_name": customer["name"],
                    "customer_phone": customer["phone"],
                    "channel": "whatsapp",
                    "status": "active",
                    "last_message": data.message,
                    "last_message_at": now,
                    "unread_count": 0,  # Don't mark as unread for historical
                    "created_at": now
                }
                await db.conversations.insert_one(conv)
            
            # Save historical message with flag
            msg_id = str(uuid.uuid4())
            msg_doc = {
                "id": msg_id,
                "conversation_id": conv["id"],
                "content": data.message,
                "sender_type": "customer",
                "message_type": "text",
                "attachments": [],
                "wa_message_id": data.messageId,
                "is_historical": True,  # Mark as historical
                "created_at": now
            }
            await db.messages.insert_one(msg_doc)
            
            return {
                "success": True,
                "mode": "historical",
                "message": "Historical message stored (no AI reply)",
                "customer_id": customer["id"]
            }
        
        # ========== CHECK 1: Is this number EXCLUDED? ==========
        is_excluded = await is_number_excluded(phone)
        if is_excluded:
            exclusion_info = await get_excluded_number_info(phone)
            logger.info(f"SILENT MODE: Message from excluded number {phone_formatted} (Tag: {exclusion_info.get('tag', 'unknown')})")
            
            # Still save the message for reference, but DON'T reply
            # Find or create a "silent" record for this number
            silent_record = await db.silent_messages.find_one({"phone": {"$regex": phone[-10:]}})
            if not silent_record:
                silent_id = str(uuid.uuid4())
                silent_record = {
                    "id": silent_id,
                    "phone": phone_formatted,
                    "tag": exclusion_info.get("tag", "other"),
                    "messages": [],
                    "created_at": now
                }
                await db.silent_messages.insert_one(silent_record)
            
            # Append message to silent record
            await db.silent_messages.update_one(
                {"phone": {"$regex": phone[-10:]}},
                {"$push": {"messages": {
                    "content": data.message,
                    "timestamp": now,
                    "has_media": data.hasMedia
                }}}
            )
            
            return {
                "success": True,
                "mode": "silent",
                "message": "Message recorded (excluded number - no reply sent)",
                "tag": exclusion_info.get("tag", "other")
            }
        
        # ========== CHECK 2: Is this from OWNER? ==========
        settings = await db.settings.find_one({"type": "global"}, {"_id": 0})
        owner_phone = settings.get("owner_phone", "").replace("+", "").replace(" ", "").replace("-", "") if settings else ""
        
        if owner_phone and phone[-10:] == owner_phone[-10:]:
            # This is from the owner
            
            # Parse escalation code from message (e.g., "ESC01: Here's the answer")
            escalation_code, actual_reply = parse_escalation_code_from_message(data.message)
            
            # CHECK 2a: Is this a reply to a specific escalation?
            if escalation_code:
                # Find the specific escalation by code
                target_escalation = await db.escalations.find_one(
                    {"escalation_code": escalation_code, "status": "pending_owner_reply"},
                    {"_id": 0}
                )
                
                if not target_escalation:
                    # Code not found or already resolved
                    await send_whatsapp_message(phone, f"[WARNING] Escalation {escalation_code} not found or already resolved.\n\nPending escalations:")
                    
                    # List pending escalations
                    pending_list = await db.escalations.find(
                        {"status": "pending_owner_reply"},
                        {"_id": 0, "escalation_code": 1, "customer_name": 1, "customer_message": 1}
                    ).to_list(10)
                    
                    if pending_list:
                        pending_msg = "\n".join([
                            f"• *{p['escalation_code']}* - {p['customer_name']}: {p['customer_message'][:50]}..."
                            for p in pending_list
                        ])
                        await send_whatsapp_message(phone, pending_msg)
                    else:
                        await send_whatsapp_message(phone, "No pending escalations.")
                    
                    return {
                        "success": False,
                        "mode": "owner_reply_invalid",
                        "message": f"Escalation {escalation_code} not found"
                    }
                
                # Found the correct escalation - process the reply
                customer_phone = target_escalation.get("customer_phone")
                customer_name = target_escalation.get("customer_name", "Customer")
                original_question = target_escalation.get("customer_message", "")
                
                if customer_phone:
                    owner_reply = actual_reply.strip()
                    
                    # Polish the reply using AI
                    try:
                        polish_prompt = f"""Polish this owner reply to make it professional and friendly for a customer.

ORIGINAL CUSTOMER QUESTION: "{original_question}"

OWNER RAW REPLY: "{owner_reply}"

RULES:
1. Keep ALL the information exactly the same (prices, specs, availability)
2. Do NOT add any new information
3. Do NOT remove any information
4. Make it friendly and professional
5. Keep it concise (2-4 sentences max)
6. Add appropriate greeting if missing
7. Do NOT mention "owner", "boss", or internal processes

Write the polished reply:"""

                        chat = LlmChat(
                            api_key=EMERGENT_LLM_KEY,
                            session_id=f"polish-{target_escalation['id']}",
                            system_message="You are a helpful store assistant. Polish the owner reply to make it professional and friendly."
                        ).with_model("openai", "gpt-5.2")
                        
                        polished_reply = await chat.send_message(UserMessage(text=polish_prompt))
                        
                        if polished_reply and len(polished_reply.strip()) > 10:
                            formatted_reply = polished_reply.strip()
                        else:
                            formatted_reply = owner_reply
                            
                    except Exception as e:
                        logger.error(f"Failed to polish reply: {e}")
                        formatted_reply = owner_reply
                        if len(owner_reply) < 50 and not owner_reply.endswith(('.', '!', '?')):
                            formatted_reply = owner_reply + "."
                    
                    # Send polished reply to the customer
                    await send_whatsapp_message(customer_phone, formatted_reply)
                    
                    # Mark this specific escalation as resolved
                    await db.escalations.update_one(
                        {"id": target_escalation["id"]},
                        {"$set": {
                            "status": "resolved",
                            "owner_reply": owner_reply,
                            "formatted_reply": formatted_reply,
                            "resolved_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    
                    # Save message in customer conversation
                    conv = await db.conversations.find_one(
                        {"customer_phone": {"$regex": customer_phone[-10:]}},
                        {"_id": 0}
                    )
                    if conv:
                        await db.messages.insert_one({
                            "id": str(uuid.uuid4()),
                            "conversation_id": conv["id"],
                            "content": formatted_reply,
                            "sender_type": "agent",
                            "message_type": "text",
                            "escalation_code": escalation_code,
                            "attachments": [],
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
                        
                        # Update conversation status
                        await db.conversations.update_one(
                            {"id": conv["id"]},
                            {"$set": {
                                "last_message": formatted_reply,
                                "last_message_at": datetime.now(timezone.utc).isoformat(),
                                "status": "active",
                                "escalated_at": None,
                                "escalation_reason": None,
                                "current_escalation_code": None,
                                "sla_deadline": None,
                                "sla_reminders_sent": 0
                            }}
                        )
                    
                    # Confirm to owner
                    preview = formatted_reply[:80] + "..." if len(formatted_reply) > 80 else formatted_reply
                    await send_whatsapp_message(phone, f"[OK] {escalation_code} resolved!\nSent to {customer_name}:\n\n\"{preview}\"")
                    
                    logger.info(f"Owner reply for {escalation_code} polished and forwarded to customer: {customer_phone}")
                    return {
                        "success": True,
                        "mode": "owner_reply_forwarded",
                        "escalation_code": escalation_code,
                        "customer_phone": customer_phone
                    }
            
            # No escalation code - check if there are any pending escalations
            pending_escalations = await db.escalations.find(
                {"status": "pending_owner_reply"},
                {"_id": 0}
            ).to_list(10)
            
            if pending_escalations and not data.message.lower().startswith(("customer", "lead", "inject")):
                # There are pending escalations but owner did not specify which one
                if len(pending_escalations) == 1:
                    # Only one pending - assume it is for that one (backward compatible)
                    target_escalation = pending_escalations[0]
                    escalation_code = target_escalation.get("escalation_code", "ESC??")
                    customer_phone = target_escalation.get("customer_phone")
                    customer_name = target_escalation.get("customer_name", "Customer")
                    original_question = target_escalation.get("customer_message", "")
                    
                    if customer_phone:
                        owner_reply = data.message.strip()
                        
                        # Polish and send (same logic as above)
                        try:
                            polish_prompt = f"""Polish this owner reply to make it professional and friendly.
ORIGINAL CUSTOMER QUESTION: "{original_question}"
OWNER RAW REPLY: "{owner_reply}"
RULES: Keep ALL info same, be friendly, 2-4 sentences, no mention of owner/boss.
Write the polished reply:"""

                            chat = LlmChat(
                                api_key=EMERGENT_LLM_KEY,
                                session_id=f"polish-{target_escalation['id']}",
                                system_message="Polish the owner reply professionally."
                            ).with_model("openai", "gpt-5.2")
                            
                            polished_reply = await chat.send_message(UserMessage(text=polish_prompt))
                            formatted_reply = polished_reply.strip() if polished_reply and len(polished_reply.strip()) > 10 else owner_reply
                        except:
                            formatted_reply = owner_reply
                        
                        await send_whatsapp_message(customer_phone, formatted_reply)
                        
                        await db.escalations.update_one(
                            {"id": target_escalation["id"]},
                            {"$set": {
                                "status": "resolved",
                                "owner_reply": owner_reply,
                                "formatted_reply": formatted_reply,
                                "resolved_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        
                        # Update conversation
                        conv = await db.conversations.find_one({"customer_phone": {"$regex": customer_phone[-10:]}}, {"_id": 0})
                        if conv:
                            await db.messages.insert_one({
                                "id": str(uuid.uuid4()),
                                "conversation_id": conv["id"],
                                "content": formatted_reply,
                                "sender_type": "agent",
                                "message_type": "text",
                                "attachments": [],
                                "created_at": datetime.now(timezone.utc).isoformat()
                            })
                            await db.conversations.update_one(
                                {"id": conv["id"]},
                                {"$set": {"last_message": formatted_reply, "last_message_at": datetime.now(timezone.utc).isoformat(), "status": "active"}}
                            )
                        
                        await send_whatsapp_message(phone, f"[OK] {escalation_code} resolved!\nSent to {customer_name}")
                        return {"success": True, "mode": "owner_reply_forwarded", "escalation_code": escalation_code}
                else:
                    # Multiple pending escalations - ask owner to specify
                    pending_msg = "[WARNING] Multiple pending escalations. Please reply with the escalation code:\n\n"
                    for esc in pending_escalations:
                        code = esc.get("escalation_code", "ESC??")
                        name = esc.get("customer_name", "Unknown")
                        msg = esc.get("customer_message", "")[:40]
                        pending_msg += f"• *{code}*: {name} - \"{msg}...\"\n"
                    
                    pending_msg += f"\nExample: {pending_escalations[0].get('escalation_code', 'ESC01')}: your answer"
                    await send_whatsapp_message(phone, pending_msg)
                    
                    return {
                        "success": False,
                        "mode": "owner_needs_to_specify",
                        "pending_count": len(pending_escalations)
                    }
            
            # CHECK 2b: Is this a lead injection command?
            lead_data = parse_lead_injection_command(data.message)
            if lead_data:
                logger.info(f"LEAD INJECTION: Owner command detected - {lead_data}")
                
                # Process lead injection
                lead_result = await inject_lead_internal(
                    customer_name=lead_data["customer_name"],
                    phone=lead_data["phone"],
                    product_interest=lead_data["product_interest"],
                    notes=f"Injected via WhatsApp command: {data.message}",
                    created_by="Owner (WhatsApp)"
                )
                
                # Send confirmation to owner
                confirm_msg = f"[OK] Lead created for {lead_data['customer_name']} ({lead_data['phone']}). AI has initiated contact about {lead_data['product_interest']}."
                await send_whatsapp_message(phone, confirm_msg)
                
                return {
                    "success": True,
                    "mode": "lead_injection",
                    "lead_id": lead_result.get("lead_id"),
                    "message": "Lead injected and outbound message sent"
                }
        
        # ========== NORMAL PROCESSING: Create/update customer and conversation ==========
        # Find or create customer - use multiple lookup strategies
        # Extract last 10 digits for matching
        phone_last10 = phone[-10:] if len(phone) >= 10 else phone
        
        # Try multiple lookup patterns
        customer = await db.customers.find_one(
            {"$or": [
                {"phone": {"$regex": phone_last10}},
                {"phone": phone},
                {"phone": phone_formatted}
            ]},
            {"_id": 0}
        )
        
        if not customer:
            customer_id = str(uuid.uuid4())
            # Store phone in clean format for easier matching
            customer = {
                "id": customer_id,
                "name": f"WhatsApp {phone_formatted}",
                "phone": phone,  # Store clean digits
                "phone_formatted": phone_formatted,  # Store formatted version
                "customer_type": "individual",
                "addresses": [],
                "preferences": {"communication": "whatsapp"},
                "purchase_history": [],
                "devices": [],
                "tags": ["whatsapp", "new"],
                "notes": "",
                "total_spent": 0.0,
                "last_interaction": now,
                "created_at": now
            }
            await db.customers.insert_one(customer)
            logger.info(f"Created new customer: {phone_formatted}")
        else:
            logger.info(f"Found existing customer: {customer.get('name')} ({customer.get('id')})")
        
        # Find or create conversation - look up by customer_id OR customer_phone
        conv = await db.conversations.find_one(
            {"$or": [
                {"customer_id": customer["id"]},
                {"customer_phone": {"$regex": phone_last10}}
            ]},
            {"_id": 0}
        )
        if not conv:
            conv_id = str(uuid.uuid4())
            conv = {
                "id": conv_id,
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "customer_phone": customer["phone"],
                "channel": "whatsapp",
                "status": "active",
                "last_message": data.message,
                "last_message_at": now,
                "unread_count": 1,
                "created_at": now
            }
            await db.conversations.insert_one(conv)
        else:
            await db.conversations.update_one(
                {"id": conv["id"]},
                {"$set": {"last_message": data.message, "last_message_at": now}, "$inc": {"unread_count": 1}}
            )
        
        # ========== AUTO-CREATE/UPDATE TOPIC BASED ON MESSAGE ==========
        # Check if there is an active topic for this customer
        active_topic = await db.topics.find_one(
            {"customer_id": customer["id"], "status": {"$in": ["open", "in_progress"]}},
            {"_id": 0}
        )
        
        if not active_topic:
            # Auto-detect topic type from message
            msg_lower = data.message.lower()
            
            # Repair keywords
            repair_keywords = ["repair", "fix", "broken", "not working", "broke", "damage", "crack", "issue", "problem", "dead", "will not turn on", "screen"]
            # Sales keywords
            sales_keywords = ["buy", "price", "cost", "purchase", "want to get", "looking for", "interested in", "available", "how much"]
            
            # Determine topic type
            is_repair = any(word in msg_lower for word in repair_keywords)
            is_sales = any(word in msg_lower for word in sales_keywords)
            
            if is_repair:
                topic_type = "service_request"
                # Try to extract device from message
                device_hints = ["mac", "macbook", "iphone", "ipad", "airpod", "watch", "imac"]
                device_found = next((d for d in device_hints if d in msg_lower), None)
                topic_title = f"{device_found.title() if device_found else 'Device'} Repair Request"
            elif is_sales:
                topic_type = "product_inquiry"
                topic_title = "Product Inquiry"
            else:
                topic_type = "support"
                topic_title = "General Inquiry"
            
            # Create topic
            topic_id = str(uuid.uuid4())
            topic_doc = {
                "id": topic_id,
                "conversation_id": conv["id"],
                "customer_id": customer["id"],
                "topic_type": topic_type,
                "title": topic_title,
                "status": "open",
                "device_info": None,
                "metadata": {"initial_message": data.message[:200]},
                "step_count": 0,
                "last_ai_question": None,
                "last_customer_message": data.message,
                "created_at": now,
                "updated_at": now
            }
            await db.topics.insert_one(topic_doc)
            logger.info(f"Auto-created topic: {topic_title} ({topic_type}) for customer {customer['id']}")
        
        # Save incoming message
        msg_id = str(uuid.uuid4())
        msg_doc = {
            "id": msg_id,
            "conversation_id": conv["id"],
            "content": data.message,
            "sender_type": "customer",
            "message_type": "text",
            "attachments": [],
            "wa_message_id": data.messageId,
            "created_at": now
        }
        await db.messages.insert_one(msg_doc)
        
        # Update customer last interaction
        await db.customers.update_one(
            {"id": customer["id"]},
            {"$set": {"last_interaction": now}}
        )
        
        logger.info(f"Incoming message from {phone_formatted}: {data.message[:50]}...")
        
        # ========== AI AUTO-REPLY ==========
        # Check if auto-reply is enabled in settings
        auto_reply_enabled = settings.get("auto_reply", True) if settings else True
        
        ai_reply_sent = False
        ai_response = None
        
        if auto_reply_enabled:
            # Generate AI response
            ai_response = await generate_ai_reply(customer["id"], conv["id"], data.message)
            
            if ai_response:
                # Send via WhatsApp
                reply_sent = await send_whatsapp_message(phone, ai_response)
                
                if reply_sent:
                    # Save AI reply
                    reply_id = str(uuid.uuid4())
                    reply_now = datetime.now(timezone.utc).isoformat()
                    reply_doc = {
                        "id": reply_id,
                        "conversation_id": conv["id"],
                        "content": ai_response,
                        "sender_type": "ai",
                        "message_type": "text",
                        "attachments": [],
                        "created_at": reply_now
                    }
                    await db.messages.insert_one(reply_doc)
                    
                    # Update conversation
                    await db.conversations.update_one(
                        {"id": conv["id"]},
                        {"$set": {"last_message": ai_response, "last_message_at": reply_now}}
                    )
                    
                    ai_reply_sent = True
                    logger.info(f"AI reply sent to {phone_formatted}")
        
        return {
            "success": True,
            "mode": "normal",
            "customer_id": customer["id"],
            "conversation_id": conv["id"],
            "message_id": msg_id,
            "ai_reply_sent": ai_reply_sent,
            "ai_response": ai_response[:50] + "..." if ai_response and len(ai_response) > 50 else ai_response
        }
    except Exception as e:
        logger.error(f"Error handling incoming message: {e}")
        return {"success": False, "error": str(e)}

async def inject_lead_internal(customer_name: str, phone: str, product_interest: str, notes: str, created_by: str) -> Dict:
    """Internal function to inject a lead (used by both API and WhatsApp command)"""
    now = datetime.now(timezone.utc).isoformat()
    
    # Normalize phone
    phone_clean = phone.replace(" ", "").replace("-", "")
    if not phone_clean.startswith("+"):
        if len(phone_clean) == 10:
            phone_clean = "+91" + phone_clean
        elif phone_clean.startswith("91") and len(phone_clean) == 12:
            phone_clean = "+" + phone_clean
    phone_formatted = f"{phone_clean[:3]} {phone_clean[3:8]} {phone_clean[8:]}" if len(phone_clean) >= 13 else phone_clean
    
    # Create or find customer
    existing_customer = await db.customers.find_one({"phone": {"$regex": phone_clean[-10:]}}, {"_id": 0})
    
    if existing_customer:
        customer = existing_customer
        customer_id = customer["id"]
    else:
        customer_id = str(uuid.uuid4())
        customer = {
            "id": customer_id,
            "name": customer_name,
            "phone": phone_formatted,
            "customer_type": "individual",
            "addresses": [],
            "preferences": {"communication": "whatsapp"},
            "purchase_history": [],
            "devices": [],
            "tags": ["lead", "owner-injected"],
            "notes": f"Lead injected by {created_by}: {product_interest}",
            "total_spent": 0.0,
            "last_interaction": now,
            "created_at": now
        }
        await db.customers.insert_one(customer)
    
    # Create conversation
    conv_id = str(uuid.uuid4())
    conv = {
        "id": conv_id,
        "customer_id": customer_id,
        "customer_name": customer["name"],
        "customer_phone": customer["phone"],
        "channel": "whatsapp",
        "status": "active",
        "last_message": None,
        "last_message_at": now,
        "unread_count": 0,
        "source": "owner-injected",
        "created_at": now
    }
    await db.conversations.insert_one(conv)
    
    # Create topic
    topic_id = str(uuid.uuid4())
    topic = {
        "id": topic_id,
        "conversation_id": conv_id,
        "customer_id": customer_id,
        "topic_type": "product_inquiry",
        "title": f"Interest in {product_interest}",
        "status": "open",
        "device_info": None,
        "metadata": {"product": product_interest, "source": "owner-injected"},
        "created_at": now,
        "updated_at": now
    }
    await db.topics.insert_one(topic)
    
    # Generate outbound message - Natural, human-like greeting
    settings = await db.settings.find_one({"type": "global"}, {"_id": 0})
    store_name = settings.get("store_name", "NeoStore") if settings else "NeoStore"
    
    # Get customer first name
    first_name = customer['name'].split()[0] if customer['name'] != "Unknown" else ""
    greeting = f"Hi {first_name} 👋" if first_name else "Hi there 👋"
    
    # Check if product exists in catalog
    product = await db.products.find_one(
        {"name": {"$regex": product_interest, "$options": "i"}, "is_active": True},
        {"_id": 0}
    )
    
    if product:
        price_str = f"{product['base_price']:,.0f}"
        outbound_msg = f"""{greeting}
Thanks for reaching out to {store_name}!

I see you are interested in the {product['name']}.
It is available at Rs {price_str}.

How can I help you today - more details, availability, or anything else?"""
    elif product_interest and product_interest != "General Inquiry":
        outbound_msg = f"""{greeting}
Thanks for reaching out to {store_name}!

I see you are interested in {product_interest}.
How can I help you today-pricing, availability, or something else?"""
    else:
        outbound_msg = f"""{greeting}
Thanks for reaching out to {store_name}!

How can I help you today?"""
    
    # Send message
    message_sent = await send_whatsapp_message(phone_clean, outbound_msg)
    
    if message_sent:
        msg_id = str(uuid.uuid4())
        msg_doc = {
            "id": msg_id,
            "conversation_id": conv_id,
            "topic_id": topic_id,
            "content": outbound_msg,
            "sender_type": "ai",
            "message_type": "text",
            "attachments": [],
            "created_at": now
        }
        await db.messages.insert_one(msg_doc)
        await db.conversations.update_one({"id": conv_id}, {"$set": {"last_message": outbound_msg, "last_message_at": now}})
    
    # Create lead record
    lead_id = str(uuid.uuid4())
    lead = {
        "id": lead_id,
        "customer_id": customer_id,
        "customer_name": customer["name"],
        "phone": phone_clean,
        "product_interest": product_interest,
        "conversation_id": conv_id,
        "topic_id": topic_id,
        "outbound_message_sent": message_sent,
        "status": "in_progress" if message_sent else "pending",
        "notes": notes,
        "created_at": now,
        "created_by": created_by
    }
    await db.lead_injections.insert_one(lead)
    
    return {"lead_id": lead_id, "customer_id": customer_id, "conversation_id": conv_id}

@api_router.post("/whatsapp/sync-messages")
async def sync_whatsapp_messages(data: WhatsAppSyncMessages):
    """Sync historical messages from WhatsApp"""
    try:
        phone = data.phone.replace("+", "").replace(" ", "")
        if not phone.startswith("91") and len(phone) == 10:
            phone = "91" + phone
        phone_formatted = f"+{phone[:2]} {phone[2:7]} {phone[7:]}" if len(phone) >= 12 else phone
        
        # Find or create customer
        customer = await db.customers.find_one({"phone": {"$regex": phone[-10:]}}, {"_id": 0})
        if not customer:
            customer_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            customer = {
                "id": customer_id,
                "name": data.chatName or f"WhatsApp {phone_formatted}",
                "phone": phone_formatted,
                "customer_type": "individual",
                "addresses": [],
                "preferences": {"communication": "whatsapp"},
                "purchase_history": [],
                "devices": [],
                "tags": ["whatsapp", "synced"],
                "notes": "",
                "total_spent": 0.0,
                "last_interaction": now,
                "created_at": now
            }
            await db.customers.insert_one(customer)
        elif data.chatName and customer["name"].startswith("WhatsApp"):
            # Update name if we have a better one
            await db.customers.update_one({"id": customer["id"]}, {"$set": {"name": data.chatName}})
            customer["name"] = data.chatName
        
        # Find or create conversation
        conv = await db.conversations.find_one({"customer_id": customer["id"]})
        now = datetime.now(timezone.utc).isoformat()
        if not conv:
            conv_id = str(uuid.uuid4())
            conv = {
                "id": conv_id,
                "customer_id": customer["id"],
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
        
        # Sync messages (skip duplicates)
        synced_count = 0
        for msg in data.messages:
            existing = await db.messages.find_one({"wa_message_id": msg.get("id")})
            if existing:
                continue
            
            msg_id = str(uuid.uuid4())
            timestamp = datetime.fromtimestamp(msg.get("timestamp", 0), tz=timezone.utc).isoformat() if msg.get("timestamp") else now
            msg_doc = {
                "id": msg_id,
                "conversation_id": conv["id"],
                "content": msg.get("body", ""),
                "sender_type": "ai" if msg.get("fromMe") else "customer",
                "message_type": "media" if msg.get("hasMedia") else "text",
                "attachments": [],
                "wa_message_id": msg.get("id"),
                "created_at": timestamp
            }
            await db.messages.insert_one(msg_doc)
            synced_count += 1
        
        # Update conversation with latest message
        if data.messages:
            latest = max(data.messages, key=lambda x: x.get("timestamp", 0))
            await db.conversations.update_one(
                {"id": conv["id"]},
                {"$set": {
                    "last_message": latest.get("body", "")[:100],
                    "last_message_at": datetime.fromtimestamp(latest.get("timestamp", 0), tz=timezone.utc).isoformat() if latest.get("timestamp") else now,
                    "customer_name": customer["name"]
                }}
            )
        
        logger.info(f"Synced {synced_count} messages for {phone_formatted}")
        return {"success": True, "synced": synced_count}
    except Exception as e:
        logger.error(f"Error syncing messages: {e}")
        return {"success": False, "error": str(e)}

@api_router.post("/whatsapp/simulate-message")
async def simulate_whatsapp_message(phone: str, message: str, user: dict = Depends(get_current_user)):
    """Simulate receiving a WhatsApp message for testing"""
    return await handle_incoming_whatsapp(WhatsAppIncoming(phone=phone, message=message))

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
            "owner_phone": "",
            "escalation_phone": "+91 98765 43210",
            "follow_up_days": 3,
            "ai_enabled": True,
            "auto_reply": True,
            "ai_instructions": "",
            "inactivity_summary_minutes": 30
        }
        await db.settings.insert_one(settings)
    # Ensure fields exist for backward compatibility
    if "owner_phone" not in settings:
        settings["owner_phone"] = ""
    if "ai_instructions" not in settings:
        settings["ai_instructions"] = ""
    return settings

@api_router.put("/settings")
async def update_settings(settings: Dict[str, Any], user: dict = Depends(get_current_user)):
    await db.settings.update_one({"type": "global"}, {"$set": settings}, upsert=True)
    return {"message": "Settings updated"}

# ============== AUTO-MESSAGING SETTINGS ==============

@api_router.get("/auto-messages/settings")
async def get_auto_message_settings_api(user: dict = Depends(get_current_user)):
    """Get auto-messaging settings and templates"""
    return await get_auto_message_settings()

@api_router.put("/auto-messages/settings")
async def update_auto_message_settings_api(settings: Dict[str, Any], user: dict = Depends(get_current_user)):
    """Update auto-messaging settings"""
    await db.auto_message_settings.update_one(
        {"type": "global"},
        {"$set": settings},
        upsert=True
    )
    return {"message": "Auto-message settings updated"}

@api_router.get("/auto-messages/templates")
async def get_auto_message_templates(user: dict = Depends(get_current_user)):
    """Get all message templates"""
    settings = await get_auto_message_settings()
    return settings.get("templates", DEFAULT_TEMPLATES)

@api_router.put("/auto-messages/templates/{trigger_type}")
async def update_auto_message_template(
    trigger_type: str,
    template: str,
    user: dict = Depends(get_current_user)
):
    """Update a specific message template"""
    valid_triggers = list(DEFAULT_TEMPLATES.keys())
    if trigger_type not in valid_triggers:
        raise HTTPException(status_code=400, detail=f"Invalid trigger type. Valid: {valid_triggers}")
    
    await db.auto_message_settings.update_one(
        {"type": "global"},
        {"$set": {f"templates.{trigger_type}": template}},
        upsert=True
    )
    return {"message": f"Template for {trigger_type} updated"}

@api_router.get("/auto-messages/history")
async def get_auto_message_history(
    customer_id: Optional[str] = None,
    trigger_type: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """Get history of sent auto-messages"""
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if trigger_type:
        query["trigger_type"] = trigger_type
    
    messages = await db.auto_messages_sent.find(query, {"_id": 0}).sort("sent_at", -1).limit(limit).to_list(limit)
    return messages

@api_router.get("/auto-messages/scheduled")
async def get_scheduled_messages(
    status: str = "pending",
    user: dict = Depends(get_current_user)
):
    """Get scheduled follow-up messages"""
    messages = await db.scheduled_messages.find(
        {"status": status},
        {"_id": 0}
    ).sort("scheduled_for", 1).to_list(100)
    return messages

@api_router.delete("/auto-messages/scheduled/{message_id}")
async def cancel_scheduled_message(message_id: str, user: dict = Depends(get_current_user)):
    """Cancel a scheduled message"""
    result = await db.scheduled_messages.update_one(
        {"id": message_id, "status": "pending"},
        {"$set": {"status": "cancelled"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Scheduled message not found or already processed")
    return {"message": "Scheduled message cancelled"}

@api_router.post("/auto-messages/test/{trigger_type}")
async def test_auto_message(
    trigger_type: str,
    customer_id: str,
    conversation_id: str,
    user: dict = Depends(get_current_user)
):
    """Test send an auto-message (for debugging)"""
    result = await send_auto_message(
        customer_id=customer_id,
        conversation_id=conversation_id,
        trigger_type=trigger_type,
        template_vars={"topic": "test", "amount": "1,000", "ticket_id": "TEST-001"}
    )
    return result

@api_router.post("/auto-messages/schedule-follow-up")
async def schedule_follow_up_api(
    customer_id: str,
    conversation_id: str,
    topic_id: str,
    delay_hours: int = 48,
    user: dict = Depends(get_current_user)
):
    """Manually schedule a follow-up message"""
    # Get topic info
    topic = await db.topics.find_one({"id": topic_id}, {"_id": 0})
    topic_title = topic.get("title", "your inquiry") if topic else "your inquiry"
    
    scheduled_id = await schedule_follow_up(
        customer_id=customer_id,
        conversation_id=conversation_id,
        topic_id=topic_id,
        trigger_type="no_response",
        delay_hours=delay_hours,
        template_vars={"topic": topic_title}
    )
    
    return {"scheduled_id": scheduled_id, "delay_hours": delay_hours}

# ============== AI BEHAVIOR POLICY ==============

# Default AI Behavior Policy
DEFAULT_AI_POLICY = {
    "version": "1.0",
    "enabled": True,
    "last_updated": None,
    "updated_by": None,
    
    # Global Rules
    "global_rules": {
        "allowed_topics": [
            "apple_products",
            "apple_repairs", 
            "it_products",
            "it_services"
        ],
        "disallowed_behavior": [
            "off_topic_replies",
            "competitor_comparison",
            "repeating_greetings",
            "assuming_intent",
            "mentioning_delivery_without_context",
            "guessing_prices",
            "multiple_questions_at_once"
        ],
        "scope_message": "I can help with Apple products, repairs, and IT services. What do you need?"
    },
    
    # Conversation States
    "states": {
        "GREETING": {
            "enabled": True,
            "triggers": ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "hii", "hiii", "hlo"],
            "allowed_actions": ["greet_user", "ask_how_can_help"],
            "forbidden_actions": ["product_pitch", "delivery_mention", "past_context_reference", "price_mention"],
            "response_template": "Hi! How can I help you today?"
        },
        "INTENT_COLLECTION": {
            "enabled": True,
            "triggers": ["need", "want", "looking", "interested", "help", "issue", "problem"],
            "allowed_actions": ["ask_clarifying_question"],
            "rules": ["ask_one_question_only", "wait_for_response"],
            "clarification_template": "Got it. Could you tell me more about what you need?"
        },
        "ACTION": {
            "enabled": True,
            "rules": ["respond_only_within_scope", "no_assumptions", "use_exact_prices"],
            "sales_flow": {
                "mention_delivery_only_if_asked": True,
                "require_storage_confirmation": True
            },
            "repair_flow": {
                "required_fields": ["device_model", "issue_description"],
                "ask_one_field_at_a_time": True
            }
        },
        "CLOSURE": {
            "enabled": True,
            "triggers": ["thanks", "thank you", "bye", "goodbye", "ok", "okay"],
            "templates": {
                "thanks": "You are welcome!",
                "bye": "Bye! Take care.",
                "ok": "Great! Let me know if you need anything else."
            }
        },
        "ESCALATION": {
            "enabled": True,
            "triggers": ["escalate_required", "unknown_info", "out_of_scope"],
            "placeholder_message": "Let me check on that and get back to you shortly.",
            "notify_owner": True
        }
    },
    
    # Response Constraints
    "response_rules": {
        "greeting_limit": "once_per_conversation",
        "question_limit": "one_at_a_time",
        "max_response_length": 150,
        "tone": "friendly_professional",
        "language": "english_hinglish",
        "emoji_usage": "minimal"
    },
    
    # Fallback Rules
    "fallback": {
        "unclear_data": {
            "action": "ask_for_clarification",
            "template": "Could you please explain a bit more?"
        },
        "out_of_scope": {
            "action": "polite_refusal",
            "template": "I can help with Apple products, repairs, and IT services. Is there something specific in that area?"
        },
        "system_error": {
            "action": "escalate_to_human",
            "template": "Let me connect you with our team for this."
        }
    },
    
    # System Triggers
    "system_triggers": {
        "lead_inject": {
            "enabled": True,
            "keywords": ["lead inject", "customer name", "lead:"],
            "action": ["extract_name", "extract_phone", "extract_product", "store_lead"],
            "reply_to_user": False,
            "start_state": "GREETING"
        }
    }
}

@api_router.get("/ai-policy")
async def get_ai_policy(user: dict = Depends(get_current_user)):
    """Get the current AI Behavior Policy"""
    policy = await db.ai_policy.find_one({"type": "global"}, {"_id": 0})
    if not policy:
        # Return default and save it
        policy = {**DEFAULT_AI_POLICY, "type": "global"}
        await db.ai_policy.insert_one(policy.copy())
        policy.pop("_id", None)
    return policy

@api_router.put("/ai-policy")
async def update_ai_policy(policy: Dict[str, Any], user: dict = Depends(get_current_user)):
    """Update the AI Behavior Policy"""
    policy["last_updated"] = datetime.now(timezone.utc).isoformat()
    policy["updated_by"] = user.get("name", "Admin")
    policy["type"] = "global"
    
    await db.ai_policy.update_one(
        {"type": "global"},
        {"$set": policy},
        upsert=True
    )
    return {"message": "AI Policy updated successfully"}

@api_router.put("/ai-policy/section/{section}")
async def update_ai_policy_section(section: str, data: Dict[str, Any], user: dict = Depends(get_current_user)):
    """Update a specific section of the AI Policy"""
    valid_sections = ["global_rules", "states", "response_rules", "fallback", "system_triggers"]
    if section not in valid_sections:
        raise HTTPException(status_code=400, detail=f"Invalid section. Valid: {valid_sections}")
    
    await db.ai_policy.update_one(
        {"type": "global"},
        {
            "$set": {
                section: data,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "updated_by": user.get("name", "Admin")
            }
        },
        upsert=True
    )
    return {"message": f"AI Policy section '{section}' updated"}

@api_router.put("/ai-policy/state/{state_name}")
async def update_ai_policy_state(state_name: str, data: Dict[str, Any], user: dict = Depends(get_current_user)):
    """Update a specific state in the AI Policy"""
    state_name = state_name.upper()
    valid_states = ["GREETING", "INTENT_COLLECTION", "ACTION", "CLOSURE", "ESCALATION"]
    if state_name not in valid_states:
        raise HTTPException(status_code=400, detail=f"Invalid state. Valid: {valid_states}")
    
    await db.ai_policy.update_one(
        {"type": "global"},
        {
            "$set": {
                f"states.{state_name}": data,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "updated_by": user.get("name", "Admin")
            }
        },
        upsert=True
    )
    return {"message": f"AI Policy state '{state_name}' updated"}

@api_router.post("/ai-policy/reset")
async def reset_ai_policy(user: dict = Depends(get_current_user)):
    """Reset AI Policy to defaults"""
    policy = {**DEFAULT_AI_POLICY, "type": "global", "last_updated": datetime.now(timezone.utc).isoformat(), "updated_by": user.get("name", "Admin")}
    await db.ai_policy.replace_one({"type": "global"}, policy, upsert=True)
    return {"message": "AI Policy reset to defaults"}

# Helper function to load AI policy for generate_ai_reply
async def get_ai_policy_config() -> dict:
    """Get AI policy configuration for use in AI reply generation"""
    policy = await db.ai_policy.find_one({"type": "global"}, {"_id": 0})
    if not policy:
        return DEFAULT_AI_POLICY
    return policy

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
        {"id": str(uuid.uuid4()), "title": "Payment Methods", "category": "faq", "content": "We accept: Cash, Credit/Debit Cards, UPI, Net Banking, EMI options available on purchases above Rs.10,000", "tags": ["payment", "emi"], "is_active": True, "created_at": now, "updated_at": now},
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
