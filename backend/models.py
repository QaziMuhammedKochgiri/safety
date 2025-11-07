from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
import uuid

# Client Model
class ClientCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    phone: str
    country: str
    caseType: str  # "hague_convention", "child_abduction", "custody_rights"

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    clientNumber: str
    firstName: str
    lastName: str
    email: EmailStr
    phone: str
    country: str
    caseType: str
    status: str = "active"  # "active", "closed", "pending"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

# Document Model
class DocumentUpload(BaseModel):
    clientNumber: str

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    documentNumber: str
    clientNumber: str
    fileName: str
    fileSize: int
    fileType: str
    filePath: str
    uploadedBy: str = "client"  # "client" or "lawyer"
    uploadedAt: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"  # "pending", "reviewed", "approved"

# Consent Model
class LocationData(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country: Optional[str] = None
    city: Optional[str] = None

class Permissions(BaseModel):
    location: bool
    browser: bool
    camera: bool
    files: bool
    forensic: bool

class ConsentCreate(BaseModel):
    sessionId: str
    permissions: Permissions
    location: Optional[LocationData] = None
    userAgent: str
    clientNumber: Optional[str] = None

class Consent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sessionId: str
    ipAddress: str
    userAgent: str
    location: Optional[LocationData] = None
    permissions: Permissions
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    clientNumber: Optional[str] = None

# Chat Message Model
class ChatMessageCreate(BaseModel):
    sessionId: str
    sender: str  # "client", "bot", "lawyer"
    message: str
    clientNumber: Optional[str] = None

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sessionId: str
    clientNumber: Optional[str] = None
    sender: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    isRead: bool = False

# Landmark Case Model (read-only)
class LandmarkCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caseNumber: str
    year: int
    countries: Dict[str, str]
    title: Dict[str, str]
    description: Dict[str, str]
    outcome: Dict[str, str]
    facts: Dict[str, str]
    legalPrinciple: Dict[str, str]
    impact: Dict[str, str]
