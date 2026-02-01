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

### WhatsApp Integration (LIVE - Baileys)
- ✅ Real QR code scanning (no Chromium needed)
- ✅ Real-time message receiving
- ✅ Message sending capability
- ✅ Session persistence
- ✅ AI auto-reply on incoming messages

### Lead Injection (NEW)
- ✅ Owner can inject leads via UI
- ✅ Owner can inject leads via WhatsApp command
- ✅ AI creates customer, conversation, topic
- ✅ AI sends first outbound message
- ✅ Lead tracking with status

### Number Exclusion - Silent Monitoring (NEW)
- ✅ Mark numbers as excluded (dealer, vendor, internal)
- ✅ Messages recorded but AI NEVER replies
- ✅ Searchable audit trail
- ✅ Category tagging

### Auto-Messaging System (NEW)
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
- ✅ Conversations
- ✅ Products
- ✅ Orders
- ✅ WhatsApp Connection
- ✅ Lead Injection (NEW)
- ✅ Excluded Numbers (NEW)
- ✅ Auto-Messages (NEW)
- ✅ Settings

## Test Credentials
- Email: demo@test.com
- Password: demo123

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
- [ ] Real osTicket API integration

### P1 - High Priority
- [ ] Background scheduler for follow-ups
- [ ] Historical message sync on WhatsApp connect
- [ ] Payment gateway (Stripe/Razorpay)
- [ ] Escalation notifications to owner's WhatsApp

### P2 - Medium Priority
- [ ] Reseller/Referral module
- [ ] Voice note transcription
- [ ] Image attachment analysis
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

## Changelog

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
