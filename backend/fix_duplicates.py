#!/usr/bin/env python3
"""
Script to merge duplicate conversations for the same phone number.
Run this on your server: python3 fix_duplicates.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "sales_brain")

async def fix_duplicates():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("Connecting to MongoDB...")
    
    # Find all conversations
    convs = await db.conversations.find({}).to_list(1000)
    print(f"Found {len(convs)} total conversations")
    
    # Group by phone (last 10 digits)
    by_phone = {}
    for c in convs:
        phone = c.get("customer_phone", "").replace("+", "").replace(" ", "").replace("-", "")
        if len(phone) >= 10:
            key = phone[-10:]
            if key not in by_phone:
                by_phone[key] = []
            by_phone[key].append(c)
    
    # Find duplicates
    fixed = 0
    for phone, conv_list in by_phone.items():
        if len(conv_list) > 1:
            print(f"\n=== Phone ...{phone} has {len(conv_list)} duplicate conversations ===")
            
            # Find the one with most messages
            best = None
            best_count = -1
            
            for c in conv_list:
                msg_count = await db.messages.count_documents({"conversation_id": c["id"]})
                print(f"  Conv {c['id'][:8]}...: {msg_count} messages, last: {c.get('last_message', '')[:30]}")
                if msg_count > best_count:
                    best_count = msg_count
                    best = c
            
            # Merge all messages into the best conversation
            if best:
                print(f"  -> KEEPING: {best['id'][:8]}... (has {best_count} messages)")
                
                for c in conv_list:
                    if c["id"] != best["id"]:
                        # Move messages from this conv to best
                        result = await db.messages.update_many(
                            {"conversation_id": c["id"]},
                            {"$set": {"conversation_id": best["id"]}}
                        )
                        print(f"  -> Moved {result.modified_count} messages from {c['id'][:8]}...")
                        
                        # Move topics too
                        await db.topics.update_many(
                            {"conversation_id": c["id"]},
                            {"$set": {"conversation_id": best["id"]}}
                        )
                        
                        # Delete the duplicate conversation
                        await db.conversations.delete_one({"id": c["id"]})
                        print(f"  -> DELETED conversation {c['id'][:8]}...")
                        fixed += 1
    
    # Also fix duplicate customers
    print("\n\n=== Checking for duplicate customers ===")
    customers = await db.customers.find({}).to_list(1000)
    by_phone_cust = {}
    for c in customers:
        phone = c.get("phone", "").replace("+", "").replace(" ", "").replace("-", "")
        if len(phone) >= 10:
            key = phone[-10:]
            if key not in by_phone_cust:
                by_phone_cust[key] = []
            by_phone_cust[key].append(c)
    
    for phone, cust_list in by_phone_cust.items():
        if len(cust_list) > 1:
            print(f"\n=== Phone ...{phone} has {len(cust_list)} duplicate customers ===")
            
            # Keep the oldest one (first created)
            cust_list.sort(key=lambda x: x.get("created_at", ""))
            best = cust_list[0]
            print(f"  -> KEEPING: {best['id'][:8]}... ({best.get('name')})")
            
            for c in cust_list[1:]:
                # Update all references to point to the best customer
                await db.conversations.update_many(
                    {"customer_id": c["id"]},
                    {"$set": {"customer_id": best["id"]}}
                )
                await db.topics.update_many(
                    {"customer_id": c["id"]},
                    {"$set": {"customer_id": best["id"]}}
                )
                await db.orders.update_many(
                    {"customer_id": c["id"]},
                    {"$set": {"customer_id": best["id"]}}
                )
                
                # Delete duplicate customer
                await db.customers.delete_one({"id": c["id"]})
                print(f"  -> DELETED customer {c['id'][:8]}... ({c.get('name')})")
                fixed += 1
    
    print(f"\n\n=== DONE! Fixed {fixed} duplicates ===")
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_duplicates())
