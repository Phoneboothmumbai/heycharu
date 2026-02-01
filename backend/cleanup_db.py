#!/usr/bin/env python3
"""
Database cleanup script - Run this to clear all customer/conversation data
Usage: python3 cleanup_db.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def clean_all():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["salesbrain"]
    
    print("=== CLEANING salesbrain DATABASE ===\n")
    
    # Collections to DELETE completely
    delete_collections = [
        "customers",
        "conversations", 
        "messages",
        "topics",
        "orders",
        "tickets",
        "escalations",
        "silent_messages",
        "lead_injections",
        "auto_messages_sent"
    ]
    
    for coll in delete_collections:
        try:
            result = await db[coll].delete_many({})
            print(f"Deleted {result.deleted_count} from {coll}")
        except Exception as e:
            print(f"Error deleting {coll}: {e}")
    
    print("\n=== DONE ===")
    print("Kept: users, settings, products, knowledge_base")
    print("Deleted: all customer and conversation data")
    print("\nSend a WhatsApp message to create fresh data.")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(clean_all())
