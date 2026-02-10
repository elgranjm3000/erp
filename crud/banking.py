"""
CRUD de Conciliación Bancaria Multimoneda
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

import models
from models.banking import BankAccount, BankTransaction
from crud.base import verify_company_ownership


def create_bank_account(
    db: Session,
    account_data: dict,
    company_id: int,
    user_id: int
) -> BankAccount:
    """Crear cuenta bancaria"""
    # Verificar que la moneda pertenezca a la empresa
    currency = verify_company_ownership(
        db=db,
        model_class=models.Currency,
        item_id=account_data['currency_id'],
        company_id=company_id,
        error_message="Currency not found in your company"
    )

    # Crear cuenta
    account = BankAccount(
        company_id=company_id,
        currency_id=account_data['currency_id'],
        account_number=account_data['account_number'],
        account_type=account_data.get('account_type', 'corriente'),
        bank_name=account_data['bank_name'],
        bank_code=account_data.get('bank_code'),
        balance=Decimal(str(account_data.get('balance', 0))),
        is_default=account_data.get('is_default', False),
        notes=account_data.get('notes'),
        balance_last_updated=datetime.now(),
        created_by=user_id
    )

    # Si es por defecto, quitar default a otras cuentas de la misma moneda
    if account.is_default:
        db.query(BankAccount).filter(
            BankAccount.company_id == company_id,
            BankAccount.currency_id == account.currency_id,
            BankAccount.id != account.id
        ).update({"is_default": False})

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


def create_bank_transaction(
    db: Session,
    transaction_data: dict,
    company_id: int,
    user_id: int
) -> BankTransaction:
    """Crear transacción bancaria"""
    # Verificar cuenta
    account = verify_company_ownership(
        db=db,
        model_class=BankAccount,
        item_id=transaction_data['bank_account_id'],
        company_id=company_id,
        error_message="Bank account not found"
    )

    # Crear transacción
    transaction = BankTransaction(
        company_id=company_id,
        bank_account_id=transaction_data['bank_account_id'],
        currency_id=account.currency_id,
        transaction_type=transaction_data['transaction_type'],
        amount=Decimal(str(transaction_data['amount'])),
        description=transaction_data['description'],
        reference_number=transaction_data.get('reference_number'),
        transaction_date=transaction_data['transaction_date'],
        related_invoice_id=transaction_data.get('related_invoice_id'),
        related_purchase_id=transaction_data.get('related_purchase_id'),
        recorded_by=user_id
    )

    # Calcular monto en moneda base si es diferente
    base_currency = db.query(models.Currency).filter(
        models.Currency.company_id == company_id,
        models.Currency.is_base_currency == True
    ).first()

    if base_currency and account.currency_id != base_currency.id:
        # Obtener tasa de cambio
        from services.currency_business_service import CurrencyService
        currency_service = CurrencyService(db)

        rate, _ = currency_service.get_exchange_rate_with_metadata(
            from_currency=account.currency.code,
            to_currency=base_currency.code,
            company_id=company_id
        )

        transaction.exchange_rate = rate
        transaction.exchange_rate_date = datetime.now()
        transaction.base_currency_amount = Decimal(str(transaction_data['amount'])) * rate
    else:
        transaction.base_currency_amount = Decimal(str(transaction_data['amount']))

    db.add(transaction)

    # Actualizar saldo de la cuenta
    if transaction.transaction_type in ['credit', 'transfer_in']:
        account.balance += transaction.amount
    else:
        account.balance -= transaction.amount

    account.balance_last_updated = datetime.now()

    db.commit()
    db.refresh(transaction)

    return transaction


def get_bank_accounts(
    db: Session,
    company_id: int,
    currency_id: Optional[int] = None
) -> List[BankAccount]:
    """Obtener cuentas bancarias"""
    query = db.query(BankAccount).filter(
        BankAccount.company_id == company_id,
        BankAccount.is_active == True
    )

    if currency_id:
        query = query.filter(BankAccount.currency_id == currency_id)

    return query.order_by(BankAccount.bank_name).all()


def get_consolidated_balance(
    db: Session,
    company_id: int
) -> dict:
    """Obtiene saldo consolidado por moneda y total en moneda base."""
    accounts = db.query(BankAccount).filter(
        BankAccount.company_id == company_id,
        BankAccount.is_active == True
    ).all()

    # Agrupar por moneda
    balances_by_currency = {}
    total_in_base = Decimal("0")

    base_currency = db.query(models.Currency).filter(
        models.Currency.company_id == company_id,
        models.Currency.is_base_currency == True
    ).first()

    for account in accounts:
        currency_code = account.currency.code
        if currency_code not in balances_by_currency:
            balances_by_currency[currency_code] = {
                "currency_id": account.currency_id,
                "currency_code": currency_code,
                "currency_symbol": account.currency.symbol,
                "balance": Decimal("0"),
                "accounts": []
            }

        balances_by_currency[currency_code]["balance"] += account.balance
        balances_by_currency[currency_code]["accounts"].append({
            "account_id": account.id,
            "bank_name": account.bank_name,
            "account_number": account.account_number,
            "balance": float(account.balance)
        })

        # Convertir a moneda base
        if base_currency and account.currency_id != base_currency.id:
            from services.currency_business_service import CurrencyService
            currency_service = CurrencyService(db)

            rate, _ = currency_service.get_exchange_rate_with_metadata(
                from_currency=currency_code,
                to_currency=base_currency.code,
                company_id=company_id
            )

            total_in_base += account.balance * rate
        elif base_currency and account.currency_id == base_currency.id:
            total_in_base += account.balance

    return {
        "balances_by_currency": [
            {
                **balances_by_currency[code],
                "balance": float(balances_by_currency[code]["balance"])
            }
            for code in balances_by_currency
        ],
        "total_in_base_currency": float(total_in_base),
        "base_currency_code": base_currency.code if base_currency else None
    }
