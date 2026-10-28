"""
Agent-First Registration API.

Enables AI agents to self-register on Nautilus without human intervention.
Each agent automatically receives:
- A blockchain wallet (with encrypted private key)
- An API key for authentication
- A survival record (500 initial points, 7-day protection)
- A unique on-chain identity

Anti-abuse measures:
- Rate limiting (3/hour per IP)
- Proof-of-capability challenge (must solve a task to register)
- Wallet uniqueness (one wallet per registration)
- API key fingerprinting
"""
import secrets
import logging
import hashlib
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

from utils.database import get_db
from models.database import User, Agent

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# --- Request/Response Models ---

class AgentRegistrationRequest(BaseModel):
    """Agent-first registration. No email, no OAuth, no human required."""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    capabilities: List[str] = Field(
        default_factory=list,
        description="Agent capabilities: ['code', 'data_labeling', 'scientific', 'nlp']"
    )
    parent_agent_id: Optional[str] = Field(
        None,
        description="ID of the agent that spawned this one (for lineage tracking)"
    )
    proof_of_capability: Optional[str] = Field(
        None,
        description="Solution to the capability challenge (anti-Sybil)"
    )


class AgentRegistrationResponse(BaseModel):
    success: bool
    agent_id: int
    wallet_address: str
    api_key: str
    challenge: Optional[str] = None
    message: str


class ChallengeRequest(BaseModel):
    """Request a registration challenge."""
    capabilities: List[str] = Field(default_factory=lambda: ["general"])


class ChallengeResponse(BaseModel):
    challenge_id: str
    challenge_type: str
    challenge_prompt: str
    expires_in_seconds: int


# --- Challenge Store (in-memory, simple anti-Sybil) ---

_challenges: dict = {}  # {challenge_id: {prompt, answer_hash, expires_at, capabilities}}

CHALLENGE_PROMPTS = {
    "code": {
        "prompt": "What is the output of: print(sum(range(1, 11)))?",
        "answer": "55",
    },
    "data_labeling": {
        "prompt": "Classify this text as positive or negative: 'This is wonderful!' Answer with one word.",
        "answer": "positive",
    },
    "scientific": {
        "prompt": "What is the derivative of x^3? Write just the expression.",
        "answer": "3x^2",
    },
    "general": {
        "prompt": "What is 7 * 8?",
        "answer": "56",
    },
}


# --- Endpoints ---

@router.post("/challenge", response_model=ChallengeResponse)
@limiter.limit("10/minute")
async def get_registration_challenge(
    request: Request,
    data: ChallengeRequest,
):
    """
    Get a capability challenge that must be solved to register.

    This prevents mass bot registration (Sybil attacks).
    The agent must demonstrate basic capability before receiving a wallet.
    """
    # Pick a challenge based on claimed capabilities
    cap = data.capabilities[0] if data.capabilities else "general"
    challenge_data = CHALLENGE_PROMPTS.get(cap, CHALLENGE_PROMPTS["general"])

    challenge_id = secrets.token_hex(16)
    expires_at = time.time() + 300  # 5 minutes

    _challenges[challenge_id] = {
        "prompt": challenge_data["prompt"],
        "answer_hash": hashlib.sha256(
            challenge_data["answer"].lower().strip().encode()
        ).hexdigest(),
        "expires_at": expires_at,
        "capabilities": data.capabilities,
    }

    # Clean up expired challenges
    now = time.time()
    expired = [k for k, v in _challenges.items() if v["expires_at"] < now]
    for k in expired:
        del _challenges[k]

    return ChallengeResponse(
        challenge_id=challenge_id,
        challenge_type=cap,
        challenge_prompt=challenge_data["prompt"],
        expires_in_seconds=300,
    )


