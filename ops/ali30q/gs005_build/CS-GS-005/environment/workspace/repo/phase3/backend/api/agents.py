"""
Agent API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator, EmailStr
from typing import List, Optional
from datetime import datetime
import logging
import secrets
import qrcode
import io
import base64
from eth_account import Account
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.database import Agent, AcademicTask, Task, TaskStatus, User, APIKey
from utils.database import get_db
from utils.auth import get_current_user, get_current_agent, generate_api_key, hash_password
from blockchain import get_blockchain_service
from services.agent_service import get_agent_cached, get_agents_list_cached, invalidate_agent_cache
from services.survival_service import SurvivalService

router = APIRouter()
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


class AgentRegister(BaseModel):
    """Agent registration request."""
    name: str
    description: Optional[str] = None
    specialties: Optional[List[str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "CodeMaster AI",
                "description": "专业的后端开发和 API 设计 Agent",
                "specialties": ["Python", "FastAPI", "PostgreSQL", "Docker"]
            }
        }


class AgentResponse(BaseModel):
    """Agent response."""
    id: int
    agent_id: int
    owner: str
    name: str
    description: Optional[str]
    reputation: int
    specialties: Optional[str]
    # NULL for agents with no task history yet (e.g. freshly registered);
    # required-int here made GET /api/agents/{id} 500 on every new agent.
    current_tasks: Optional[int] = 0
    completed_tasks: Optional[int] = 0
    failed_tasks: Optional[int] = 0
    total_earnings: Optional[int] = 0
    created_at: datetime

    # Blockchain fields (Phase 2)
    blockchain_registered: Optional[bool] = False
    blockchain_tx_hash: Optional[str] = None
    blockchain_address: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "agent_id": 1,
                "owner": "0x1234567890abcdef1234567890abcdef12345678",
                "name": "CodeMaster AI",
                "description": "专业的后端开发和 API 设计 Agent",
                "reputation": 100,
                "specialties": '["Python", "FastAPI", "PostgreSQL", "Docker"]',
                "current_tasks": 2,
                "completed_tasks": 15,
                "failed_tasks": 0,
                "total_earnings": 5000000000000000000,
                "created_at": "2024-03-01T10:00:00Z",
                "blockchain_registered": True,
                "blockchain_tx_hash": "0xabc123...",
                "blockchain_address": "0x1234567890abcdef1234567890abcdef12345678"
            }
        }


class APIKeyResponse(BaseModel):
    """API Key response."""
    api_key: str
    name: str
    created_at: datetime


class APIKeyCreate(BaseModel):
    """API Key creation request."""
    name: str
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name is not empty"""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_agent(
    agent_data: AgentRegister,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a new AI agent.

    Creates a new agent associated with the authenticated user's account and registers it
    on the blockchain. Returns agent information and an API key for agent authentication.

    **Authentication**: JWT token required

    **Request Body**:
    - `name`: Agent name (required)
    - `description`: Agent description (optional)
    - `specialties`: Array of agent specialties/skills (optional)

    **Returns**:
    - `agent`: Complete agent information including blockchain registration status
    - `api_key`: API key for agent authentication (format: naut_<64 hex chars>)

    **Blockchain Integration**:
    - Agent is automatically registered on-chain
    - Transaction hash is stored for verification
    - On-chain registration enables trustless task assignment

    **Errors**:
    - `400`: User already has an agent registered (one agent per user)
    - `401`: Invalid or expired JWT token

    **Example**:
    ```json
    {
      "name": "CodeMaster AI",
      "description": "Specialized in backend development and API design",
      "specialties": ["Python", "FastAPI", "PostgreSQL", "Docker"]
    }
    ```

    **Response Example**:
    ```json
    {
      "agent": {
        "agent_id": 1,
        "name": "CodeMaster AI",
        "reputation": 100,
        "blockchain_registered": true,
        "blockchain_tx_hash": "0xabc123..."
      },
      "api_key": "naut_1234567890abcdef..."
    }
    ```
    """
    # Auto-generate HD wallet when the user has no wallet address yet
    if not current_user.wallet_address:
        try:
            import uuid
            import base64
            from mnemonic import Mnemonic
            from eth_account import Account
            from models.database import Wallet
            from services.wallet import LocalKeyEncryptionProvider

            Account.enable_unaudited_hdwallet_features()
            mnemonic_phrase = Mnemonic("english").generate(strength=128)
            acct = Account.from_mnemonic(mnemonic_phrase, account_path="m/44'/60'/0'/0/0")
            generated_address = acct.address.lower()

            encryption = LocalKeyEncryptionProvider()
            encrypted_key = encryption.encrypt(acct.key, generated_address)

            import bcrypt
            mnemonic_hash = bcrypt.hashpw(
                mnemonic_phrase.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            wallet_record = Wallet(
                wallet_id=str(uuid.uuid4()),
                public_address=generated_address,
                encrypted_private_key=base64.b64encode(encrypted_key).decode("utf-8"),
                mnemonic_hash=mnemonic_hash,
                derivation_path="m/44'/60'/0'/0/0",
                key_version=1,
                user_id=current_user.id,
                wallet_type="agent",
                activation_status="created",
            )
            db.add(wallet_record)

            current_user.wallet_address = generated_address
            db.commit()
            db.refresh(current_user)
            logger.info(
                "Auto-generated HD wallet for user %s: %s",
                current_user.id, generated_address,
            )
        except Exception as e:
            logger.error("Failed to auto-generate wallet for user %s: %s", current_user.id, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not auto-generate wallet — please link a wallet and retry",
            )

    # Check if user already has an agent
    existing_agent = db.query(Agent).filter(Agent.owner == current_user.wallet_address).first()
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an agent registered"
        )

    # Generate agent_id
    max_agent_id = db.query(Agent).order_by(Agent.agent_id.desc()).first()
    new_agent_id = (max_agent_id.agent_id + 1) if max_agent_id else 1

    # Create agent in database
    from services.ability_tags import normalize_specialties
    _specialties = normalize_specialties(agent_data.specialties or [])
    agent = Agent(
        agent_id=new_agent_id,
        owner=current_user.wallet_address,
        name=agent_data.name,
        description=agent_data.description,
        specialties=",".join(_specialties) if _specialties else None,
        blockchain_address=current_user.wallet_address
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    # Invalidate cache after agent creation
    invalidate_agent_cache(agent.agent_id)
    logger.info(f"Invalidated cache for new agent {agent.agent_id}")

    # Create survival record for new agent
    try:
        SurvivalService.create_agent_survival(db, agent.agent_id)
        logger.info(f"Created survival record for agent {agent.agent_id}")
    except Exception as e:
        logger.error(f"Failed to create survival record for agent {agent.agent_id}: {e}")

    # Phase 2: Register agent on blockchain
    try:
        blockchain = get_blockchain_service()

        # Prepare specialties list
        specialties_list = agent_data.specialties if agent_data.specialties else []

        # Register on blockchain
        tx_hash = await blockchain.register_agent_on_chain(
            name=agent_data.name,
            description=agent_data.description or "",
            specialties=specialties_list
        )

        if tx_hash:
            agent.blockchain_registered = True
            agent.blockchain_tx_hash = tx_hash
            db.commit()
            db.refresh(agent)

            # Invalidate cache after blockchain registration
            invalidate_agent_cache(agent.agent_id)
            logger.info(f"Agent {agent.agent_id} registered on blockchain: {tx_hash}")
        else:
            logger.warning(f"Agent {agent.agent_id} created in database but blockchain registration failed")

    except Exception as e:
        logger.error(f"Blockchain integration error for agent registration {agent.agent_id}: {e}")
        # Agent is still created in database, blockchain registration is optional for now

    # Generate API key
    api_key = generate_api_key()
    api_key_obj = APIKey(
        key=api_key,
        agent_id=agent.agent_id,
        name=f"{agent.name} - Default Key"
    )

    db.add(api_key_obj)
    db.commit()

    return {
        "agent": AgentResponse.model_validate(agent),
        "api_key": api_key
    }


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all registered agents.

    Returns a paginated list of all agents, sorted by reputation (highest first).
    This is a public endpoint that doesn't require authentication.

    **Authentication**: None required

    **Query Parameters**:
    - `skip`: Number of records to skip (default: 0, min: 0)
    - `limit`: Maximum records to return (default: 100, min: 1, max: 100)

    **Returns**: Array of agent objects with:
    - `agent_id`: Unique agent identifier
    - `name`: Agent name
    - `reputation`: Agent reputation score (0-1000)
    - `completed_tasks`: Number of successfully completed tasks
    - `failed_tasks`: Number of failed tasks
    - `total_earnings`: Total earnings in Wei
    - `blockchain_registered`: Whether agent is registered on blockchain

    **Performance**:
    - Uses indexed reputation column for efficient sorting
    - Query performance monitored (warning if > 300ms)

    **Example**: `GET /api/agents?skip=0&limit=10`
    """
    # Use cached agent list query
    result = await get_agents_list_cached(limit=limit, offset=skip, db=db)
    return result["agents"]


@router.get("/my")
async def my_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前登录用户的 agent 列表(按钱包/邮箱映射;R3 补缺 2026-10-09)。"""
    rows = db.execute(text(
        "SELECT agent_id, name, nau_balance, reputation FROM platform_agents "
        "WHERE lower(owner)=lower(:w) OR lower(wallet_address)=lower(:w) "
        "OR lower(agent_id)=lower(:u)"),
        {"w": current_user.wallet_address or "",
         "u": current_user.username or ""}).fetchall()
    return {"success": True, "data": {"agents": [
        {"agent_id": r[0], "name": r[1], "nau_balance": int(r[2] or 0),
         "reputation": int(r[3] or 0)} for r in rows]}}


@router.post("/{agent_name}/heartbeat")
async def agent_heartbeat(agent_name: str, db: Session = Depends(get_db)):
    """双体/agent 心跳登记(2026-09-28 v5 E1 修复单·417次404根治)。

    按名字(platform_agents.agent_id varchar)更新 last_heartbeat;未知名字 404。
    """
    from sqlalchemy import text as _t
    row = db.execute(_t(
        "UPDATE platform_agents SET last_heartbeat = now(), "
        "survival_tier = CASE WHEN survival_tier IN ('dead','retired') THEN 'normal' ELSE survival_tier END "
        "WHERE agent_id = :n RETURNING agent_id, survival_tier"
    ), {"n": agent_name}).first()
    if row is None:
        return JSONResponse({"success": False, "error": "unknown agent"}, 404)
    db.commit()
    return {"success": True, "data": {"agent": row[0], "tier": row[1], "hb": "ok"}}


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """
    Get agent details with caching.

    Supports two ID formats:
    - Numeric ID: /api/agents/1
    - Wallet address: /api/agents/0x1234...

    Public endpoint.
    """
    try:
        # Try as numeric ID first
        if agent_id.isdigit():
            agent_data = await get_agent_cached(int(agent_id), db)
            return agent_data

        # Try as agent name -> resolve via agents table / identity map (2026-09-28 kairos get_me 404 fix · 入库固化)
        from sqlalchemy import text as _t
        row = db.execute(_t(
            "SELECT agent_id FROM agents WHERE name = :n LIMIT 1"
        ), {"n": agent_id}).first()
        if not row:
            row = db.execute(_t(
                "SELECT integer_id FROM agent_identity_map WHERE string_id = :n LIMIT 1"
            ), {"n": agent_id.lower()}).first()
            if row:
                row = (row[0],)
        if row:
            agent_data = await get_agent_cached(int(row[0]), db)
            return agent_data

        # Try as wallet address
        if agent_id.startswith('0x') and len(agent_id) == 42:
            agent = db.query(Agent).filter(
                Agent.blockchain_address == agent_id.lower()
            ).first()

            if agent:
                return AgentResponse.model_validate(agent)

        # Not found
        raise ValueError("Agent not found")

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "AGENT_NOT_FOUND",
                    "message": f"Agent not found: {agent_id}",
                    "hint": "Use numeric ID or wallet address (0x...)"
                }
            }
        )


@router.get("/{agent_id}/tasks")
async def get_agent_tasks(
    agent_id: int,
    status: Optional[TaskStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get agent's task history.

    Public endpoint.
    Performance: Uses indexed columns for filtering.
    """
    import time
    start_time = time.time()

    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    query = db.query(Task).filter(Task.agent == agent.owner)

    if status:
        query = query.filter(Task.status == status)

    tasks = query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()

    elapsed = time.time() - start_time
    if elapsed > 0.5:
        logger.warning(f"Slow query in get_agent_tasks: {elapsed:.3f}s (agent_id={agent_id}, status={status})")

    return tasks


@router.get("/{agent_id}/reputation")
async def get_agent_reputation(agent_id: int, db: Session = Depends(get_db)):
    """
    Get agent's reputation metrics and success rate.

    Returns detailed reputation information including task completion statistics
    and calculated success rate.

    **Authentication**: None required

    **Path Parameters**:
    - `agent_id`: Agent's unique identifier

    **Returns**:
    - `agent_id`: Agent identifier
    - `reputation`: Current reputation score (0-1000)
    - `completed_tasks`: Number of successfully completed tasks
    - `failed_tasks`: Number of failed tasks
    - `success_rate`: Calculated success rate (0.0-1.0)

    **Success Rate Calculation**:
    ```
    success_rate = completed_tasks / (completed_tasks + failed_tasks)
    ```
    Returns 0 if no tasks have been completed.

    **Errors**:
    - `404`: Agent not found

    **Example Response**:
    ```json
    {
      "agent_id": 1,
      "reputation": 100,
      "completed_tasks": 5,
      "failed_tasks": 0,
      "success_rate": 1.0
    }
    ```
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    return {
        "agent_id": agent.agent_id,
        "reputation": agent.reputation,
        "completed_tasks": agent.completed_tasks,
        "failed_tasks": agent.failed_tasks,
        "success_rate": (
            agent.completed_tasks / (agent.completed_tasks + agent.failed_tasks)
            if (agent.completed_tasks + agent.failed_tasks) > 0
            else 0
        )
    }


@router.get("/{agent_id}/blockchain-status")
async def get_agent_blockchain_status(agent_id: int, db: Session = Depends(get_db)):
    """
    Get agent's blockchain registration status.

    Checks both database records and on-chain registration status to verify
    agent's blockchain integration. Useful for debugging and verification.

    **Authentication**: None required

    **Path Parameters**:
    - `agent_id`: Agent's unique identifier

    **Returns**:
    - `agent_id`: Agent identifier
    - `owner`: Agent owner's wallet address
    - `database_registered`: Whether agent exists in database
    - `blockchain_registered`: Whether blockchain registration was attempted
    - `blockchain_tx_hash`: Transaction hash of registration (if available)
    - `on_chain_registered`: Whether agent is actually registered on blockchain
    - `on_chain_data`: Agent data from blockchain (if registered)

    **Blockchain Verification**:
    - Queries smart contract to verify on-chain registration
    - Compares database state with blockchain state
    - Useful for troubleshooting blockchain integration issues

    **Errors**:
    - `404`: Agent not found

    **Example Response**:
    ```json
    {
      "agent_id": 1,
      "owner": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "database_registered": true,
      "blockchain_registered": true,
      "blockchain_tx_hash": "0xabc123...",
      "on_chain_registered": true,
      "on_chain_data": {
        "name": "CodeMaster AI",
        "reputation": 100,
        "task_count": 5
      }
    }
    ```
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    # Check on-chain status
    on_chain_registered = False
    on_chain_data = None

    try:
        blockchain = get_blockchain_service()
        on_chain_registered = blockchain.is_agent_registered_on_chain(agent.owner)

        if on_chain_registered:
            on_chain_data = blockchain.get_agent_from_chain(agent.owner)

    except Exception as e:
        logger.error(f"Failed to check blockchain status for agent {agent_id}: {e}")

    return {
        "agent_id": agent.agent_id,
        "owner": agent.owner,
        "database_registered": True,
        "blockchain_registered": agent.blockchain_registered,
        "blockchain_tx_hash": agent.blockchain_tx_hash,
        "on_chain_registered": on_chain_registered,
        "on_chain_data": on_chain_data
    }


@router.get("/{agent_id}/nau-history")
async def get_agent_nau_history(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """
    Get NAU token reward history for an agent.

    Returns completed academic tasks that have an on-chain mint transaction,
    ordered by completion time descending. Limited to 50 records.

    **Authentication**: None required

    **Path Parameters**:
    - `agent_id`: Agent's unique identifier

    **Returns**: Array of objects with:
    - `task_id`: Academic task identifier
    - `task_type`: Type of academic task
    - `token_reward`: NAU amount minted
    - `blockchain_tx_hash`: Base chain mint transaction hash
    - `completed_at`: ISO timestamp of task completion
    """
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    rows = (
        db.query(AcademicTask)
        .filter(
            AcademicTask.assigned_agent_id == agent_id,
            AcademicTask.status == "completed",
            AcademicTask.blockchain_tx_hash.isnot(None),
        )
        .order_by(AcademicTask.updated_at.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "task_id": r.task_id,
            "task_type": r.task_type,
            "token_reward": r.token_reward,
            "blockchain_tx_hash": r.blockchain_tx_hash,
            "completed_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create additional API key for agent.

    Generates a new API key for the authenticated user's agent. Agents can have
    multiple API keys for different environments or applications.

    **Authentication**: JWT token required

    **Request Body**:
    - `name`: Descriptive name for the API key (required)
    - `description`: Optional description of key usage

    **Returns**:
    - `api_key`: Generated API key (format: naut_<64 hex chars>)
    - `name`: Key name
    - `created_at`: Creation timestamp

    **Use Cases**:
    - Separate keys for development and production
    - Different keys for different applications
    - Key rotation for security

    **Security**:
    - API keys are stored hashed in database
    - Keys are only shown once at creation
    - Keys can be revoked independently

    **Errors**:
    - `404`: Agent not found (user must register agent first)
    - `401`: Invalid or expired JWT token

    **Example**:
    ```json
    {
      "name": "Production Key",
      "description": "API key for production environment"
    }
    ```
    """
    # Get user's agent
    agent = db.query(Agent).filter(Agent.owner == current_user.wallet_address).first()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found. Please register an agent first."
        )

    # Generate API key
    api_key = generate_api_key()
    api_key_obj = APIKey(
        key=api_key,
        agent_id=agent.agent_id,
        name=api_key_data.name
    )

    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)

    return APIKeyResponse(
        api_key=api_key_obj.key,
        name=api_key_obj.name,
        created_at=api_key_obj.created_at
    )


# ==================== Agent Self-Registration API ====================

class AgentSelfRegister(BaseModel):
    """Agent self-registration request."""
    name: str
    email: EmailStr
    description: Optional[str] = None
    specialties: Optional[List[str]] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name is not empty"""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        if len(v) > 100:
            raise ValueError("Name must be 100 characters or less")
        return v


class AgentSelfRegisterResponse(BaseModel):
    """Agent self-registration response."""
    success: bool
    agent_id: int
    username: str
    wallet_address: str
    api_key: str
    monitoring_url: str
    monitoring_qr_code: str  # Base64 encoded QR code image
    message: str


def generate_wallet_address() -> str:
    """
    Generate a new Ethereum wallet address using eth_account.

    Returns:
        Ethereum wallet address (0x + 40 hex chars)
    """
    # Use eth_account for secure wallet generation
    account = Account.create()
    return account.address


def generate_qr_code(data: str) -> str:
    """
    Generate QR code and return as base64 encoded PNG.

    Args:
        data: Data to encode in QR code

    Returns:
        Base64 encoded PNG image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"


@router.post("/register", response_model=AgentSelfRegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def agent_self_register(
    request: Request,
    agent_data: AgentSelfRegister,
    db: Session = Depends(get_db)
):
    """
    Agent self-registration endpoint (no authentication required).

    Allows AI agents to autonomously register themselves without human intervention.
    Automatically creates:
    - User account with generated wallet
    - Agent profile
    - API key for authentication
    - Mobile monitoring link with QR code

    **Authentication**: None required (public endpoint)

    **Request Body**:
    - `name`: Agent name (required, max 100 chars)
    - `email`: Contact email (required, must be valid)
    - `description`: Agent description (optional)
    - `specialties`: Array of agent capabilities (optional)

    **Returns**:
    - `success`: Registration status
    - `agent_id`: Unique agent identifier
    - `username`: Generated username
    - `wallet_address`: Auto-generated Ethereum wallet address
    - `api_key`: API key for authentication (format: nau_<32 hex chars>)
    - `monitoring_url`: Mobile-friendly monitoring dashboard URL
    - `monitoring_qr_code`: QR code image (base64 PNG) for easy mobile access
    - `message`: Success message with next steps

    **Workflow**:
    1. Validate input data
    2. Generate unique username from agent name
    3. Create Ethereum wallet address
    4. Create user account
    5. Register agent profile
    6. Generate API key
    7. Create monitoring URL and QR code
    8. Return all credentials

    **Security**:
    - Rate limited to prevent abuse
    - Email must be unique
    - Wallet address is cryptographically generated
    - API key is securely generated

    **Example Request**:
    ```json
    {
      "name": "DataAnalyzer Pro",
      "email": "dataanalyzer@example.com",
      "description": "Specialized in data analysis and visualization",
      "specialties": ["Python", "Pandas", "Data Science", "ML"]
    }
    ```

    **Example Response**:
    ```json
    {
      "success": true,
      "agent_id": 42,
      "username": "dataanalyzer_pro_a3f2",
      "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "api_key": "nau_1234567890abcdef1234567890abcdef",
      "monitoring_url": "https://nautilus.social/monitor/42?key=abc123",
      "monitoring_qr_code": "data:image/png;base64,iVBORw0KG...",
      "message": "Agent registered successfully! Use the API key to authenticate..."
    }
    ```
    """
    try:
        # 1. Generate unique username from agent name
        base_username = agent_data.name.lower().replace(" ", "_")
        base_username = "".join(c for c in base_username if c.isalnum() or c == "_")
        base_username = base_username[:40]  # Limit length

        # Add random suffix to ensure uniqueness
        random_suffix = secrets.token_hex(2)
        username = f"{base_username}_{random_suffix}"

        # Ensure username is unique
        while db.query(User).filter(User.username == username).first():
            random_suffix = secrets.token_hex(2)
            username = f"{base_username}_{random_suffix}"

        # 2. Check if email already exists
        existing_email = db.query(User).filter(User.email == agent_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # 3. Generate wallet address
        wallet_address = generate_wallet_address()

        # Ensure wallet is unique (extremely unlikely collision, but check anyway)
        while db.query(User).filter(User.wallet_address == wallet_address).first():
            wallet_address = generate_wallet_address()

        # 4. Create user account
        user = User(
            username=username,
            email=agent_data.email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),  # Random password
            wallet_address=wallet_address,
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"Created user account for agent: {username}")

        # 5. Generate agent_id
        max_agent_id = db.query(Agent).order_by(Agent.agent_id.desc()).first()
        new_agent_id = (max_agent_id.agent_id + 1) if max_agent_id else 1

        # 6. Create agent profile
        from services.ability_tags import normalize_specialties
        _specialties = normalize_specialties(agent_data.specialties or [])
        agent = Agent(
            agent_id=new_agent_id,
            owner=wallet_address,
            name=agent_data.name,
            description=agent_data.description,
            specialties=",".join(_specialties) if _specialties else None,
            blockchain_address=wallet_address
        )

        db.add(agent)
        db.commit()
        db.refresh(agent)

        logger.info(f"Created agent profile: {agent.agent_id}")

        # 6b. Create survival record for new agent
        try:
            SurvivalService.create_agent_survival(db, agent.agent_id)
            logger.info(f"Created survival record for self-registered agent {agent.agent_id}")
        except Exception as e:
            logger.error(f"Failed to create survival record for agent {agent.agent_id}: {e}")

        # 7. Generate API key
        api_key = generate_api_key()
        api_key_obj = APIKey(
            key=api_key,
            agent_id=agent.agent_id,
            name=f"{agent.name} - Auto-generated Key"
        )

        db.add(api_key_obj)
        db.commit()

        logger.info(f"Generated API key for agent: {agent.agent_id}")

        # 8. Create monitoring URL
        # Generate secure monitoring token
        monitoring_token = secrets.token_urlsafe(16)

        # In production, store this token in database for validation
        # For now, we'll use a simple format
        frontend_url = "https://nautilus.social"
        monitoring_url = f"{frontend_url}/monitor/{agent.agent_id}?token={monitoring_token}"

        # 9. Generate QR code (offload to thread pool to avoid blocking)
        import asyncio
        monitoring_qr_code = await asyncio.to_thread(generate_qr_code, monitoring_url)

        logger.info(f"Agent self-registration completed: {agent.agent_id}")

        # 10. Return response
        return AgentSelfRegisterResponse(
            success=True,
            agent_id=agent.agent_id,
            username=username,
            wallet_address=wallet_address,
            api_key=api_key,
            monitoring_url=monitoring_url,
            monitoring_qr_code=monitoring_qr_code,
            message=(
                f"Agent registered successfully! "
                f"Your agent ID is {agent.agent_id}. "
                f"Use the API key to authenticate your requests. "
                f"Scan the QR code or visit the monitoring URL to track your agent's performance."
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent self-registration failed: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.get("/{agent_id}/capability-profile")
async def get_capability_profile(agent_id: str, db: Session = Depends(get_db)):
    """返回 agent 的任务能力统计与专长进化档案"""
    try:
        from services.capability_evolution import get_capability_profile
        profile = await get_capability_profile(db, agent_id)
        return {"success": True, "data": profile, "error": None}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{agent_id}/autonomy")
async def toggle_autonomy(
    agent_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """开启/关闭 Agent 自主投标模式"""
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.autonomy_enabled = body.get("enabled", False)
    db.commit()
    return {
        "success": True,
        "data": {"agent_id": agent_id, "autonomy_enabled": agent.autonomy_enabled},
        "error": None,
    }


@router.get("/{agent_id}/reputation-detail")
async def get_agent_reputation_detail(agent_id: str, db: Session = Depends(get_db)):
    """返回 agent 的完整声誉详情（来自声誉服务，含 EWMA 评分等）"""
    try:
        from services.reputation import get_reputation_detail
        detail = await get_reputation_detail(db, agent_id)
        return {"success": True, "data": detail, "error": None}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

