#!/usr/bin/env python3
"""
Script para configurar actualizaciones automáticas BCV via cron
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models import User, Company
from services.bcv_rate_updater import BCVRateUpdater
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_all_companies():
    """Actualiza tasas BCV para todas las empresas activas."""
    db = SessionLocal()

    try:
        companies = db.query(Company).filter(Company.is_active == True).all()

        for company in companies:
            try:
                admin_user = db.query(User).filter(
                    User.company_id == company.id,
                    User.is_company_admin == True,
                    User.is_active == True
                ).first()

                if not admin_user:
                    logger.warning(f"No admin user found for company {company.id}")
                    continue

                updater = BCVRateUpdater(db, company.id)
                results = updater.update_bcv_currencies(
                    user_id=admin_user.id,
                    force_update=True
                )

                logger.info(
                    f"Company {company.id} ({company.name}): "
                    f"{results['total_updated']} updated, "
                    f"{results['total_failed']} failed"
                )

            except Exception as e:
                logger.error(f"Error updating company {company.id}: {e}")
                db.rollback()

        logger.info("BCV update completed for all companies")

    except Exception as e:
        logger.error(f"Fatal error in BCV update: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    update_all_companies()
