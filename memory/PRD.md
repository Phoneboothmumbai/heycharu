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
- ✅ Conversation Summaries API (structured summaries generation)
- ✅ Enhanced AI with Rules

### Frontend (React + Tailwind + Shadcn UI)
- ✅ Login/Register pages with light/dark theme
- ✅ Dashboard with key metrics
- ✅ Customer management page
- ✅ Conversations page with chat interface
- ✅ Products catalog page
- ✅ Orders & Tickets page (osTicket MOCKED)
- ✅ **WhatsApp connection page with LIVE QR code**
- ✅ Settings page
- ✅ Theme toggle (Neural Slate palette)

### WhatsApp Service (Node.js + Baileys) - **LIVE!**
- ✅ Express server running on port 3001
- ✅ **Baileys library - NO Chromium required!**
- ✅ **Real QR code generation - scan with your phone**
- ✅ Real-time message receiving
- ✅ Message sending capability
- ✅ Session persistence (auth stored in auth_info_baileys)
- ✅ Auto-reconnection on disconnect
- ✅ Message forwarding to backend

### Integrations
- ✅ OpenAI GPT-5.2 (via Emergent LLM key) - WORKING
- ✅ **WhatsApp (LIVE - using Baileys, no Chromium needed)**
- ⚠️ osTicket (MOCKED - tickets stored locally)
- ⚠️ Payment Gateway (MOCKED)

## Technical Architecture
```
/app/
├── backend/
│   ├── server.py         # Main FastAPI app
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
├── whatsapp-service/     # Node.js WhatsApp service (Baileys)
│   ├── index.js          # LIVE WhatsApp implementation
│   ├── auth_info_baileys/ # Session storage
│   └── package.json
└── memory/
    └── PRD.md
```

## Key API Endpoints
- `/api/auth/{register, login, me}`
- `/api/dashboard/stats`
- `/api/ai/chat`
- `/api/kb`, `/api/escalations`, `/api/summaries`
- `/api/whatsapp/{status, qr, send, disconnect, reconnect, incoming, sync-messages}`
- `/api/customers`, `/api/products`, `/api/orders`, `/api/tickets`

## Test Credentials
- Email: demo@test.com
- Password: demo123

## WhatsApp Setup Instructions
1. Navigate to WhatsApp page in the app
2. A REAL QR code will be displayed
3. Open WhatsApp on your phone → Settings → Linked Devices → Link a Device
4. Scan the QR code
5. WhatsApp is now connected! Messages will flow automatically

## Prioritized Backlog

### P0 - Critical
- [x] ~~Real WhatsApp integration~~ **DONE with Baileys!**
- [ ] Real osTicket API integration
- [ ] Multi-topic conversation parsing

### P1 - High Priority
- [ ] Historical message sync on WhatsApp connect
- [ ] Customer purchase history tracking
- [ ] Device ownership management
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

### February 1, 2026
- Replaced whatsapp-web.js with Baileys library
- WhatsApp now works WITHOUT Chromium browser
- Real QR code generation and scanning
- Real-time message receiving and sending
- Auto-reconnection support

### January 2026
- Initial MVP with FastAPI + React
- AI Chat integration with GPT-5.2
- Customer, Product, Order management
- Knowledge Base and Escalations
