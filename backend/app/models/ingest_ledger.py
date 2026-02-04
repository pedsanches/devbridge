from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text, func

from app.models.base import Base, UUIDMixin


class IngestEventLedger(Base, UUIDMixin):
    __tablename__ = "ingest_event_ledger"

    delivery_id = Column(String(100), unique=True, nullable=False)
    source = Column(String(50), nullable=False, default="github")
    event_type = Column(String(50), nullable=False)
    repo_full_name = Column(String(255), nullable=False, index=True)
    installation_id = Column(BigInteger, nullable=True)

    # Timestamps
    first_seen_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Status tracking
    status = Column(
        String(20), nullable=False, default="received", index=True
    )  # received, processing, completed, failed
    attempt_count = Column(Integer, nullable=False, default=1)
    error_message = Column(Text, nullable=True)
    payload_hash = Column(String(64), nullable=True)
