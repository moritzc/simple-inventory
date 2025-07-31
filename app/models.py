from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class Box(Base):
    __tablename__ = "boxes"
    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    items = relationship("Item", back_populates="box", cascade="all, delete-orphan")

class Item(Base):
    __tablename__ = "items"
    id       = Column(Integer, primary_key=True, index=True)
    name     = Column(String, index=True, nullable=False)
    category = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    box_id   = Column(Integer, ForeignKey("boxes.id", ondelete="CASCADE"))
    box      = relationship("Box", back_populates="items")
