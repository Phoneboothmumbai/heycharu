# Sales Brain - AI-Powered Customer Intelligence Platform

## Product Overview
Sales Brain is a SaaS platform that acts as a central brain for customer intelligence, sales, and relationship management. It captures, remembers, organizes, and intelligently uses everything a business knows about its customers, then uses AI to communicate, assist, and sell on behalf of the business.

## What's Been Implemented (February 2026)

### Core Features
- ✅ JWT Authentication (register/login)
- ✅ Customer CRUD operations with profiles
- ✅ Products/Services catalog with pricing
- ✅ Conversations & Topics management
- ✅ AI Chat integration (OpenAI GPT-5.2 via Emergent LLM Key)
- ✅ Orders with automatic ticket creation
- ✅ Dashboard statistics
- ✅ Knowledge Base (FAQs, Policies)
- ✅ Escalation System

### Unanswered Questions Page (NEW - Feb 2026)
Dashboard to manage questions the AI couldn't answer:

**Features:**
- ✅ View all escalated/unanswered questions
- ✅ Stats cards: Pending, Overdue, Resolved, Irrelevant counts
- ✅ Filter by status (Pending, Resolved, Irrelevant, All)
- ✅ Unique Escalation Codes (ESC01, ESC02, ESC03...)
- ✅ Status badges: WAITING (orange), OVERDUE (red), RESOLVED (green)
- ✅ **Add KB Article** - Create new knowledge base article to answer the question
- ✅ **Link KB/Excel** - Search and link existing KB articles or product data
- ✅ **Mark Irrelevant** - Mark spam/irrelevant questions

**API Endpoints:**
- `GET /api/unanswered-questions` - List with filters (status, relevance)
- `PUT /api/unanswered-questions/{id}/relevance` - Mark relevant/irrelevant
- `POST /api/unanswered-questions/{id}/add-kb-article` - Create & link KB article
- `POST /api/unanswered-questions/{id}/link-kb-article/{kb_id}` - Link existing KB
- `POST /api/unanswered-questions/{id}/link-excel-data` - Search KB/products/Excel

### Multiple Escalation Thread Mapping (NEW - Feb 2026)
Strict one-to-one mapping between customer questions and owner replies:

**Escalation ID System:**
- Unique codes: ESC01, ESC02, ESC03... (auto-incrementing)
- Sent to owner with each escalation message
- Owner must reply with format: `ESC01: your answer here`

**Thread Mapping Rules:**
- Each question → own escalation ID
- Each escalation ID → mapped to specific owner reply
- No ID match = no response sent to customer
- If multiple pending escalations, owner must specify which one

**Example Owner WhatsApp Flow:**
```
🚨 *ESC01* - Need Your Input
Customer: John Doe
Phone: 9876543210
Question: "Do you have iPhone 15 Pro Max in stock?"
---
Reply with: *ESC01: your answer*
```
Owner replies: `ESC01: Yes, we have it for ₹1,39,900`
AI polishes and sends to customer.

### 4-Part AI Control System (NEW - Feb 2026)
Complete AI conversation control with strict decision logic:

1. **Context Fetch** - AI loads customer profile, conversation history, KB articles, and product catalog
2. **Decision Logic** - AI uses ONLY verified sources (KB + Products), NO guessing allowed
3. **Escalation with SLA** - If info not found, AI says "Let me check..." and escalates to owner with 30-min SLA timer
4. **Reply Polishing** - When owner replies, AI polishes the response (grammar/tone) and sends to customer

**Conversation Status Labels:**
- `ACTIVE` (Green) - Normal conversation, AI is handling
- `WAITING` (Orange) - Escalated, waiting for owner response
- `OVERDUE` (Red) - Past 30-min SLA deadline

**SLA Timer Features:**
- 30-minute deadline for owner replies
- Auto-reminders via WhatsApp + Dashboard (up to 3 reminders)
- Visual status indicators in Conversations page

**API Endpoints:**
- `GET /api/escalations/pending-sla` - Get pending escalations with SLA status
- `POST /api/escalations/check-sla` - Trigger SLA check and send reminders

### Customer 360° Cover View
- ✅ Comprehensive single-page customer dashboard
- ✅ Customer header with avatar, name, type badge, contact info
- ✅ Total Lifetime Value display
- ✅ Statistics row (Total Orders, Active Topics, Delivered, Conversations)
- ✅ Topics tab: Active and Resolved topics
- ✅ Orders tab: Full order history with status badges
- ✅ Devices tab: Customer devices with Add/Remove functionality
- ✅ Notes tab: Customer tags (add/remove) + Internal notes (edit/save)
- ✅ Shows Lead Injection info and Silent Monitoring status
- ✅ Navigation from customers list via row click or View 360° button

**API Endpoints:**
- `GET /api/customers/{id}/360` - Get comprehensive customer data
- `PUT /api/customers/{id}/notes` - Update internal notes
- `PUT /api/customers/{id}/tags` - Update customer tags
- `POST /api/customers/{id}/devices` - Add device
- `DELETE /api/customers/{id}/devices/{index}` - Remove device

### WhatsApp Integration (LIVE - Baileys)
- ✅ Real QR code scanning (no Chromium needed)
- ✅ Real-time message receiving
- ✅ Message sending capability
- ✅ Session persistence
- ✅ AI auto-reply on incoming messages

### Lead Injection
- ✅ Owner can inject leads via UI
- ✅ Owner can inject leads via WhatsApp command
- ✅ AI creates customer, conversation, topic
- ✅ AI sends first outbound message
- ✅ Lead tracking with status

