"""
Script para sembrar los tipos e impuestos venezolanos por defecto.

Ejecutar: python3 seed_venezuelan_taxes.py
"""

import sys
sys.path.insert(0, '/home/muentes/devs/erp')

from sqlalchemy.orm import Session
from database import engine, SessionLocal
# Import models from the models package
import models
from models import TaxType, Tax, Company
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_tax_types_and_taxes_for_company(db: Session, company_id: int):
    """
    Sembrar tax types y taxes para una empresa específica.
    """

    # Verificar que la empresa existe
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        logger.error(f"Company {company_id} not found")
        return

    logger.info(f"Seeding taxes for company: {company.name} (ID: {company_id})")

    # ==================== TAX TYPES (Categorías) ====================

    tax_types_data = [
        {"code": "1", "description": "General", "name": "General", "aliquot": 16, "fiscal_printer_position": 1, "status": True},
        {"code": "2", "description": "Reducida", "name": "Reducida", "aliquot": 8, "fiscal_printer_position": 2, "status": True},
        {"code": "3", "description": "General + Adicional", "name": "General + Adicional", "aliquot": 31, "fiscal_printer_position": 3, "status": True},
        {"code": "4", "description": "Exento", "name": "Exento", "aliquot": 0, "fiscal_printer_position": 0, "status": True},
        {"code": "5", "description": "Alicuota General + Adicional Decreto 3085", "name": "Decreto 3085 Gen+Adic", "aliquot": 9, "fiscal_printer_position": 3, "status": False},
        {"code": "6", "description": "Alicuota Reducida Decreto 3085", "name": "Decreto 3085 Reducida", "aliquot": 7, "fiscal_printer_position": 2, "status": False},
        {"code": "7", "description": "Percibido", "name": "Percibido", "aliquot": 0, "fiscal_printer_position": 4, "status": True},
    ]

    tax_type_map = {}  # Map code -> ID

    for tt_data in tax_types_data:
        # Check if already exists
        existing = db.query(TaxType).filter(
            TaxType.company_id == company_id,
            TaxType.code == tt_data["code"]
        ).first()

        if existing:
            logger.info(f"  TaxType {tt_data['code']} already exists, skipping")
            tax_type_map[tt_data["code"]] = existing.id
            continue

        tax_type = TaxType(
            company_id=company_id,
            **tt_data
        )
        db.add(tax_type)
        db.flush()
        tax_type_map[tt_data["code"]] = tax_type.id
        logger.info(f"  Created TaxType: {tt_data['code']} - {tt_data['description']}")

    # ==================== TAXES (Códigos específicos) ====================

    taxes_data = [
        {"code": "01", "description": "Alicuota General", "short_description": "16%", "aliquot": 16, "tax_type_id": tax_type_map["1"]},
        {"code": "02", "description": "Alicuota General + Adicional", "short_description": "31%", "aliquot": 31, "tax_type_id": tax_type_map["3"]},
        {"code": "03", "description": "Alicuota Reducida", "short_description": "8%", "aliquot": 8, "tax_type_id": tax_type_map["2"]},
        {"code": "EX", "description": "Exento", "short_description": "Exento", "aliquot": 0, "tax_type_id": tax_type_map["4"]},
        {"code": "04", "description": "Alicuota Decreto 3085", "short_description": "9%", "aliquot": 9, "tax_type_id": tax_type_map["5"], "status": False},
        {"code": "05", "description": "Alicuota Decreto 3085", "short_description": "7%", "aliquot": 7, "tax_type_id": tax_type_map["6"], "status": False},
        {"code": "06", "description": "Percibido", "short_description": "Percibido", "aliquot": 0, "tax_type_id": tax_type_map["7"]},
    ]

    for tax_data in taxes_data:
        # Check if already exists
        existing = db.query(Tax).filter(
            Tax.company_id == company_id,
            Tax.code == tax_data["code"]
        ).first()

        if existing:
            logger.info(f"  Tax {tax_data['code']} already exists, skipping")
            continue

        # Set status for active taxes
        if "status" not in tax_data:
            tax_data["status"] = True

        tax = Tax(
            company_id=company_id,
            **tax_data
        )
        db.add(tax)
        logger.info(f"  Created Tax: {tax_data['code']} - {tax_data['description']} ({tax_data['aliquot']}%)")

    db.commit()
    logger.info(f"✅ Successfully seeded taxes for company {company_id}")


def main():
    db = SessionLocal()

    try:
        # Get all companies
        companies = db.query(Company).all()

        if not companies:
            logger.error("No companies found in database")
            return

        logger.info(f"Found {len(companies)} companies")

        for company in companies:
            seed_tax_types_and_taxes_for_company(db, company.id)

        logger.info("✅ All companies seeded successfully!")

    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
