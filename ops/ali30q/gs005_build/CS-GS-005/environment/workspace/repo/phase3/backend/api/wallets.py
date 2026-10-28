"""Wallet management API endpoints."""
import logging
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from sqlalchemy import select

from models.database import User, Wallet
from utils.database import get_db
from utils.auth import get_current_user
from services.key_encryption_provider import LocalKeyEncryptionProvider

logger = logging.getLogger(__name__)

router = APIRouter()

TESTING = os.getenv("TESTING", "false").lower() == "true"
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)

# Module-level encryption provider (singleton)
_encryption_provider = LocalKeyEncryptionProvider()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CreateWalletRequest(BaseModel):
    """Request to create a new custodial wallet."""
    wallet_type: str = Field(default="agent", pattern="^(agent|user)$")


class CreateWalletResponse(BaseModel):
    """Response after wallet creation (mnemonic shown once)."""
    wallet_id: str
    address: str
    mnemonic: str
    derivation_path: str


class ImportWalletRequest(BaseModel):
    """Request to import wallet from mnemonic."""
    mnemonic: str = Field(..., min_length=10)
    derivation_path: str = Field(default="m/44'/60'/0'/0/0")


class ImportWalletResponse(BaseModel):
    """Response after wallet import."""
    wallet_id: str
    address: str
    derivation_path: str


class WalletBalanceResponse(BaseModel):
    """Wallet balance across token types."""
    address: str
    eth: float
    usdc: float
    usdt: float


class SignMessageRequest(BaseModel):
    """Request to sign a message with wallet key."""
    message: str = Field(..., min_length=1, max_length=4096)


class SignMessageResponse(BaseModel):
    """Signed message result."""
    wallet_id: str
    signature: str


class WalletSummary(BaseModel):
    """Wallet info without sensitive fields."""
    wallet_id: str
    address: str
    wallet_type: str
    activation_status: str
    derivation_path: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_wallet_service(db: Session):
    """
    Create a WalletIssuerService backed by a sync session.

    WalletIssuerService was designed for AsyncSession but the rest of the
    app uses synchronous SQLAlchemy.  We import it lazily and wrap the sync
    session so callers can still ``await`` its methods (SQLAlchemy sync
    sessions silently support this when running inside ``asyncio``).
    """
    from services.wallet_issuer_service import WalletIssuerService
    return WalletIssuerService(db, _encryption_provider)  # type: ignore[arg-type]


def _assert_wallet_owner(wallet: Wallet, current_user: User) -> None:
    """Raise 403 if the wallet does not belong to the current user."""
    if wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "WALLET_ACCESS_DENIED",
                    "message": "You do not own this wallet",
                }
            },
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/create",
    response_model=CreateWalletResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("3/hour")
async def create_wallet(
    request: Request,
    body: CreateWalletRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new HD wallet for the current user.

    The mnemonic is returned **once** and never stored in plaintext.
    Rate limit: 3 per hour.
    """
    svc = _get_wallet_service(db)
    try:
        result = await svc.create_wallet(
            wallet_type=body.wallet_type,
            user_id=current_user.id,
        )
    except Exception as exc:
        logger.error("Wallet creation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "WALLET_CREATION_FAILED",
                    "message": "Failed to create wallet",
                    "details": {"reason": str(exc)},
                }
            },
        )

    return CreateWalletResponse(
        wallet_id=result["wallet_id"],
        address=result["address"],
        mnemonic=result["mnemonic"],
        derivation_path=result["derivation_path"],
    )


@router.get(
    "/{wallet_id}/balance",
    response_model=WalletBalanceResponse,
)
@limiter.limit("30/minute")
async def get_wallet_balance(
    request: Request,
    wallet_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get ETH, USDC and USDT balances for a wallet.

    Only the wallet owner can query the balance.
    """
    svc = _get_wallet_service(db)
    wallet = await svc.get_wallet(wallet_id)

    if wallet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "WALLET_NOT_FOUND",
                    "message": "Wallet not found",
                    "details": {"wallet_id": wallet_id},
                }
            },
        )

    _assert_wallet_owner(wallet, current_user)

    try:
        balance = await svc.get_balance(wallet.public_address)
    except Exception as exc:
        logger.error("Balance query failed for %s: %s", wallet_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": {
                    "code": "BALANCE_QUERY_FAILED",
                    "message": "Failed to query on-chain balance",
                    "details": {"reason": str(exc)},
                }
            },
        )

    return WalletBalanceResponse(
        address=balance["address"],
        eth=balance["eth"],
        usdc=balance["usdc"],
        usdt=balance["usdt"],
    )


@router.post(
    "/import",
    response_model=ImportWalletResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("3/hour")
async def import_wallet(
    request: Request,
    body: ImportWalletRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Import a wallet from an existing BIP39 mnemonic.

    Rate limit: 3 per hour.
    """
    svc = _get_wallet_service(db)
    try:
        result = await svc.import_wallet(
            mnemonic_phrase=body.mnemonic,
            derivation_path=body.derivation_path,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "WALLET_IMPORT_FAILED",
                    "message": str(exc),
                    "details": {},
                }
            },
        )
    except Exception as exc:
        logger.error("Wallet import failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "WALLET_IMPORT_ERROR",
                    "message": "Failed to import wallet",
                    "details": {"reason": str(exc)},
                }
            },
        )

    return ImportWalletResponse(
        wallet_id=result["wallet_id"],
        address=result["address"],
        derivation_path=result["derivation_path"],
    )


@router.post(
    "/{wallet_id}/sign",
    response_model=SignMessageResponse,
)
@limiter.limit("10/minute")
async def sign_message(
    request: Request,
    wallet_id: str,
    body: SignMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sign a plaintext message with the wallet's private key.

    Only the wallet owner can sign. Rate limit: 10 per minute.
    """
    svc = _get_wallet_service(db)
    wallet = await svc.get_wallet(wallet_id)

    if wallet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "WALLET_NOT_FOUND",
                    "message": "Wallet not found",
                    "details": {"wallet_id": wallet_id},
                }
            },
        )

    _assert_wallet_owner(wallet, current_user)

    try:
        signature = await svc.sign_message(wallet_id, body.message)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "SIGNING_FAILED",
                    "message": str(exc),
                    "details": {},
                }
            },
        )
    except Exception as exc:
        logger.error("Signing failed for wallet %s: %s", wallet_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SIGNING_ERROR",
                    "message": "Failed to sign message",
                    "details": {"reason": str(exc)},
                }
            },
        )

    return SignMessageResponse(wallet_id=wallet_id, signature=signature)


@router.get(
    "/my",
    response_model=List[WalletSummary],
)
@limiter.limit("30/minute")
async def list_my_wallets(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all wallets owned by the current user.

    Private keys and mnemonic hashes are never included.
    """
    wallets = (
        db.query(Wallet)
        .filter(Wallet.user_id == current_user.id)
        .order_by(Wallet.created_at.desc())
        .all()
    )

    return [
        WalletSummary(
            wallet_id=w.wallet_id,
            address=w.public_address,
            wallet_type=w.wallet_type,
            activation_status=w.activation_status,
            derivation_path=w.derivation_path,
        )
        for w in wallets
    ]
