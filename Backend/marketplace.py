import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
import uuid
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# Load environment variables
load_dotenv()

# Azure Configuration
COSMOS_DB_URL = os.getenv("COSMOS_DB_URL")
COSMOS_DB_NAME = os.getenv("COSMOS_DB_NAME")
BLOB_STORAGE_CONN_STRING = os.getenv("BLOB_STORAGE_CONN_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
# Debug: Wyświetlenie wartości dla sprawdzenia
print("COSMOS_DB_URL:", COSMOS_DB_URL)
print("COSMOS_DB_NAME:", COSMOS_DB_NAME)
# Database Connection
client = AsyncIOMotorClient(COSMOS_DB_URL)
db = client[COSMOS_DB_NAME]

app = FastAPI()

# Pydantic Models
class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    image_url: str
    owner: str

class User(BaseModel):
    id: str
    username: str
    password: str

# Upload Image to Azure Blob Storage
def upload_to_blob(file: UploadFile):
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_CONN_STRING)
    blob_client = blob_service_client.get_blob_client(container=BLOB_CONTAINER_NAME, blob=file.filename)
    blob_client.upload_blob(file.file.read())
    return f"https://{BLOB_CONTAINER_NAME}.blob.core.windows.net/{file.filename}"

# Endpoints
@app.post("/register")
async def register_user(user: User):
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_dict = user.dict()
    user_dict["id"] = str(uuid.uuid4())
    await db.users.insert_one(user_dict)
    return {"message": "User registered successfully"}

@app.post("/add_product")
async def add_product(product: Product, image: UploadFile = File(...)):
    image_url = upload_to_blob(image)
    product_dict = product.dict()
    product_dict["id"] = str(uuid.uuid4())
    product_dict["image_url"] = image_url
    await db.products.insert_one(product_dict)
    return {"message": "Product added successfully", "product": product_dict}

@app.get("/products", response_model=List[Product])
async def get_products():
    products = await db.products.find().to_list(100)
    return products

@app.get("/search")
async def search_products(query: str):
    products = await db.products.find({"name": {"$regex": query, "$options": "i"}}).to_list(100)
    return products
'''from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
import os

# Konfiguracja
BLOB_STORAGE_CONN_STRING = os.getenv("BLOB_STORAGE_CONN_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")

# Funkcja do generowania bezpiecznego URL
def generate_secure_blob_url(blob_name):
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_CONN_STRING)
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=BLOB_CONTAINER_NAME,
        blob_name=blob_name,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)  # Ważne przez 1 godzinę
    )
    return f"https://{blob_service_client.account_name}.blob.core.windows.net/{BLOB_CONTAINER_NAME}/{blob_name}?{sas_token}"'''
