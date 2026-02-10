"""
Excepciones personalizadas para el sistema ERP.
"""

from typing import Optional, Any
from datetime import datetime


class ERPBaseException(Exception):
    """Base exception para todas las excepciones del ERP."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[dict] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convierte la excepción a diccionario para respuesta HTTP"""
        return {
            "error": True,
            "message": self.message,
            "error_code": self.error_code,
            "status_code": self.status_code,
            "details": self.details,
            "timestamp": self.timestamp
        }


class ValidationError(ERPBaseException):
    """Error de validación de datos."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[dict] = None
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field

        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=error_details
        )


class NotFoundError(ERPBaseException):
    """Recurso no encontrado."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        details: Optional[dict] = None
    ):
        error_details = details or {}
        if resource_type:
            error_details["resource_type"] = resource_type
        if resource_id is not None:
            error_details["resource_id"] = str(resource_id)

        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=error_details
        )


class ConflictError(ERPBaseException):
    """Conflicto de datos (ej: duplicado)."""

    def __init__(
        self,
        message: str,
        conflict_type: Optional[str] = None,
        conflicting_field: Optional[str] = None,
        details: Optional[dict] = None
    ):
        error_details = details or {}
        if conflict_type:
            error_details["conflict_type"] = conflict_type
        if conflicting_field:
            error_details["conflicting_field"] = conflicting_field

        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=error_details
        )


class BusinessRuleError(ERPBaseException):
    """Violación de regla de negocio."""

    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        details: Optional[dict] = None
    ):
        error_details = details or {}
        if rule_name:
            error_details["rule_name"] = rule_name

        super().__init__(
            message=message,
            status_code=400,
            error_code="BUSINESS_RULE_VIOLATION",
            details=error_details
        )


class CurrencyError(ERPBaseException):
    """Error específico para operaciones de monedas."""

    def __init__(
        self,
        message: str,
        currency_code: Optional[str] = None,
        details: Optional[dict] = None
    ):
        error_details = details or {}
        if currency_code:
            error_details["currency_code"] = currency_code

        super().__init__(
            message=message,
            status_code=400,
            error_code="CURRENCY_ERROR",
            details=error_details
        )


class CurrencyNotFoundError(NotFoundError):
    """Moneda no encontrada."""

    def __init__(self, currency_code: str, company_id: Optional[int] = None):
        message = f"Currency '{currency_code}' not found"
        if company_id:
            message += f" for company {company_id}"

        super().__init__(
            message=message,
            resource_type="Currency",
            resource_id=currency_code,
            details={"company_id": company_id} if company_id else None
        )


class DuplicateCurrencyError(ConflictError):
    """Moneda duplicada."""

    def __init__(self, currency_code: str, company_id: int):
        super().__init__(
            message=f"Currency '{currency_code}' already exists for company {company_id}",
            conflict_type="Duplicate Currency",
            conflicting_field="code",
            details={
                "currency_code": currency_code,
                "company_id": company_id
            }
        )


class InvalidCurrencyCodeError(ValidationError):
    """Código de moneda inválido."""

    def __init__(self, currency_code: str, reason: str = "Invalid ISO 4217 code"):
        super().__init__(
            message=f"Invalid currency code '{currency_code}': {reason}",
            field="code",
            details={
                "currency_code": currency_code,
                "reason": reason
            }
        )


class InvalidExchangeRateError(ValidationError):
    """Tasa de cambio inválida."""

    def __init__(self, rate: Any, reason: str = "Invalid exchange rate"):
        super().__init__(
            message=f"Invalid exchange rate: {reason}",
            field="exchange_rate",
            details={
                "rate": str(rate),
                "reason": reason
            }
        )


class BaseCurrencyAlreadyExistsError(ConflictError):
    """Ya existe una moneda base."""

    def __init__(self, company_id: int, existing_currency: str):
        super().__init__(
            message=f"Company {company_id} already has a base currency: {existing_currency}",
            conflict_type="Base Currency Exists",
            conflicting_field="is_base_currency",
            details={
                "company_id": company_id,
                "existing_currency": existing_currency
            }
        )


class CannotDeleteBaseCurrencyError(BusinessRuleError):
    """No se puede eliminar la moneda base."""

    def __init__(self, currency_code: str):
        super().__init__(
            message=f"Cannot delete base currency '{currency_code}'. Set another currency as base first.",
            rule_name="Cannot Delete Base Currency",
            details={"currency_code": currency_code}
        )