### Number Exclusion - Silent Monitoring
- ✅ Mark numbers as excluded (dealer, vendor, internal)
- ✅ Messages recorded but AI NEVER replies
- ✅ Searchable audit trail
- ✅ Category tagging

### Auto-Messaging System
Trigger-based, permission-controlled automated messages with full anti-spam controls.

**Implemented Triggers:**
1. ✅ **Order Confirmed** - Sent when order is placed
2. ✅ **Payment Received** - Sent when payment marked as received
3. ✅ **Order Completed** - Sent when order status is "delivered"
4. ✅ **Ticket Created** - Sent when support ticket is created
5. ✅ **Ticket Updated** - Sent when ticket status changes to in_progress
6. ✅ **Ticket Resolved** - Sent when ticket is resolved/closed
7. ✅ **AI Uncertain** - Fallback message when AI confidence is low
8. ✅ **No Response Follow-up** - Configurable (default: 2 days)

**Anti-Spam Controls:**
- ✅ Max messages per topic (default: 3)
- ✅ Cooldown period between messages (default: 24h)
- ✅ Do Not Disturb window (default: 9 PM - 9 AM)
- ✅ Excluded numbers list integration
- ✅ Manual override capability

**API Endpoints:**
- `GET /api/auto-messages/settings` - Get settings
- `PUT /api/auto-messages/settings` - Update settings
- `GET /api/auto-messages/templates` - Get templates
- `PUT /api/auto-messages/templates/{trigger_type}` - Update template
- `GET /api/auto-messages/history` - View sent messages
- `GET /api/auto-messages/scheduled` - View scheduled messages
- `DELETE /api/auto-messages/scheduled/{id}` - Cancel scheduled
- `POST /api/auto-messages/schedule-follow-up` - Manually schedule

### Frontend Pages
- ✅ Dashboard
- ✅ Customers
- ✅ Conversations (with status badges)
- ✅ Products
- ✅ Orders
- ✅ WhatsApp Connection
- ✅ Lead Injection
- ✅ Excluded Numbers
- ✅ Auto-Messages
- ✅ Settings

## Test Credentials
- Email: test@test.com
- Password: test123

## WhatsApp Command Formats
From owner's phone (set Owner Phone in Settings):
```
Customer name Rahul, number 9876543210 is asking for iPhone 15 Pro Max
Lead: Priya - 8765432109 - wants MacBook Air
inject Amit 9988776655 iPad Pro
```

## Default Message Templates
```
no_response: "Just checking in — let me know if you need any help with {topic}."
order_confirmed: "Thanks for confirming your order! I'm sharing the payment details below. Total: ₹{amount}"
payment_received: "Payment received ✓ We'll update you once the order is processed."
order_completed: "Your order has been completed. Let us know if you need anything else!"
ticket_created: "We've created a support ticket for this. Ticket ID: #{ticket_id}"
ticket_resolved: "This issue has been resolved. Please let us know if you face it again."
ai_uncertain: "Let me check this and get back to you shortly."
```

## Prioritized Backlog

### P0 - Critical
- [x] ~~Real WhatsApp~~ DONE
- [x] ~~Lead Injection~~ DONE
- [x] ~~Number Exclusion~~ DONE
- [x] ~~Auto-Messaging MVP~~ DONE
- [x] ~~Customer 360° Cover View~~ DONE
- [x] ~~4-Part AI Control System~~ DONE
- [ ] Real osTicket API integration

### P1 - High Priority
- [ ] Image Understanding (GPT-4 Vision / Gemini Vision)
- [ ] Background scheduler for follow-ups
- [ ] Historical message sync on WhatsApp connect
- [ ] Payment gateway (Stripe/Razorpay)

### P2 - Medium Priority
- [ ] Reseller/Referral module
- [ ] Voice note transcription
- [ ] Advanced analytics
- [ ] Warranty/AMC reminders
- [ ] Owner-triggered broadcasts

### P3 - Nice to Have
- [ ] Mobile app
- [ ] Multi-language support
- [ ] Audit logs

## Known Limitations
1. **osTicket** - Mocked (tickets in MongoDB)
2. **Payment Gateway** - Mocked
3. **Follow-up Scheduler** - Manual only (no background job yet)
4. **WhatsApp** - Requires QR scan to connect in preview

## Changelog

### February 2, 2026 (Session 4)
- **NEW**: 4-Part AI Control System implemented
  - Context fetch from customer profile, KB, product catalog
  - Strict decision tree (no AI guessing)
  - Owner escalation with 30-min SLA timer
  - AI reply polishing when owner responds
- **NEW**: Conversation status labels (ACTIVE, WAITING, OVERDUE)
- **NEW**: SLA check endpoints for dashboard monitoring
- **FIX**: Fixed babel-metadata-plugin infinite recursion issue

### February 1, 2026 (Session 3)
- **NEW**: Customer 360° Cover View - comprehensive single-page customer dashboard
- Shows customer header, stats, topics, orders, devices, tags, notes
- Integrated with Lead Injection and Silent Monitoring status
- Navigation from customers list via row click or View 360° button

### February 1, 2026 (Session 2)
- **NEW**: Auto-Messaging system with triggers for orders, payments, tickets
- **NEW**: Anti-spam controls (cooldown, DND, max per topic)
- **NEW**: Message templates with variable substitution
- **NEW**: Auto-message history and scheduled messages management
- **NEW**: Auto-reply on incoming WhatsApp (AI-powered)

### February 1, 2026 (Session 1)
- Lead Injection feature
- Excluded Numbers (Silent Monitoring)
- WhatsApp integration with Baileys (no Chromium)
- Real QR code scanning
