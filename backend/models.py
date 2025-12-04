from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime, timezone
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
    hashedPassword: Optional[str] = None  # For client portal login
    role: str = "client"  # "client" or "admin"
    status: str = "active"  # "active", "closed", "pending"
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    uploadedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    clientNumber: Optional[str] = None

# Chat Message Model
class ChatMessageCreate(BaseModel):
    sessionId: str
    sender: str  # "client", "bot", "agent"
    message: str
    clientNumber: Optional[str] = None
    agentName: Optional[str] = None  # Name of the support agent
    isMobile: Optional[bool] = None
    language: Optional[str] = None

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sessionId: str
    clientNumber: Optional[str] = None
    sender: str
    message: str
    agentName: Optional[str] = None  # Name of the support agent
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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

# Authentication Models
class ClientRegister(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    lastName: str
    phone: str
    country: str
    caseType: str

class ClientLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    clientNumber: str
    email: str
    firstName: str
    lastName: str

# Meeting/Video Call Models
class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    scheduledTime: Optional[datetime] = None
    duration: int = 60  # in minutes
    meetingType: str = "consultation"  # "consultation", "follow_up", "urgent"

class Meeting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    meetingId: str
    clientNumber: str
    clientEmail: str
    title: str
    description: Optional[str] = None
    roomName: str
    meetingUrl: str
    scheduledTime: Optional[datetime] = None
    duration: int = 60
    meetingType: str = "consultation"
    status: str = "scheduled"  # "scheduled", "in_progress", "completed", "cancelled"
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    startedAt: Optional[datetime] = None
    endedAt: Optional[datetime] = None

# Forensic & Chain of Custody Models
class ChainOfCustodyEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str  # e.g., "Client: John Doe", "System: SHA256 Verification", "Lawyer: Admin"
    action: str  # e.g., "UPLOAD", "HASH_VERIFICATION", "ACCESS", "REPORT_GENERATED"
    details: str
    ipAddress: Optional[str] = None
    hashAtEvent: Optional[str] = None  # File hash at this specific point

class ForensicCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caseId: str  # Unique Case ID (e.g., CASE_20251128_XYZ)
    clientNumber: str
    caseStatus: str = "pending"  # pending, analyzing, completed, failed
    evidenceFiles: List[str] = []  # List of file paths/names
    primaryFileHash: Optional[str] = None  # SHA-256 Hash of the main evidence
    chainOfCustody: List[ChainOfCustodyEvent] = []
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EvidenceRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token: str # Unique access token for the magic link
    clientNumber: str
    lawyerId: str # Which admin created this request
    requestedTypes: List[str] = [] # e.g. ["photos", "documents", "whatsapp_backup"]
    status: str = "pending" # pending, completed, expired
    expiresAt: datetime
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SharedReportLink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token: str  # Unique token for URL
    caseId: str
    generatedBy: str  # Admin who generated it
    expiresAt: datetime
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    isRevoked: bool = False
