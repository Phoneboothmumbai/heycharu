#!/usr/bin/env python3
"""
FULL DATABASE DIAGNOSTIC AND CLEANUP
Run: python3 full_cleanup.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def full_cleanup():
    # Try multiple MongoDB URLs
    mongo_urls = [
        os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
        "mongodb://localhost:27017",
        "mongodb://127.0.0.1:27017"
    ]
    
    for mongo_url in mongo_urls:
        print(f"\n{'='*60}")
        print(f"TRYING: {mongo_url}")
        print('='*60)
        
        try:
            client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
            
            # List all databases
            dbs = await client.list_database_names()
            print(f"\nFound databases: {dbs}")
            
            for db_name in dbs:
                if db_name in ['admin', 'local', 'config']:
                    continue
                
                db = client[db_name]
                
                # Count documents in each collection
                collections = await db.list_collection_names()
                has_data = False
                
                for coll in collections:
                    count = await db[coll].count_documents({})
                    if count > 0:
                        has_data = True
                        print(f"\n  [{db_name}].{coll}: {count} documents")
                
                if has_data:
                    print(f"\n  >>> CLEANING {db_name}...")
                    
                    # Delete from all collections except users/settings/products
                    keep = ['users', 'settings', 'products', 'knowledge_base', 'excluded_numbers', 'auto_message_settings']
                    
                    for coll in collections:
                        if coll not in keep:
                            result = await db[coll].delete_many({})
                            if result.deleted_count > 0:
                                print(f"      Deleted {result.deleted_count} from {coll}")
                    
                    print(f"  >>> {db_name} CLEANED!")
            
            client.close()
            
        except Exception as e:
            print(f"Error with {mongo_url}: {e}")
    
    print(f"\n{'='*60}")
    print("CLEANUP COMPLETE!")
    print("Restart services with: pm2 restart all")
    print('='*60)

if __name__ == "__main__":
    asyncio.run(full_cleanup())
