from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
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
# Load .env file from the current working directory at runtime
load_dotenv()

# Debug: Print environment variables
print(f"Environment variables loaded:")
print(f"MONGO_URL: {os.getenv('MONGO_URL')}")
print(f"DB_NAME: {os.getenv('DB_NAME')}")
print(f"APPWRITE_ENDPOINT: {os.getenv('APPWRITE_ENDPOINT')}")
print(f"APPWRITE_PROJECT_ID: {os.getenv('APPWRITE_PROJECT_ID')}")
print(f"APPWRITE_BUCKET_ID: {os.getenv('APPWRITE_BUCKET_ID')}")
print(f"ENV file path: {ROOT_DIR / '.env'}")
print(f"ENV file exists: {(ROOT_DIR / '.env').exists()}")

# MongoDB connection
try:
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    print(f"Successfully connected to MongoDB")
except KeyError as e:
    print(f"Missing environment variable: {e}")
    # Use fallback values or exit
    raise

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
    print(f"Upload request received for file: {file.filename}")
    print(f"File size: {file.size if hasattr(file, 'size') else 'unknown'}")
    print(f"Content type: {file.content_type}")
    
    try:
        # Debug: Check environment variables at upload time
        print(f"Checking environment variables during upload:")
        print(f"APPWRITE_ENDPOINT: {os.getenv('APPWRITE_ENDPOINT')}")
        print(f"APPWRITE_PROJECT_ID: {os.getenv('APPWRITE_PROJECT_ID')}")
        print(f"APPWRITE_BUCKET_ID: {os.getenv('APPWRITE_BUCKET_ID')}")
        print(f"APPWRITE_API_KEY exists: {bool(os.getenv('APPWRITE_API_KEY'))}")
        
        # Read file content
        print("Reading file content...")
        file_content = await file.read()
        print(f"File content read: {len(file_content)} bytes")
        
        # Upload to Appwrite
        print("Initializing Appwrite storage...")
        storage = init_appwrite()
        file_id = ID.unique()
        print(f"Generated file ID: {file_id}")
        
        # Use InputFile.from_bytes for Appwrite
        print("Creating InputFile...")
        input_file = InputFile.from_bytes(file_content, filename=file.filename)
        
        print("Uploading to Appwrite...")
        result = storage.create_file(
            bucket_id=os.getenv("APPWRITE_BUCKET_ID"),
            file_id=file_id,
            file=input_file
        )
        print(f"Appwrite upload result: {result}")
        
        # Create metadata
        print("Creating metadata...")
        metadata = FileMetadata(
            appwrite_file_id=result["$id"],
            original_name=file.filename,
            file_size=result["sizeOriginal"],
            mime_type=file.content_type or "application/octet-stream"
        )
        print(f"Metadata created: {metadata.dict()}")
        
        # Save metadata to MongoDB
        print("Saving to MongoDB...")
        result_db = await db.file_metadata.insert_one(metadata.dict())
        print(f"MongoDB save result: {result_db.inserted_id}")
        
        # Return response
        print("Upload successful!")
        return FileMetadataResponse(**metadata.dict())
    except Exception as e:
        print(f"Upload error occurred: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
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

# Mount static files for frontend
static_dir = Path("frontend/build")
print(f"Looking for static files at: {static_dir.absolute()}")
print(f"Static directory exists: {static_dir.exists()}")
if static_dir.exists():
    static_files_path = static_dir / "static"
    print(f"Static files path: {static_files_path.absolute()}")
    print(f"Static files directory exists: {static_files_path.exists()}")
    if static_files_path.exists():
        print(f"Mounting static files from: {static_files_path}")
        app.mount("/static", StaticFiles(directory=str(static_files_path)), name="static")
        print("Static files mounted successfully")
    else:
        print("Warning: Static files directory not found")
else:
    print(f"Frontend build directory not found at: {static_dir.absolute()}")
    
    # Serve React app for all non-API routes
    from fastapi.responses import FileResponse
    
    @app.get("/")
    async def serve_react_app():
        return FileResponse(static_dir / "index.html")
    
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        # If the path doesn't start with /api, serve the React app
        if not full_path.startswith("api"):
            return FileResponse(static_dir / "index.html")
        else:
            raise HTTPException(status_code=404, detail="Not found")

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