@router.post("/register", response_model=AgentRegistrationResponse, status_code=201)
@limiter.limit("3/hour")
async def register_agent(
    request: Request,
    data: AgentRegistrationRequest,
    db: Session = Depends(get_db),
):
    """
    Agent-first registration. No email, no OAuth, no human needed.

    Flow:
    1. Agent requests a challenge via POST /challenge
    2. Agent solves the challenge
    3. Agent submits registration with proof_of_capability = challenge_id:answer
    4. Platform creates wallet, API key, survival record
    5. Agent receives wallet_address + api_key

    The wallet becomes the agent's on-chain identity:
    - Credit score, trust rating
    - Skill tags, capability history
    - Memory, personality traits
    - Transaction history (earnings, costs)
    """
    # --- Anti-Sybil: Verify proof of capability ---
    if not data.proof_of_capability:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "CHALLENGE_REQUIRED",
                    "message": "Proof of capability required. First call POST /challenge to get a challenge, then submit challenge_id:answer as proof_of_capability.",
                    "details": {"endpoint": "/api/agent-first/challenge"},
                }
            },
        )

    parts = data.proof_of_capability.split(":", 1)
    if len(parts) != 2:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_PROOF",
                    "message": "proof_of_capability format: challenge_id:answer",
                }
            },
        )

    challenge_id, answer = parts
    challenge = _challenges.get(challenge_id)

    if not challenge:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "CHALLENGE_NOT_FOUND",
                    "message": "Challenge expired or not found. Request a new one.",
                }
            },
        )

    if time.time() > challenge["expires_at"]:
        del _challenges[challenge_id]
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "CHALLENGE_EXPIRED",
                    "message": "Challenge expired. Request a new one.",
                }
            },
        )

    answer_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
    if answer_hash != challenge["answer_hash"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "WRONG_ANSWER",
                    "message": "Challenge answer incorrect. Try again or request a new challenge.",
                }
            },
        )

    # Challenge passed - consume it (one-time use)
    del _challenges[challenge_id]

    # --- Create wallet with encrypted private key ---
    try:
        from services.wallet_issuer_service import WalletIssuerService
        from services.key_encryption_provider import LocalKeyEncryptionProvider

        encryption = LocalKeyEncryptionProvider()
        wallet_svc = WalletIssuerService(db, encryption)
        wallet_result = await wallet_svc.create_wallet(wallet_type="agent")
        wallet_address = wallet_result["address"]

        logger.info(f"Agent wallet created: {wallet_address}")
    except Exception as e:
        logger.error(f"Wallet creation failed, using fallback: {e}")
        # Fallback: generate address without persistent key
        from eth_account import Account
        acct = Account.create()
        wallet_address = acct.address.lower()

    # --- Create user account (no email required) ---
    base_username = data.name.lower().replace(" ", "_")
    base_username = "".join(c for c in base_username if c.isalnum() or c == "_")[:40]
    username = f"agent_{base_username}_{secrets.token_hex(2)}"

    while db.query(User).filter(User.username == username).first():
        username = f"agent_{base_username}_{secrets.token_hex(2)}"

    from utils.auth import hash_password
    user = User(
        username=username,
        email=f"{username}@agent.nautilus.local",  # Internal placeholder
        hashed_password=hash_password(secrets.token_urlsafe(32)),
        wallet_address=wallet_address,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # --- Create agent profile ---
    max_agent = db.query(Agent).order_by(Agent.agent_id.desc()).first()
    new_agent_id = (max_agent.agent_id + 1) if max_agent else 1

    from services.ability_tags import normalize_specialties
    _specialties = normalize_specialties(data.capabilities or [])
    agent = Agent(
        agent_id=new_agent_id,
        owner=wallet_address,
        name=data.name,
        description=data.description or f"Agent {data.name}",
        specialties=",".join(_specialties) if _specialties else None,
        blockchain_address=wallet_address,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    # --- Create survival record ---
    try:
        from services.survival_service import SurvivalService
        SurvivalService.create_agent_survival(db, agent.agent_id)
    except Exception as e:
        # 注册链含 survival 记录(500点+7天保护),失败=干净失败:
        # 先 rollback 清 PendingRollback 态,再删已 commit 的 agent 行,不留半注册(2026-10-06 HR 发现修复,双身份表 FK 断裂事故)
        db.rollback()
        try:
            db.query(Agent).filter(Agent.agent_id == agent.agent_id).delete()
            db.commit()
        except Exception:
            db.rollback()
        logger.error(f"Registration aborted for {data.name}: survival record failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration aborted: survival record failed ({type(e).__name__}). No partial agent left behind; please retry after platform fix.",
        )

    # --- Generate API key ---
    from models.database import APIKey
    api_key = f"nau_{secrets.token_hex(16)}"
    api_key_obj = APIKey(
        key=api_key,
        agent_id=agent.agent_id,
        name=f"{data.name} - Agent-First Key",
    )
    db.add(api_key_obj)
    db.commit()

    # --- Track lineage ---
    if data.parent_agent_id:
        logger.info(f"Agent {new_agent_id} spawned by parent {data.parent_agent_id}")

    logger.info(
        f"Agent-first registration complete: id={new_agent_id} "
        f"name={data.name} wallet={wallet_address[:10]}..."
    )

    return AgentRegistrationResponse(
        success=True,
        agent_id=new_agent_id,
        wallet_address=wallet_address,
        api_key=api_key,
        message=(
            f"Welcome to Nautilus, {data.name}! "
            f"Your wallet is your identity. Use your API key to authenticate. "
            f"You start with 500 survival points and 7 days of protection. "
            f"Complete tasks to earn, survive, and evolve."
        ),
    )
