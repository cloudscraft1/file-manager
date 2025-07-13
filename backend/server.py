from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
from appwrite.client import Client
from appwrite.services.storage import Storage
from appwrite.input_file import InputFile
from appwrite.id import ID
import io


ROOT_DIR = Path(__file__).parent
# Load .env file from the current directory (works both locally and in Docker)
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Appwrite configuration
def init_appwrite() -> Storage:
    appwrite_client = Client()
    appwrite_client.set_endpoint(os.getenv("APPWRITE_ENDPOINT"))
    appwrite_client.set_project(os.getenv("APPWRITE_PROJECT_ID"))
    appwrite_client.set_key(os.getenv("APPWRITE_API_KEY"))
    return Storage(appwrite_client)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class FileMetadata(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    appwrite_file_id: str
    original_name: str
    file_size: int
    mime_type: str
    uploaded_by: Optional[str] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    tags: Optional[List[str]] = []
    description: Optional[str] = None

class FileMetadataResponse(BaseModel):
    id: str
    appwrite_file_id: str
    original_name: str
    file_size: int
    mime_type: str
    uploaded_by: Optional[str] = None
    upload_date: datetime
    tags: Optional[List[str]] = []
    description: Optional[str] = None

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Existing endpoints
@api_router.get("/")
async def root():
    return {"message": "File Manager API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# File management endpoints
@api_router.post("/files/upload", response_model=FileMetadataResponse)
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to Appwrite
        storage = init_appwrite()
        file_id = ID.unique()
        
        # Use InputFile.from_bytes for Appwrite
        input_file = InputFile.from_bytes(file_content, filename=file.filename)
        
        result = storage.create_file(
            bucket_id=os.getenv("APPWRITE_BUCKET_ID"),
            file_id=file_id,
            file=input_file
        )
        
        # Create metadata
        metadata = FileMetadata(
            appwrite_file_id=result["$id"],
            original_name=file.filename,
            file_size=result["sizeOriginal"],
            mime_type=file.content_type or "application/octet-stream"
        )
        
        # Save metadata to MongoDB
        result_db = await db.file_metadata.insert_one(metadata.dict())
        
        # Return response
        return FileMetadataResponse(**metadata.dict())
    except Exception as e:
        logging.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.get("/files/list")
async def list_files():
    try:
        files = await db.file_metadata.find().to_list(1000)
        for file in files:
            # Convert ObjectId to string if present
            if "_id" in file:
                del file["_id"]
        return {"files": files}
    except Exception as e:
        logging.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@api_router.get("/files/download/{file_id}")
async def download_file(file_id: str):
    try:
        # Get metadata from MongoDB
        metadata = await db.file_metadata.find_one({"appwrite_file_id": file_id})
        if not metadata:
            raise HTTPException(status_code=404, detail="File metadata not found")
        
        # Download from Appwrite
        storage = init_appwrite()
        file_data = storage.get_file_download(
            bucket_id=os.getenv("APPWRITE_BUCKET_ID"),
            file_id=file_id
        )
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=metadata["mime_type"],
            headers={"Content-Disposition": f"attachment; filename={metadata['original_name']}"}
        )
    except Exception as e:
        logging.error(f"Download failed: {str(e)}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")

@api_router.delete("/files/delete/{file_id}")
async def delete_file(file_id: str):
    try:
        # Delete from Appwrite
        storage = init_appwrite()
        storage.delete_file(
            bucket_id=os.getenv("APPWRITE_BUCKET_ID"),
            file_id=file_id
        )
        
        # Delete metadata from MongoDB
        result = await db.file_metadata.delete_one({"appwrite_file_id": file_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="File metadata not found")
        
        return {"message": "File deleted successfully"}
    except Exception as e:
        logging.error(f"Delete failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deletion error: {str(e)}")

@api_router.get("/files/info/{file_id}")
async def get_file_info(file_id: str):
    try:
        # Get metadata from MongoDB
        metadata = await db.file_metadata.find_one({"appwrite_file_id": file_id})
        if not metadata:
            raise HTTPException(status_code=404, detail="File metadata not found")
        
        if "_id" in metadata:
            del metadata["_id"]
        
        return metadata
    except Exception as e:
        logging.error(f"Error getting file info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting file info: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()