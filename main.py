from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db import Base, engine, get_db
import re, secrets

app = FastAPI()

# ------------------ MODELS ------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    reset_token = Column(String, nullable=True)


# ------------------ SCHEMAS ------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgetPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str


# ------------------ UTILS ------------------
def validate_password(password: str):
    """
    Password must contain:
    - First letter capital
    - At least 1 number
    - At least 1 '@'
    """
    if not password[0].isupper():
        return False
    if "@" not in password:
        return False
    if not any(ch.isdigit() for ch in password):
        return False
    return True


# ------------------ API ------------------
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def read_root():
    return {"message": "Welcome to the User Management API"}

@app.post("/signup")
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    if not validate_password(user.password):
        raise HTTPException(
            status_code=400,
            detail="Password must start with a capital letter, contain '@' and at least one number."
        )

    q = await db.execute(select(User).where(User.email == user.email))
    existing_user = q.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(email=user.email, password=user.password)
    db.add(new_user)
    await db.commit()
    return {"message": "User registered successfully"}


@app.post("/signin")
async def signin(user: UserLogin, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.email == user.email))
    db_user = q.scalars().first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful"}


@app.post("/forget-password")
async def forget_password(data: ForgetPassword, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.email == data.email))
    db_user = q.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Email not found")

    token = secrets.token_hex(16)
    db_user.reset_token = token
    await db.commit()
    return {"reset_token": token}


@app.post("/reset-password")
async def reset_password(data: ResetPassword, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.reset_token == data.token))
    db_user = q.scalars().first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid token")

    if not validate_password(data.new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must start with a capital letter, contain '@' and at least one number."
        )

    db_user.password = data.new_password
    db_user.reset_token = None
    await db.commit()
    return {"message": "Password reset successfully"}
