from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends,HTTPException,status
from schemas import Login, Token
from auth import get_user, verify_password, create_access_token,verify_token
from datetime import timedelta
from models import fake_users_db
from models import User
from sqlalchemy.orm import Session
import database
import crud
from config import  ACCESS_TOKEN_EXPIRE_MINUTES


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


router = APIRouter()


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    print(payload)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = get_user(fake_users_db, payload["sub"])
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user



# Endpoint protegido que requiere autenticación
@router.get("/users/me")
def read_users_me(payload: dict = Depends(verify_token)):
    username = payload 
    return {"username": username}


@router.post("/users/")
def create_new_user(username: str, password: str, db: Session = Depends(database.get_db)):
    db_user = crud.create_user(db=db, username=username, password=password)
    return {"id": db_user.id, "username": db_user.username}


@router.post("/login/", response_model=Token)
def login(username: str, password: str, db: Session = Depends(database.get_db)):
    user =  crud.authenticate_user(db=db, username=username, password=password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generar el token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    
    # Devuelve el token generado
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"msg": f"Hello {current_user.username}"}