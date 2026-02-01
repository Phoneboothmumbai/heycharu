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
- ✅ WhatsApp integration endpoints (simulation mode for preview)
- ✅ Dashboard statistics
- ✅ Settings management
- ✅ Seed data for demo
- ✅ **Knowledge Base API** (FAQs, Policies, Procedures)
- ✅ **Escalation System** (automatic escalation on authority-boundary triggers)
- ✅ **Conversation Summaries API** (structured summaries generation)
- ✅ **Enhanced AI with Rules**:
  - Context-First Rule (loads customer profile before responding)
  - No Assumptions Rule (asks clarifying questions)
  - No Repetition Rule (uses stored data)
  - Authority Boundary Rule (escalates discount/delivery requests)
  - Professional tone enforcement

### Frontend (React + Tailwind + Shadcn UI)
- ✅ Login/Register pages with light/dark theme
- ✅ Dashboard with key metrics
- ✅ Customer management page
- ✅ Conversations page with chat interface
- ✅ Products catalog page
- ✅ Orders & Tickets page (osTicket MOCKED)
- ✅ WhatsApp connection page (QR code with simulation)
- ✅ Settings page
- ✅ Theme toggle (Neural Slate palette)

### WhatsApp Service (Node.js)
- ✅ Express server running on port 3001
- ✅ Preview mode with mock QR code generation
- ✅ Status, connect, disconnect endpoints
- ✅ Message simulation support
- ⚠️ Real WhatsApp (via whatsapp-web.js) requires Chromium - only works in production

### Integrations
- ✅ OpenAI GPT-5.2 (via Emergent LLM key) - WORKING
- ⚠️ WhatsApp (PREVIEW MODE - QR scan simulation in preview environment)
- ⚠️ osTicket (MOCKED - tickets stored locally)
- ⚠️ Payment Gateway (MOCKED)

## Fixed Issues (February 2026)
1. ✅ Removed duplicate `simulate-message` endpoint in server.py
2. ✅ Fixed dead code in WhatsApp routes
3. ✅ Created WhatsApp service with preview mode support
4. ✅ Added supervisor configuration for WhatsApp service
5. ✅ Backend passes `previewMode` flag to frontend

## Technical Architecture
```
/app/
├── backend/
│   ├── server.py         # Main FastAPI app (1400+ lines)
│   ├── tests/            # API tests
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/AppLayout.js
│   │   │   └── ui/       # Shadcn UI components
│   │   ├── contexts/     # AuthContext, ThemeContext
│   │   └── pages/        # React pages
│   ├── package.json
│   └── .env
├── whatsapp-service/     # Node.js WhatsApp service
│   ├── index.js          # Preview mode implementation
│   └── package.json
└── memory/
    └── PRD.md
```

## Key API Endpoints
- `/api/auth/{register, login, me}`
- `/api/dashboard/stats`
- `/api/ai/chat`
- `/api/kb`, `/api/escalations`, `/api/summaries`
- `/api/whatsapp/{status, qr, simulate-message, send, disconnect, reconnect}`
- `/api/customers`, `/api/products`, `/api/orders`, `/api/tickets`

## Test Credentials
- Email: demo@test.com
- Password: demo123

## Prioritized Backlog

### P0 - Critical (for Production)
- [ ] Deploy to production for real WhatsApp Web.js integration (requires Chromium)
- [ ] Real osTicket API integration
- [ ] Multi-topic conversation parsing

### P1 - High Priority
- [ ] Customer purchase history tracking
- [ ] Device ownership management
- [ ] Payment gateway integration (Stripe/Razorpay)
- [ ] Follow-up automation
- [ ] Reseller/Referral module
- [ ] Historical message sync on WhatsApp connect

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

## Known Limitations in Preview
1. **WhatsApp Web.js** - Requires Chromium browser which cannot run in the K8s preview environment. Works in production deployment.
2. **osTicket** - Integration is mocked, tickets are stored in MongoDB instead of osTicket.
3. **Payment Gateway** - Mocked, payment status must be updated manually.

## Next Steps
1. Deploy to production environment for real WhatsApp functionality
2. Connect osTicket API
3. Add multi-topic parsing logic
4. Implement escalation notifications to Charu's phone
