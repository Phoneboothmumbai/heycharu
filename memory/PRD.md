# Sales Brain - AI-Powered Customer Intelligence Platform

## Product Overview
Sales Brain is a SaaS platform that acts as a central brain for customer intelligence, sales, and relationship management. It captures, remembers, organizes, and intelligently uses everything a business knows about its customers, then uses AI to communicate, assist, and sell on behalf of the business.

## User Personas
1. **Business Owner (Charu)** - Primary user who manages customer relationships and needs AI assistance for sales
2. **Sales Staff** - Team members who interact with customers via WhatsApp
3. **Customers** - End users communicating via WhatsApp

## Core Requirements (Static)
- Customer profile management (individuals, companies, employees)
- Purchase history and device tracking
- WhatsApp integration for communication
- Multi-topic conversation handling
- AI-powered responses with persistent context
- Product/Services catalog with pricing
- Order and ticket management
- Human escalation system

## What's Been Implemented (February 2026)

### Backend (FastAPI + MongoDB)
- ✅ JWT Authentication (register/login)
- ✅ Customer CRUD operations
- ✅ Products/Services catalog with pricing
- ✅ Conversations & Topics management
- ✅ AI Chat integration (OpenAI GPT-5.2 via Emergent LLM Key)
- ✅ Orders with automatic ticket creation
- ✅ **WhatsApp integration (LIVE using Baileys library)**
- ✅ Dashboard statistics
- ✅ Settings management
- ✅ Seed data for demo
- ✅ Knowledge Base API (FAQs, Policies, Procedures)
- ✅ Escalation System (automatic escalation on authority-boundary triggers)
- ✅ Conversation Summaries API
- ✅ **Lead Injection API** - Owner can inject leads, AI handles outreach
- ✅ **Excluded Numbers API** - Silent monitoring (record but never reply)
- ✅ **AI Auto-Reply** - Automatic AI responses to incoming WhatsApp messages

### Frontend (React + Tailwind + Shadcn UI)
- ✅ Login/Register pages with light/dark theme
- ✅ Dashboard with key metrics
- ✅ Customer management page
- ✅ Conversations page with chat interface
- ✅ Products catalog page
- ✅ Orders & Tickets page (osTicket MOCKED)
- ✅ **WhatsApp connection page with LIVE QR code**
- ✅ **Lead Injection page** - Inject and track leads
- ✅ **Excluded Numbers page** - Manage silent monitoring
- ✅ Settings page with Owner Phone configuration
- ✅ Theme toggle (Neural Slate palette)

### WhatsApp Service (Node.js + Baileys) - **LIVE!**
- ✅ Express server running on port 3001
- ✅ **Baileys library - NO Chromium required!**
- ✅ **Real QR code generation - scan with your phone**
- ✅ Real-time message receiving
- ✅ Message sending capability
- ✅ Session persistence (auth stored in auth_info_baileys)
- ✅ Auto-reconnection on disconnect

### New Features (February 1, 2026)

#### 1. Owner-Initiated Lead Injection
**How it works:**
- Owner (Charu) can inject leads via:
  - **UI**: Use the Lead Injection page to enter customer name, phone, and product interest
  - **WhatsApp Command**: Send a message like "Customer name Rahul, number 9876543210 is asking for iPhone 15 Pro Max"

**System behavior:**
1. Creates or updates customer profile
2. Creates conversation and topic (Product Inquiry)
3. Sends outbound WhatsApp message to customer
4. AI takes over the sales conversation
5. Follows all rules (no discounts, escalate when unsure)

**API Endpoints:**
- `GET /api/leads` - List all injected leads
- `POST /api/leads/inject` - Inject new lead
- `PUT /api/leads/{id}/status` - Update lead status

#### 2. Number Exclusion (Silent Monitoring)
**How it works:**
- Mark specific phone numbers as "Excluded from Reply"
- Messages from excluded numbers are recorded but AI NEVER replies
- Use for dealers, vendors, internal contacts

**Data handling:**
- Messages still stored in `silent_messages` collection
- Searchable and auditable
- Can be used for analytics

