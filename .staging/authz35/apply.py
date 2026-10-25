from pathlib import Path

ROOT=Path('/runtime')
MODELS=ROOT/'backend/app/models.py'
MAIN=ROOT/'backend/app/main.py'


def replace_once(text, old, new, label):
    count=text.count(old)
    if count != 1:
        raise SystemExit(f'authz35 patch mismatch for {label}: expected 1 match, found {count}')
    return text.replace(old,new,1)

models=MODELS.read_text()
models=replace_once(
    models,
    "    company_id: Mapped[str] = mapped_column(ForeignKey('companies.id'), index=True)\n    first_name: Mapped[str] = mapped_column(String)\n",
    "    company_id: Mapped[str] = mapped_column(ForeignKey('companies.id'), index=True)\n    assigned_user_id: Mapped[str|None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), index=True, nullable=True)\n    first_name: Mapped[str] = mapped_column(String)\n",
    'Lead.assigned_user_id',
)
MODELS.write_text(models)

main=MAIN.read_text()

old_tenant="""def tenant_lead(db:Session,u:User,lead_id:str):
    lead=db.get(Lead,lead_id)
    if not lead: raise HTTPException(404,'Lead not found')
    same_company(u,lead.company_id); return lead
"""
new_tenant="""def visible_leads_query(db:Session,u:User):
    q=db.query(Lead).filter(Lead.company_id==u.company_id)
    if u.role.upper()!='OWNER':
        q=q.filter(Lead.assigned_user_id==u.id)
    return q

def tenant_lead(db:Session,u:User,lead_id:str):
    lead=db.get(Lead,lead_id)
    if not lead: raise HTTPException(404,'Lead not found')
    same_company(u,lead.company_id)
    if u.role.upper()!='OWNER' and lead.assigned_user_id!=u.id:
        raise HTTPException(404,'Lead not found')
    return lead
"""
main=replace_once(main,old_tenant,new_tenant,'tenant lead guard')

# Replace every company-wide Lead query with the visibility-scoped helper.
main=main.replace("db.query(Lead).filter(Lead.company_id==u.company_id)", "visible_leads_query(db,u)")

old_create="""@app.post('/api/leads')
def secure_create_lead(data:LeadIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    lead=Lead(company_id=u.company_id,**data.model_dump()); db.add(lead); db.flush(); audit(db,u.company_id,'LEAD_CREATED',lead.id,u.id,f'{data.first_name} {data.last_name}'); db.commit(); db.refresh(lead); return lead_view(lead)
"""
new_create="""@app.post('/api/leads')
def secure_create_lead(data:LeadIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    lead=Lead(company_id=u.company_id,assigned_user_id=u.id,**data.model_dump()); db.add(lead); db.flush(); audit(db,u.company_id,'LEAD_CREATED',lead.id,u.id,f'{data.first_name} {data.last_name}'); db.commit(); db.refresh(lead); return lead_view(lead)
"""
main=replace_once(main,old_create,new_create,'new lead assignment')

user_model="class UserIn(BaseModel): name: str; email: str; role: str='REP'"
main=replace_once(
    main,
    user_model,
    user_model+"\nclass LeadAssignmentIn(BaseModel): assigned_user_id: str",
    'assignment input model',
)

old_users="""@app.get('/api/users')
def secure_users(u:User=Depends(require_roles(*MANAGEMENT_ROLES)),db:Session=Depends(get_db)):
    rows=db.query(User).filter(User.company_id==u.company_id).order_by(User.name).all()
    return [{'id':x.id,'name':x.name,'email':x.email,'role':x.role,'active':x.active} for x in rows]
"""
new_users="""@app.get('/api/users')
def secure_users(u:User=Depends(require_roles('OWNER')),db:Session=Depends(get_db)):
    rows=db.query(User).filter(User.company_id==u.company_id).order_by(User.name).all()
    return [{'id':x.id,'name':x.name,'email':x.email,'role':x.role,'active':x.active} for x in rows]

@app.patch('/api/leads/{lead_id}/assignment')
def secure_assign_lead(lead_id:str,data:LeadAssignmentIn,u:User=Depends(require_roles('OWNER')),db:Session=Depends(get_db)):
    lead=tenant_lead(db,u,lead_id)
    target=db.get(User,data.assigned_user_id)
    if not target or target.company_id!=u.company_id or not target.active:
        raise HTTPException(400,'Invalid assignee')
    lead.assigned_user_id=target.id
    audit(db,u.company_id,'LEAD_ASSIGNED',lead.id,u.id,f'assigned to {target.email}')
    db.commit(); db.refresh(lead)
    result=lead_view(lead); result['assigned_user_id']=lead.assigned_user_id
    return result
"""
main=replace_once(main,old_users,new_users,'owner-only user list and assignment endpoint')

old_create_user="""@app.post('/api/users')
def secure_create_user(data:UserIn,u:User=Depends(require_roles(*ADMIN_ROLES)),db:Session=Depends(get_db)):
    role=data.role.upper()
    if role not in ('OWNER','ADMIN','MANAGER','REP'): raise HTTPException(400,'Invalid role')
    if db.query(User).filter(User.email==data.email).first(): raise HTTPException(409,'Email already exists')
    row=User(company_id=u.company_id,name=data.name,email=data.email,role=role,active=True)
    db.add(row); audit(db,u.company_id,'USER_CREATED',user_id=u.id,detail=f'{data.email} ({role})'); db.commit(); db.refresh(row)
    return {'id':row.id,'name':row.name,'email':row.email,'role':row.role,'active':row.active}
"""
new_create_user="""@app.post('/api/users')
def secure_create_user(data:UserIn,u:User=Depends(require_roles('OWNER')),db:Session=Depends(get_db)):
    role=data.role.upper()
    if role not in ('ADMIN','MANAGER','REP'): raise HTTPException(400,'Additional users cannot have OWNER access')
    if db.query(User).filter(User.email==data.email).first(): raise HTTPException(409,'Email already exists')
    row=User(company_id=u.company_id,name=data.name,email=data.email,role=role,active=True)
    db.add(row); audit(db,u.company_id,'USER_CREATED',user_id=u.id,detail=f'{data.email} ({role})'); db.commit(); db.refresh(row)
    return {'id':row.id,'name':row.name,'email':row.email,'role':row.role,'active':row.active}
"""
main=replace_once(main,old_create_user,new_create_user,'owner-only user creation')

# Include assignment in standard lead JSON when the simple lead_view literal is present.
main=main.replace("'status':l.status,'created_at':l.created_at", "'status':l.status,'assigned_user_id':l.assigned_user_id,'created_at':l.created_at")
main=main.replace("'status':x.status,'created_at':x.created_at", "'status':x.status,'assigned_user_id':x.assigned_user_id,'created_at':x.created_at")

MAIN.write_text(main)
print('authz35: owner-only user management enabled')
print('authz35: non-owner lead visibility restricted to assigned_user_id')
print('authz35: new leads auto-assigned to creator; owner assignment endpoint enabled')
