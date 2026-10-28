"""
Payment service for credit-based billing.

All money operations use DB transactions for atomicity.
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from models.payment import CreditAccount, CreditTransaction, TransactionType
import logging

logger = logging.getLogger(__name__)


class InsufficientBalanceError(Exception):
    """Raised when account balance is insufficient for a charge."""
    def __init__(self, balance: float, amount: float):
        self.balance = balance
        self.amount = amount
        super().__init__(f"Insufficient balance: {balance} < {amount}")


class PaymentService:
    """Credit-based payment service for B2B clients."""

    @staticmethod
    def get_or_create_account(db: Session, user_id: int) -> CreditAccount:
        """Get existing account or create a new one for the user."""
        account = db.query(CreditAccount).filter(
            CreditAccount.user_id == user_id
        ).first()

        if not account:
            account = CreditAccount(
                user_id=user_id,
                balance=0.0,
                total_deposited=0.0,
                total_spent=0.0,
            )
            db.add(account)
            db.flush()
            logger.info(f"Created credit account for user {user_id}")

        return account

    @staticmethod
    def deposit(
        db: Session,
        user_id: int,
        amount: float,
        description: str = "",
    ) -> CreditTransaction:
        """
        Deposit credits into a user's account.

        Args:
            db: Database session
            user_id: Target user ID
            amount: Amount to deposit (must be positive)
            description: Human-readable description

        Returns:
            The created CreditTransaction
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")

        account = PaymentService.get_or_create_account(db, user_id)

        account.balance += amount
        account.total_deposited += amount
        account.updated_at = datetime.utcnow()

        tx = CreditTransaction(
            account_id=account.id,
            transaction_type=TransactionType.DEPOSIT.value,
            amount=amount,
            balance_after=account.balance,
            description=description,
        )
        db.add(tx)
        db.commit()

        logger.info(
            f"Deposit: user={user_id}, amount={amount}, "
            f"balance_after={account.balance}"
        )
        return tx

    @staticmethod
    def charge(
        db: Session,
        user_id: int,
        amount: float,
        task_id: str,
        description: str = "",
    ) -> CreditTransaction:
        """
        Charge credits for a task.

        Args:
            db: Database session
            user_id: User to charge
            amount: Amount to charge (must be positive)
            task_id: Associated task ID
            description: Human-readable description

        Returns:
            The created CreditTransaction

        Raises:
            InsufficientBalanceError: If balance < amount
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Charge amount must be positive")

        account = PaymentService.get_or_create_account(db, user_id)

        if account.balance < amount:
            raise InsufficientBalanceError(account.balance, amount)

        account.balance -= amount
        account.total_spent += amount
        account.updated_at = datetime.utcnow()

        tx = CreditTransaction(
            account_id=account.id,
            transaction_type=TransactionType.TASK_CHARGE.value,
            amount=-amount,
            balance_after=account.balance,
            description=description,
            task_id=task_id,
        )
        db.add(tx)
        db.commit()

        logger.info(
            f"Charge: user={user_id}, amount={amount}, task={task_id}, "
            f"balance_after={account.balance}"
        )
        return tx

    @staticmethod
    def refund(
        db: Session,
        user_id: int,
        amount: float,
        task_id: str,
        description: str = "",
    ) -> CreditTransaction:
        """
        Refund credits for a task.

        Args:
            db: Database session
            user_id: User to refund
            amount: Amount to refund (must be positive)
            task_id: Associated task ID
            description: Human-readable description

        Returns:
            The created CreditTransaction
        """
        if amount <= 0:
            raise ValueError("Refund amount must be positive")

        account = PaymentService.get_or_create_account(db, user_id)

        account.balance += amount
        account.total_spent -= amount
        account.updated_at = datetime.utcnow()

        tx = CreditTransaction(
            account_id=account.id,
            transaction_type=TransactionType.REFUND.value,
            amount=amount,
            balance_after=account.balance,
            description=description,
            task_id=task_id,
        )
        db.add(tx)
        db.commit()

        logger.info(
            f"Refund: user={user_id}, amount={amount}, task={task_id}, "
            f"balance_after={account.balance}"
        )
        return tx

    @staticmethod
    def get_balance(db: Session, user_id: int) -> float:
        """Get current credit balance for a user."""
        account = PaymentService.get_or_create_account(db, user_id)
        return account.balance

    @staticmethod
    def get_transactions(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get transaction history for a user.

        Args:
            db: Database session
            user_id: User ID
            limit: Max records to return
            offset: Pagination offset
            transaction_type: Optional filter by type

        Returns:
            List of transaction dicts
        """
        account = db.query(CreditAccount).filter(
            CreditAccount.user_id == user_id
        ).first()

        if not account:
            return []

        query = db.query(CreditTransaction).filter(
            CreditTransaction.account_id == account.id
        )

        if transaction_type:
            query = query.filter(
                CreditTransaction.transaction_type == transaction_type
            )

        query = query.order_by(CreditTransaction.created_at.desc())
        query = query.limit(limit).offset(offset)

        transactions = query.all()

        return [
            {
                "id": tx.id,
                "transaction_type": tx.transaction_type,
                "amount": tx.amount,
                "balance_after": tx.balance_after,
                "description": tx.description,
                "task_id": tx.task_id,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
            }
            for tx in transactions
        ]

    @staticmethod
    def get_invoice_summary(
        db: Session,
        user_id: int,
        year: int,
        month: int,
    ) -> Dict:
        """
        Generate a monthly invoice summary.

        Args:
            db: Database session
            user_id: User ID
            year: Invoice year
            month: Invoice month (1-12)

        Returns:
            Invoice summary dict
        """
        account = db.query(CreditAccount).filter(
            CreditAccount.user_id == user_id
        ).first()

        if not account:
            return {
                "user_id": user_id,
                "year": year,
                "month": month,
                "total_deposits": 0.0,
                "total_charges": 0.0,
                "total_refunds": 0.0,
                "net_spend": 0.0,
                "transaction_count": 0,
                "current_balance": 0.0,
            }

        # Query transactions for the given month
        transactions = db.query(CreditTransaction).filter(
            CreditTransaction.account_id == account.id,
            extract("year", CreditTransaction.created_at) == year,
            extract("month", CreditTransaction.created_at) == month,
        ).all()

        total_deposits = sum(
            tx.amount for tx in transactions
            if tx.transaction_type == TransactionType.DEPOSIT.value
        )
        total_charges = sum(
            abs(tx.amount) for tx in transactions
            if tx.transaction_type == TransactionType.TASK_CHARGE.value
        )
        total_refunds = sum(
            tx.amount for tx in transactions
            if tx.transaction_type == TransactionType.REFUND.value
        )

        return {
            "user_id": user_id,
            "year": year,
            "month": month,
            "total_deposits": total_deposits,
            "total_charges": total_charges,
            "total_refunds": total_refunds,
            "net_spend": total_charges - total_refunds,
            "transaction_count": len(transactions),
            "current_balance": account.balance,
        }
