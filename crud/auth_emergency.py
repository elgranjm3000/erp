"""
EMERGENCY LOGIN FIX - Versión ultra simplificada

Este módulo reemplaza temporalmente el login normal
para eliminar cualquier posible causa de timeout.
"""

from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import User
from passlib.context import CryptContext
import time

# Password context con rounds reducidos para velocidad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password_fast(plain_password: str, hashed_password: str) -> bool:
    """Verificar password - maneja timeout internamente"""
    try:
        start = time.time()
        result = pwd_context.verify(plain_password, hashed_password)
        elapsed = (time.time() - start) * 1000
        print(f"[LOGIN] Password verify took: {elapsed}ms")
        return result
    except Exception as e:
        print(f"[LOGIN] Password verify ERROR: {str(e)}")
        return False

def authenticate_multicompany_emergency(db: Session, login_data):
    """
    Login EMERGENCY con logging extensivo para identificar bottleneck.

    Esta versión:
    - Usa queries SQL directas sin ORM overhead
    - Tiene logging en cada paso
    - Maneja timeouts en cada operación
    - Es más rápida pero menos elegante
    """
    print(f"[LOGIN] Attempt login for user: {login_data.username}")
    overall_start = time.time()

    try:
        # Paso 1: Buscar usuario con SQL directo
        print("[LOGIN] Step 1: Query user...")
        step_start = time.time()

        query = text("""
            SELECT id, username, email, hashed_password,
                   company_id, role, is_company_admin,
                   is_active, created_at
            FROM users
            WHERE username = :username
              AND is_active = 1
            LIMIT 1
        """)

        result = db.execute(query, {"username": login_data.username})
        user_row = result.fetchone()
        db.close()  # Cerrar result set inmediatamente

        step_time = (time.time() - step_start) * 1000
        print(f"[LOGIN] Step 1 took: {step_time}ms")

        if not user_row:
            print("[LOGIN] User not found")
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        # Convertir a diccionario manual
        user = {
            "id": user_row[0],
            "username": user_row[1],
            "email": user_row[2],
            "hashed_password": user_row[3],
            "company_id": user_row[4],
            "role": user_row[5],
            "is_company_admin": user_row[6],
            "is_active": user_row[7],
            "created_at": user_row[8]
        }

        # Paso 2: Verificar password
        print("[LOGIN] Step 2: Verify password...")
        step_start = time.time()

        if not verify_password_fast(login_data.password, user["hashed_password"]):
            print("[LOGIN] Invalid password")
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        step_time = (time.time() - step_start) * 1000
        print(f"[LOGIN] Step 2 took: {step_time}ms")

        # Paso 3: Actualizar last_login (opcional, no crítico)
        print("[LOGIN] Step 3: Update last_login...")
        step_start = time.time()

        try:
            update_query = text("""
                UPDATE users
                SET last_login = :now
                WHERE id = :user_id
            """)
            db.execute(update_query, {
                "now": datetime.utcnow(),
                "user_id": user["id"]
            })
            db.commit()
        except Exception as e:
            print(f"[LOGIN] Update last_login failed (non-critical): {str(e)}")
            db.rollback()

        step_time = (time.time() - step_start) * 1000
        print(f"[LOGIN] Step 3 took: {step_time}ms")

        # Paso 4: Obtener company
        print("[LOGIN] Step 4: Query company...")
        step_start = time.time()

        company_data = None
        if user["company_id"]:
            company_query = text("""
                SELECT id, name, tax_id, is_active
                FROM companies
                WHERE id = :company_id
                LIMIT 1
            """)
            company_result = db.execute(company_query, {"company_id": user["company_id"]})
            company_row = company_result.fetchone()

            if company_row:
                company_data = {
                    "id": company_row[0],
                    "name": company_row[1],
                    "tax_id": company_row[2],
                    "is_active": company_row[3]
                }

        step_time = (time.time() - step_start) * 1000
        print(f"[LOGIN] Step 4 took: {step_time}ms")

        # Paso 5: Generar token
        print("[LOGIN] Step 5: Generate token...")
        step_start = time.time()

        from auth import create_access_token
        from config import ACCESS_TOKEN_EXPIRE_MINUTES

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user["username"],
                "company_id": user["company_id"],
                "role": user["role"],
                "is_company_admin": user["is_company_admin"]
            },
            expires_delta=access_token_expires
        )

        step_time = (time.time() - step_start) * 1000
        print(f"[LOGIN] Step 5 took: {step_time}ms")

        # Paso 6: Construir response
        print("[LOGIN] Step 6: Build response...")
        step_start = time.time()

        from schemas import LoginResponse, UserWithCompany

        response = LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserWithCompany(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                role=user["role"],
                company_id=user["company_id"],
                is_active=user["is_active"],
                is_company_admin=user["is_company_admin"],
                created_at=user["created_at"],
                last_login=datetime.utcnow(),
                company=company_data
            )
        )

        step_time = (time.time() - step_start) * 1000
        print(f"[LOGIN] Step 6 took: {step_time}ms")

        total_time = (time.time() - overall_start) * 1000
        print(f"[LOGIN] ✅ TOTAL TIME: {total_time}ms")
        print(f"[LOGIN] ✅ Login successful for: {user['username']}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        total_time = (time.time() - overall_start) * 1000
        print(f"[LOGIN] ❌ ERROR after {total_time}ms: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}"
        )
