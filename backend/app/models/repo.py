from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Repository(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "repositories"

    name = Column(String, unique=True, index=True, nullable=False)  # "owner/repo"
    owner = Column(String, index=True, nullable=False)
    url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    activities = relationship("Activity", back_populates="repository", cascade="all, delete-orphan")
