import enum
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import os
# Connect to Docker Postgres
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/purrvision_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class StoreStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROVISIONING = "PROVISIONING"
    READY = "READY"
    FAILED = "FAILED"
    DELETING = "DELETING"
    DELETED = "DELETED"

class StoreEngine(str, enum.Enum):
    WOOCOMMERCE = "woocommerce"
    MEDUSA = "medusa"

class Store(Base):
    __tablename__ = "stores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, index=True)
    status = Column(Enum(StoreStatus), default=StoreStatus.QUEUED)
    
    
    engine = Column(Enum(StoreEngine), default=StoreEngine.WOOCOMMERCE)
    
    url = Column(String, nullable=True)
    
    # Credentials
    admin_user = Column(String, default="admin")
    admin_password = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    audit_logs = relationship("AuditLog", back_populates="store")

class AuditLog(Base):
    """
    Separate table for history. 
    Matches requirement: 'Audit log: who created/deleted what and when'
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"))
    event = Column(String) 
    details = Column(String, nullable=True) 
    timestamp = Column(DateTime, default=datetime.utcnow)

    store = relationship("Store", back_populates="audit_logs")

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()