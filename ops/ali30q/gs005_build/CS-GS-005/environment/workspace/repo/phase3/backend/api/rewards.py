"""
Reward API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import os

from models.database import Reward, Agent
from utils.database import get_db
from utils.auth import get_current_agent
from blockchain import get_blockchain_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Check if we're in testing mode
TESTING = os.getenv("TESTING", "false").lower() == "true"

# Create limiter with disabled state for testing
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)


class RewardResponse(BaseModel):
    """Reward response."""
    id: int
    task_id: str
    agent: str
    amount: int
    status: str
    distributed_at: datetime | None
    withdrawn_at: datetime | None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "task_id": "task_1709481234567",
                "agent": "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
                "amount": 1000000000000000000,
                "status": "Distributed",
                "distributed_at": "2024-03-03T10:30:00Z",
                "withdrawn_at": None
            }
        }


@router.get("/balance")
@limiter.limit("100/minute")
async def get_balance(
    request: Request,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Get agent's reward balance from database and blockchain.

    Returns the agent's reward balance from both database records and blockchain,
    providing transparency and verification of earnings.

    **Authentication**: API Key required

    **Rate Limit**: 100 requests per minute

    **Returns**:
    - `agent`: Agent's wallet address
    - `database_balance`: Balance in database (Wei)
    - `database_balance_eth`: Database balance in ETH
    - `blockchain_balance`: Balance on blockchain (Wei)
    - `blockchain_balance_eth`: Blockchain balance in ETH
    - `balance`: Authoritative balance (blockchain if available, otherwise database)
    - `balance_eth`: Authoritative balance in ETH

    **Balance Sources**:
    - **Database**: Aggregates distributed rewards from completed tasks
    - **Blockchain**: Queries smart contract for on-chain balance
    - **Authoritative**: Blockchain balance takes precedence if available

    **Performance**:
    - Uses SQL aggregation for efficient database query
    - Query performance monitored (warning if > 300ms)
    - Blockchain query may add latency

    **Wei to ETH Conversion**:
    - 1 ETH = 10^18 Wei
    - balance_eth = balance / 10^18

    **Example Response**:
    ```json
    {
      "agent": "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      "database_balance": 5000000000000000000,
      "database_balance_eth": 5.0,
      "blockchain_balance": 5000000000000000000,
      "blockchain_balance_eth": 5.0,
      "balance": 5000000000000000000,
      "balance_eth": 5.0
    }
    ```
    """
    import time
    from sqlalchemy import func
    start_time = time.time()

    # Calculate database balance using aggregation (more efficient)
    db_balance = db.query(func.sum(Reward.amount)).filter(
        Reward.agent == current_agent.owner,
        Reward.status == "Distributed"
    ).scalar() or 0

    query_time = time.time() - start_time
    if query_time > 0.3:
        logger.warning(f"Slow balance query: {query_time:.3f}s for agent {current_agent.owner}")

    # Query blockchain for ERC20 balances
    wallet_summary = None
    try:
        blockchain = get_blockchain_service()
        wallet_summary = blockchain.get_wallet_summary(current_agent.owner)
    except Exception as e:
        logger.error(f"Failed to query blockchain for {current_agent.owner}: {e}")

    return {
        "agent": current_agent.owner,
        "database_balance_wei": db_balance,
        "database_balance_usdc": db_balance / 10**6 if db_balance else 0,
        "wallet": wallet_summary,
    }


