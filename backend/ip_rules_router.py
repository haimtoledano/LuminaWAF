from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, IPRule, User
from auth import require_admin

ip_rules_router = APIRouter(prefix="/api/ip-rules", tags=["IP Rules"])

class IPRuleCreate(BaseModel):
    ip_address: str
    rule_type: str
    notes: Optional[str] = None

class IPRuleRead(BaseModel):
    id: str
    ip_address: str
    rule_type: str
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime

@ip_rules_router.get("/", response_model=List[IPRuleRead], summary="List all IP rules")
def list_ip_rules(db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    rules = db.query(IPRule).all()
    # Pydantic will serialize the ORM objects automatically if configured, or we map manually
    return rules

@ip_rules_router.post("/", response_model=IPRuleRead, status_code=status.HTTP_201_CREATED, summary="Create a new IP rule")
def create_ip_rule(rule_data: IPRuleCreate, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    # Validate IP address format roughly
    import ipaddress
    try:
        ipaddress.ip_address(rule_data.ip_address)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address format")
        
    existing_rule = db.query(IPRule).filter(IPRule.ip_address == rule_data.ip_address).first()
    if existing_rule:
        raise HTTPException(status_code=400, detail="An IP rule for this address already exists")
        
    new_rule = IPRule(
        ip_address=rule_data.ip_address,
        rule_type=rule_data.rule_type,
        notes=rule_data.notes
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@ip_rules_router.delete("/{rule_id}", summary="Delete an IP rule")
def delete_ip_rule(rule_id: str, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    rule = db.query(IPRule).filter(IPRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="IP rule not found")
        
    db.delete(rule)
    db.commit()
    return {"status": "deleted"}

class IPRuleUpdate(BaseModel):
    is_active: Optional[bool] = None
    notes: Optional[str] = None
    ip_address: Optional[str] = None

@ip_rules_router.patch("/{rule_id}", response_model=IPRuleRead, summary="Update an IP rule")
def update_ip_rule(rule_id: str, update_data: IPRuleUpdate, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    rule = db.query(IPRule).filter(IPRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="IP rule not found")
        
    if update_data.is_active is not None:
        rule.is_active = update_data.is_active
    if update_data.notes is not None:
        rule.notes = update_data.notes
    if update_data.ip_address is not None:
        rule.ip_address = update_data.ip_address
        
    db.commit()
    db.refresh(rule)
    return rule
