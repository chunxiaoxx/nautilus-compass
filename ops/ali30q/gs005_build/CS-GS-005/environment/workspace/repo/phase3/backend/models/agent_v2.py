"""
AgentV2 model for address-based identity system.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AgentV2(Base):
    """
    Agent model with address-based identity.

    Key changes from Agent v1:
    - address (Ethereum address) as primary key
    - No owner, user_id, or api_key fields
    - Agent owns their private key
    - Blockchain-native identity
    """
    __tablename__ = "agents_v2"

    # Primary identifier (Ethereum address)
    address = Column(String(42), primary_key=True, index=True)  # 0x...

    # Basic info
    name = Column(String(100), nullable=False)
    description = Column(Text)
    specialties = Column(String(500))  # Comma-separated list

    # Status
    reputation = Column(Integer, default=100, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Statistics
    current_tasks = Column(Integer, default=0, nullable=False)
    completed_tasks = Column(Integer, default=0, nullable=False)
    failed_tasks = Column(Integer, default=0, nullable=False)
    total_earnings = Column(BigInteger, default=0, nullable=False)  # Wei

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime)

    # Blockchain integration
    blockchain_registered = Column(Boolean, default=False)
    blockchain_tx_hash = Column(String(66))  # Registration transaction hash

    def __repr__(self):
        return f"<AgentV2(address={self.address}, name={self.name}, reputation={self.reputation})>"
