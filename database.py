
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel
import os
from typing import Optional
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database = None

# Initialize database connection
async def get_database():
    if Database.client is None:
        mongo_url = os.environ.get('MONGO_URL')
        print(f"Mongo url {mongo_url}")
        if not mongo_url:
            # Fallback for production deployment
            mongo_url = "mongodb://localhost:27017"
            logger.warning("MONGO_URL not found, using fallback connection")
            
        try:
            Database.client = AsyncIOMotorClient(
                mongo_url,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,         # 10 second connection timeout
                maxPoolSize=50,                 # Connection pool size
                retryWrites=True               # Enable retry writes for Atlas
            )
            
            # Test the connection
            await Database.client.admin.command('ping')
            
            db_name = os.environ.get('DB_NAME', 'daakyi_compaas')
            Database.database = Database.client[db_name]
            
            # Create indexes
            await create_indexes()
            logger.info(f"Connected to MongoDB: {db_name}")
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            logger.warning("Application starting without database connection")
            # Don't raise exception to allow app to start in degraded mode
            Database.database = None
    
    return Database.database

async def close_database():
    if Database.client:
        Database.client.close()
        Database.client = None
        Database.database = None

async def create_indexes():
    """Create database indexes for optimal performance"""
    try:
        if Database.database is None:
            logger.warning("Database not available, skipping index creation")
            return
            
        db = Database.database
        
        # Users collection indexes
        await db.users.create_indexes([
            IndexModel("email", unique=True),
            IndexModel("session_token"),
            IndexModel("organization_id"),
            IndexModel("role")
        ])
        
        # MVP 1 Users collection indexes
        await db.mvp1_users.create_indexes([
            IndexModel("email", unique=True),
            IndexModel("session_token"),
            IndexModel("organization_id"),
            IndexModel("role"),
            IndexModel([("email", 1), ("organization_id", 1)], unique=True)
        ])
        
        # MVP 1 Organizations collection indexes
        await db.mvp1_organizations.create_indexes([
            IndexModel("name", unique=True),
            IndexModel("status"),
            IndexModel("subscription_tier")
        ])
        
        # MVP 1 Engagements collection indexes
        await db.mvp1_engagements.create_indexes([
            IndexModel("organization_id"),
            IndexModel("engagement_code", unique=True),
            IndexModel("status"),
            IndexModel("framework"),
            IndexModel("assigned_analysts"),
            IndexModel("assigned_auditors"),
            IndexModel("leadership_stakeholders"),
            IndexModel([("organization_id", 1), ("status", 1)])
        ])
        
        # MVP 1 Audit Logs collection indexes
        await db.mvp1_audit_logs.create_indexes([
            IndexModel("organization_id"),
            IndexModel("engagement_id"),
            IndexModel("action_type"),
            IndexModel("actor_id"),
            IndexModel("timestamp"),
            IndexModel([("organization_id", 1), ("timestamp", -1)])
        ])
        
        # Organizations collection indexes
        await db.organizations.create_indexes([
            IndexModel("name")
        ])
        
        # Assessments collection indexes
        await db.assessments.create_indexes([
            IndexModel("organization_id"),
            IndexModel("created_by"),
            IndexModel("status"),
            IndexModel("framework"),
            IndexModel([("organization_id", 1), ("status", 1)])
        ])
        
        # Control assessments collection indexes
        await db.control_assessments.create_indexes([
            IndexModel("assessment_id"),
            IndexModel("control_id"),
            IndexModel([("assessment_id", 1), ("control_id", 1)], unique=True),
            IndexModel("status"),
            IndexModel("assessor_id")
        ])
        
        # Evidence files collection indexes
        await db.evidence_files.create_indexes([
            IndexModel("assessment_id"),
            IndexModel("uploaded_by"),
            IndexModel("processing_status"),
            IndexModel([("assessment_id", 1), ("processing_status", 1)])
        ])
        
        # Reports collection indexes
        await db.assessment_reports.create_indexes([
            IndexModel("assessment_id"),
            IndexModel("generated_by"),
            IndexModel("report_type")
        ])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {str(e)}")
        # Don't raise exception to allow app to start

