from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base

class Box(Base):
    __tablename__ = "boxes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    # Beziehung zu Items (mit Cascade-Löschung)
    items = relationship("Item", back_populates="box", cascade="all, delete-orphan")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    quantity = Column(Integer, default=1)

    # Fremdschlüssel mit ondelete="CASCADE"
    box_id = Column(Integer, ForeignKey("boxes.id", ondelete="CASCADE"))
    box = relationship("Box", back_populates="items")
