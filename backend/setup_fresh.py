#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def setup():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    
    print("1. Dropping test_database...")
    await client.drop_database("test_database")
    
    print("2. Cleaning salesbrain...")
    db = client["salesbrain"]
    await db.customers.delete_many({})
    await db.conversations.delete_many({})
    await db.messages.delete_many({})
    await db.topics.delete_many({})
    await db.orders.delete_many({})
    await db.tickets.delete_many({})
    await db.escalations.delete_many({})
    await db.lead_injections.delete_many({})
    await db.silent_messages.delete_many({})
    await db.auto_messages_sent.delete_many({})
    
    print("3. Done! Fresh start ready.")
    client.close()

asyncio.run(setup())
