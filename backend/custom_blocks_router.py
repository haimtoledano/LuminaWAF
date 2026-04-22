from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, CustomBlock, User
from auth import require_admin

custom_blocks_router = APIRouter(prefix="/api/custom-blocks", tags=["Custom Blocks"])

class CustomBlockCreate(BaseModel):
    vs_id: Optional[str] = None
    ip_address: Optional[str] = None
    path_pattern: Optional[str] = None
    notes: Optional[str] = None

class CustomBlockRead(BaseModel):
    id: str
    vs_id: Optional[str] = None
    ip_address: Optional[str] = None
    path_pattern: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True

@custom_blocks_router.get("/", response_model=List[CustomBlockRead], summary="List all custom blocks")
def list_custom_blocks(db: Session = Depends(get_db)):
    rules = db.query(CustomBlock).all()
    return rules

@custom_blocks_router.post("/", response_model=CustomBlockRead, status_code=status.HTTP_201_CREATED, summary="Create a new custom block")
def create_custom_block(rule_data: CustomBlockCreate, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    if not rule_data.ip_address and not rule_data.path_pattern:
        raise HTTPException(status_code=400, detail="Must provide either ip_address or path_pattern")
        
    new_rule = CustomBlock(
        vs_id=rule_data.vs_id,
        ip_address=rule_data.ip_address,
        path_pattern=rule_data.path_pattern,
        notes=rule_data.notes
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    
    # Rely on the 10-second health check loop automatically picking up state changes in IPRules and CustomBlocks
    return new_rule

@custom_blocks_router.delete("/{rule_id}", summary="Delete a custom block")
def delete_custom_block(rule_id: str, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    rule = db.query(CustomBlock).filter(CustomBlock.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Custom block not found")
        
    db.delete(rule)
    db.commit()
    return {"status": "deleted"}

class CustomBlockUpdate(BaseModel):
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    ip_address: Optional[str] = None
    path_pattern: Optional[str] = None

@custom_blocks_router.patch("/{rule_id}", response_model=CustomBlockRead, summary="Update a custom block")
def update_custom_block(rule_id: str, update_data: CustomBlockUpdate, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    rule = db.query(CustomBlock).filter(CustomBlock.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Custom block not found")
        
    if update_data.is_active is not None:
        rule.is_active = update_data.is_active
    if update_data.notes is not None:
        rule.notes = update_data.notes
    if update_data.ip_address is not None:
        rule.ip_address = update_data.ip_address
    if update_data.path_pattern is not None:
        rule.path_pattern = update_data.path_pattern
        
    db.commit()
    db.refresh(rule)
    return rule