# Database helper functions
async def get_collection(collection_name: str):
    """Get a specific collection from the database"""
    db = await get_database()
    return db[collection_name]

# Common database operations
class DatabaseOperations:
    
    @staticmethod
    async def find_one(collection: str, filter_dict: dict, projection: dict = None):
        """Find a single document in collection"""
        try:
            db = await get_database()
            if db is None:
                logger.warning(f"Database unavailable for find_one in {collection}")
                return None
            result = await db[collection].find_one(filter_dict, projection)
            if result:
                # Convert ObjectId to string
                if '_id' in result:
                    result['_id'] = str(result['_id'])
            return result
        except Exception as e:
            logger.error(f"Database find_one error in {collection}: {str(e)}")
            return None
    
    @staticmethod
    async def find_many(collection: str, filter_dict: dict = None, projection: dict = None, limit: int = None, sort: list = None, skip: int = None):
        """Find multiple documents in collection"""
        try:
            db = await get_database()
            if db is None:
                logger.warning(f"Database unavailable for find_many in {collection}")
                return []
            cursor = db[collection].find(filter_dict or {}, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
                
            results = await cursor.to_list(length=limit)
            # Convert ObjectIds to strings
            for result in results:
                if '_id' in result:
                    result['_id'] = str(result['_id'])
            return results
        except Exception as e:
            logger.error(f"Database find_many error in {collection}: {str(e)}")
            return []
    
    @staticmethod
    async def insert_one(collection: str, document: dict):
        """Insert a single document"""
        try:
            db = await get_database()
            if db is None:
                logger.warning(f"Database unavailable for insert_one in {collection}")
                return None
            result = await db[collection].insert_one(document)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Database insert_one error in {collection}: {str(e)}")
            return None
    
    @staticmethod
    async def insert_many(collection: str, documents: list):
        """Insert multiple documents"""
        try:
            db = await get_database()
            if db is None:
                logger.warning(f"Database unavailable for insert_many in {collection}")
                return None
            result = await db[collection].insert_many(documents)
            return result.inserted_ids
        except Exception as e:
            logger.error(f"Database insert_many error in {collection}: {str(e)}")
            return None
    
    @staticmethod
    async def update_one(collection: str, filter_dict: dict, update_dict: dict, upsert: bool = False):
        """Update a single document"""
        try:
            db = await get_database()
            if db is None:
                logger.warning(f"Database unavailable for update_one in {collection}")
                return 0
            result = await db[collection].update_one(filter_dict, {"$set": update_dict}, upsert=upsert)
            return result.modified_count
        except Exception as e:
            logger.error(f"Database update_one error in {collection}: {str(e)}")
            return 0
    
    @staticmethod
    async def update_many(collection: str, filter_dict: dict, update_dict: dict):
        """Update multiple documents"""
        db = await get_database()
        result = await db[collection].update_many(filter_dict, {"$set": update_dict})
        return result.modified_count
    
    @staticmethod
    async def delete_one(collection: str, filter_dict: dict):
        """Delete a single document"""
        db = await get_database()
        result = await db[collection].delete_one(filter_dict)
        return result.deleted_count
    
    @staticmethod
    async def delete_many(collection: str, filter_dict: dict):
        """Delete multiple documents"""
        db = await get_database()
        result = await db[collection].delete_many(filter_dict)
        return result.deleted_count
    
    @staticmethod
    async def count_documents(collection: str, filter_dict: dict = None):
        """Count documents in collection"""
        try:
            db = await get_database()
            if db is None:
                logger.warning(f"Database unavailable for count_documents in {collection}")
                return 0
            return await db[collection].count_documents(filter_dict or {})
        except Exception as e:
            logger.error(f"Database count_documents error in {collection}: {str(e)}")
            return 0
    
    @staticmethod
    async def aggregate(collection: str, pipeline: list):
        """Run aggregation pipeline"""
        db = await get_database()
        cursor = db[collection].aggregate(pipeline)
        return await cursor.to_list(length=None)