**API Endpoints:**
- `GET /api/excluded-numbers` - List excluded numbers
- `POST /api/excluded-numbers` - Add number to exclusion list
- `DELETE /api/excluded-numbers/{id}` - Remove exclusion
- `GET /api/excluded-numbers/check/{phone}` - Check if number is excluded

### Integrations
- ✅ OpenAI GPT-5.2 (via Emergent LLM key) - WORKING
- ✅ **WhatsApp (LIVE - using Baileys, no Chromium needed)**
- ⚠️ osTicket (MOCKED - tickets stored locally)
- ⚠️ Payment Gateway (MOCKED)

## Technical Architecture
```
/app/
├── backend/
│   ├── server.py         # Main FastAPI app (~2000 lines)
│   ├── tests/            # API tests
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/AppLayout.js
│   │   │   └── ui/       # Shadcn UI components
│   │   ├── contexts/     # AuthContext, ThemeContext
│   │   └── pages/
│   │       ├── LeadsPage.js         # NEW
│   │       ├── ExcludedNumbersPage.js # NEW
│   │       └── ...
│   ├── package.json
│   └── .env
├── whatsapp-service/     # Node.js WhatsApp service (Baileys)
│   ├── index.js
│   ├── auth_info_baileys/
│   └── package.json
└── memory/
    └── PRD.md
```

## Key API Endpoints
- `/api/auth/{register, login, me}`
- `/api/dashboard/stats`
- `/api/ai/chat`
- `/api/kb`, `/api/escalations`, `/api/summaries`
- `/api/whatsapp/{status, qr, send, disconnect, reconnect, incoming}`
- `/api/customers`, `/api/products`, `/api/orders`, `/api/tickets`
- `/api/leads`, `/api/leads/inject` - **NEW**
- `/api/excluded-numbers`, `/api/excluded-numbers/check/{phone}` - **NEW**

## Test Credentials
- Email: demo@test.com
- Password: demo123

## WhatsApp Setup Instructions
1. Navigate to WhatsApp page in the app
2. A REAL QR code will be displayed
3. Open WhatsApp on your phone → Settings → Linked Devices → Link a Device
4. Scan the QR code
5. WhatsApp is now connected! Messages will flow automatically

## Lead Injection Command Formats
From owner's WhatsApp (set Owner Phone in Settings):
```
Customer name Rahul, number 9876543210 is asking for iPhone 15 Pro Max
Lead: Priya - 8765432109 - wants MacBook Air
inject Amit 9988776655 iPad Pro
```

## Prioritized Backlog

### P0 - Critical
- [x] ~~Real WhatsApp integration~~ **DONE with Baileys!**
- [x] ~~Lead Injection~~ **DONE!**
- [x] ~~Number Exclusion~~ **DONE!**
- [ ] Real osTicket API integration

### P1 - High Priority
- [ ] Historical message sync on WhatsApp connect
- [ ] Payment gateway integration (Stripe/Razorpay)
- [ ] Follow-up automation
- [ ] Reseller/Referral module

### P2 - Medium Priority
- [ ] Voice note transcription
- [ ] Image attachment analysis
- [ ] Advanced analytics dashboard
- [ ] Customer segmentation
- [ ] Bulk messaging

### P3 - Nice to Have
- [ ] Mobile app version
- [ ] API rate limiting
- [ ] Audit logs
- [ ] Multi-language support

## Known Limitations
1. **osTicket** - Integration is mocked, tickets are stored in MongoDB instead of osTicket.
2. **Payment Gateway** - Mocked, payment status must be updated manually.

## Changelog

### February 1, 2026 (Latest)
- **NEW**: Lead Injection feature - Owner can inject leads via UI or WhatsApp command
- **NEW**: Excluded Numbers (Silent Monitoring) - Record messages but never reply
- **NEW**: AI Auto-Reply on incoming WhatsApp messages
- **NEW**: Owner phone setting for WhatsApp lead injection commands
- Replaced whatsapp-web.js with Baileys library (no Chromium needed)
- Real QR code generation and scanning
- All tests passing (100% success rate)

### January 2026
- Initial MVP with FastAPI + React
- AI Chat integration with GPT-5.2
- Customer, Product, Order management
- Knowledge Base and Escalations
