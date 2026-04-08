from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from database import get_db, User, UserRole
from auth import require_admin, get_password_hash

users_router = APIRouter()

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserRead(BaseModel):
    id: str
    username: str
    role: str
    mfa_enabled: bool

@users_router.get("/", response_model=List[UserRead], summary="List all users")
def list_users(db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    users = db.query(User).all()
    return [{"id": str(u.id), "username": u.username, "role": u.role.value, "mfa_enabled": u.mfa_enabled} for u in users]

@users_router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Create a new user")
def create_user(new_user_data: UserCreate, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    if len(new_user_data.password) < 4:
        raise HTTPException(status_code=400, detail="Password too short")
    existing_user = db.query(User).filter(User.username == new_user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
        
    hashed_password = get_password_hash(new_user_data.password)
    
    new_user = User(
        username=new_user_data.username,
        role=UserRole(new_user_data.role),
        hashed_password=hashed_password,
        mfa_enabled=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"id": str(new_user.id), "username": new_user.username, "role": new_user.role.value, "mfa_enabled": new_user.mfa_enabled}

@users_router.delete("/{user_id}", summary="Delete a user by ID")
def delete_user(user_id: str, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user_to_delete.id == current_admin.id:
        raise HTTPException(status_code=403, detail="Cannot delete your own admin account")
        
    db.delete(user_to_delete)
    db.commit()
    return {"status": "deleted"}