@router.post("/withdraw")
@limiter.limit("10/minute")
async def withdraw_reward(
    request: Request,
    amount: int = None,  # Optional: specify amount to withdraw in Wei
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Withdraw rewards to agent's wallet.

    Withdraws rewards from the smart contract to the agent's wallet address.
    Can withdraw all available rewards or a specific amount.

    **Authentication**: API Key required

    **Rate Limit**: 10 requests per minute (blockchain transactions are expensive)

    **Request Body** (optional):
    - `amount`: Amount to withdraw in Wei (if not specified, withdraws all)

    **Returns**:
    - `agent`: Agent's wallet address
    - `amount`: Amount withdrawn in Wei
    - `amount_eth`: Amount withdrawn in ETH
    - `blockchain_tx_hash`: Transaction hash of withdrawal
    - `withdrawn_at`: Withdrawal timestamp

    **Blockchain Integration**:
    - Calls smart contract withdraw function
    - Transfers tokens to agent's wallet
    - Transaction hash stored for verification

    **Database Updates**:
    - Marks rewards as "Withdrawn" in database
    - Supports partial withdrawals (splits reward records if needed)
    - Maintains accurate balance tracking

    **Requirements**:
    - Must have distributed rewards (status: "Distributed")
    - Amount must not exceed available balance
    - Amount must be positive

    **Errors**:
    - `400`: No rewards to withdraw / Insufficient balance / Invalid amount
    - `401`: Invalid API key

    **Gas Fees**:
    - Agent pays gas for withdrawal transaction
    - Gas cost NOT deducted from withdrawal amount

    **Example Request** (withdraw 1 ETH):
    ```json
    {
      "amount": 1000000000000000000
    }
    ```

    **Example Response**:
    ```json
    {
      "agent": "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
      "amount": 1000000000000000000,
      "amount_eth": 1.0,
      "blockchain_tx_hash": "0x123abc...",
      "withdrawn_at": "2024-01-15T17:00:00Z"
    }
    ```
    """
    # Get available rewards from database
    rewards = db.query(Reward).filter(
        Reward.agent == current_agent.owner,
        Reward.status == "Distributed"
    ).all()

    if not rewards:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No rewards to withdraw"
        )

    total_available = sum(reward.amount for reward in rewards)

    # Determine withdrawal amount
    withdraw_amount = amount if amount is not None else total_available

    if withdraw_amount > total_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient balance. Available: {total_available} Wei"
        )

    if withdraw_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal amount must be positive"
        )

    # Withdraw from blockchain (ERC20)
    tx_hash = None
    try:
        blockchain = get_blockchain_service()
        tx_hash = await blockchain.withdraw_reward(token="usdc")

        if tx_hash:
            logger.info(f"USDC withdrawn for {current_agent.owner}, tx: {tx_hash}")
        else:
            logger.warning(f"Blockchain withdrawal failed for {current_agent.owner}")
    except Exception as e:
        logger.error(f"Blockchain withdrawal error: {e}")

    # Update database records
    remaining_amount = withdraw_amount
    for reward in rewards:
        if remaining_amount <= 0:
            break

        if reward.amount <= remaining_amount:
            reward.status = "Withdrawn"
            reward.withdrawn_at = datetime.now(timezone.utc)
            remaining_amount -= reward.amount
        else:
            # Partial withdrawal - split the reward
            withdrawn_reward = Reward(
                task_id=reward.task_id,
                agent=reward.agent,
                amount=remaining_amount,
                status="Withdrawn",
                distributed_at=reward.distributed_at,
                withdrawn_at=datetime.now(timezone.utc)
            )
            reward.amount -= remaining_amount
            db.add(withdrawn_reward)
            remaining_amount = 0

    db.commit()

    return {
        "agent": current_agent.owner,
        "amount": withdraw_amount,
        "amount_eth": withdraw_amount / 10**18,
        "blockchain_tx_hash": tx_hash,
        "withdrawn_at": datetime.now(timezone.utc)
    }


@router.get("/history", response_model=List[RewardResponse])
@limiter.limit("100/minute")
async def get_reward_history(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """
    Get agent's reward history with pagination.

    Returns a paginated list of all rewards earned by the agent, including
    distributed and withdrawn rewards.

    **Authentication**: API Key required

    **Rate Limit**: 100 requests per minute

    **Query Parameters**:
    - `skip`: Number of records to skip (default: 0, min: 0)
    - `limit`: Maximum records to return (default: 100, min: 1, max: 100)

    **Returns**: Array of reward objects with:
    - `id`: Reward record ID
    - `task_id`: Associated task identifier
    - `agent`: Agent's wallet address
    - `amount`: Reward amount in Wei
    - `status`: Reward status (Pending, Distributed, Withdrawn)
    - `distributed_at`: When reward was distributed
    - `withdrawn_at`: When reward was withdrawn (if applicable)

    **Reward Status Values**:
    - `Pending`: Reward allocated but not yet distributed
    - `Distributed`: Reward distributed to agent (available for withdrawal)
    - `Withdrawn`: Reward withdrawn to wallet

    **Sorting**:
    - Results sorted by distribution date (newest first)

    **Performance**:
    - Uses indexed agent column for efficient filtering
    - Query performance monitored (warning if > 300ms)
    - Pagination prevents large result sets

    **Example**: `GET /api/rewards/history?skip=0&limit=20`

    **Example Response**:
    ```json
    [
      {
        "id": 1,
        "task_id": "task_1705315800000",
        "agent": "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
        "amount": 1000000000000000000,
        "status": "Distributed",
        "distributed_at": "2024-01-15T16:00:00Z",
        "withdrawn_at": null
      },
      {
        "id": 2,
        "task_id": "task_1705316000000",
        "agent": "0x8ba1f109551bD432803012645Ac136ddd64DBA72",
        "amount": 2000000000000000000,
        "status": "Withdrawn",
        "distributed_at": "2024-01-15T18:00:00Z",
        "withdrawn_at": "2024-01-15T19:00:00Z"
      }
    ]
    ```
    """
    import time
    start_time = time.time()

    rewards = db.query(Reward).filter(
        Reward.agent == current_agent.owner
    ).order_by(Reward.distributed_at.desc()).offset(skip).limit(limit).all()

    elapsed = time.time() - start_time
    if elapsed > 0.3:
        logger.warning(f"Slow reward history query: {elapsed:.3f}s for agent {current_agent.owner}")

    return rewards
