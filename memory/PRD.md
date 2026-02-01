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

## What's Been Implemented (January 2026)

### Backend (FastAPI + MongoDB)
- ✅ JWT Authentication (register/login)
- ✅ Customer CRUD operations
- ✅ Products/Services catalog with pricing
- ✅ Conversations & Topics management
- ✅ AI Chat integration (OpenAI GPT-5.2 via Emergent)
- ✅ Orders with automatic ticket creation
- ✅ WhatsApp simulation endpoints
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
- ✅ WhatsApp connection page (QR scan MOCKED)
- ✅ Settings page
- ✅ Theme toggle (Neural Slate palette)

### Integrations
- ✅ OpenAI GPT-5.2 (via Emergent LLM key)
- ⏳ WhatsApp (MOCKED - QR scan simulation)
- ⏳ osTicket (MOCKED)
- ⏳ Payment Gateway (MOCKED)

### AI Response Guidelines Implemented
- Context loading before every response
- Knowledge Base consultation for accurate answers
- Authority limits enforced (no discounts, no delivery promises)
- Automatic escalation for sensitive requests
- Multi-topic detection in messages

## Prioritized Backlog

### P0 - Critical
- [ ] Real WhatsApp Web.js integration (replace mock)
- [ ] Real osTicket API integration
- [ ] Multi-topic conversation parsing
- [ ] Escalation notification system

### P1 - High Priority
- [ ] Customer purchase history tracking
- [ ] Device ownership management
- [ ] Payment gateway integration (Razorpay)
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

## Technical Architecture
- **Frontend**: React 19, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Motor (async MongoDB)
- **Database**: MongoDB
- **AI**: OpenAI GPT-5.2 via Emergent Integrations
- **Authentication**: JWT
- **Deployment**: Kubernetes (Emergent Platform)

## Next Steps
1. Implement real WhatsApp Web.js integration
2. Connect osTicket API
3. Add multi-topic parsing logic
4. Implement escalation notifications to Charu's phone
