from pathlib import Path

ROOT = Path('/runtime')
MAIN = ROOT / 'backend/app/main.py'
CONFIG = ROOT / 'backend/app/config.py'
INDEX = ROOT / 'web/index.html'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'Owner reset patch mismatch for {label}: expected 1 match, found {count}')
    return text.replace(old, new, 1)

cfg = CONFIG.read_text()
cfg = replace_once(
    cfg,
    "    owner_activation_token: str = os.getenv('RB_OWNER_ACTIVATION_TOKEN', '')\n",
    "    owner_activation_token: str = os.getenv('RB_OWNER_ACTIVATION_TOKEN', '')\n    owner_reset_token: str = os.getenv('RB_OWNER_RESET_TOKEN', '')\n",
    'owner reset config',
)
CONFIG.write_text(cfg)

main = MAIN.read_text()
main = replace_once(
    main,
    "path in ('/auth/login','/auth/browser-login','/auth/activate-owner')",
    "path in ('/auth/login','/auth/browser-login','/auth/activate-owner','/auth/reset-owner-password')",
    'public reset route',
)
change_model = "class ChangePasswordIn(BaseModel):\n    current_password:str=Field(min_length=1,max_length=256)\n    new_password:str=Field(min_length=12,max_length=256)\n"
main = replace_once(
    main,
    change_model,
    change_model + "class ResetOwnerPasswordIn(BaseModel):\n    email:str\n    reset_code:str=Field(min_length=24,max_length=256)\n    password:str=Field(min_length=12,max_length=256)\n",
    'reset request model',
)
anchor = "@app.post('/auth/change-password')\ndef change_own_password"
endpoint = """@app.post('/auth/reset-owner-password')
def reset_owner_password(data:ResetOwnerPasswordIn, request:Request, response:Response, db:Session=Depends(get_db)):
    from .rate_limit import limiter
    ip=request.client.host if request.client else 'unknown'
    allowed,retry=limiter.allow('reset-owner:'+ip, 6, 600)
    if not allowed:
        raise HTTPException(429,'Too many reset attempts',headers={'Retry-After':str(retry)})
    configured=settings.owner_reset_token
    if not configured:
        raise HTTPException(404,'Owner password reset is not available')
    if not secrets.compare_digest(data.reset_code,configured):
        raise HTTPException(401,'Invalid reset code')
    token_fingerprint=hashlib.sha256(configured.encode()).hexdigest()
    already=db.query(Activity).filter(Activity.action=='OWNER_PASSWORD_RESET_TOKEN_USED',Activity.detail==token_fingerprint).first()
    if already:
        raise HTTPException(410,'This reset code has already been used')
    email=data.email.strip().lower()
    u=db.query(User).filter(User.email==email,User.active==True).first()
    if not u or u.role.upper()!='OWNER':
        raise HTTPException(404,'Owner account not found')
    try:
        validate_password_strength(data.password)
    except ValueError as e:
        raise HTTPException(400,str(e))
    cred=db.get(UserCredential,u.id)
    if not cred:
        cred=UserCredential(user_id=u.id,password_hash=hash_password(data.password)); db.add(cred)
    else:
        cred.password_hash=hash_password(data.password)
    db.query(AuthSession).filter(AuthSession.user_id==u.id).delete(synchronize_session=False)
    audit(db,u.company_id,'OWNER_PASSWORD_RESET_TOKEN_USED',user_id=u.id,detail=token_fingerprint)
    db.commit()
    token=new_session(db,u.id)
    _set_browser_cookie(response,token)
    response.headers['Cache-Control']='no-store'
    return {'ok':True,'user':{'id':u.id,'company_id':u.company_id,'name':u.name,'email':u.email,'role':u.role}}

"""
main = replace_once(main, anchor, endpoint + anchor, 'reset endpoint')
MAIN.write_text(main)

idx = INDEX.read_text()
idx = replace_once(
    idx,
    '<div class="auth-switch"><button class="auth-link" id="showActivate" type="button">First-time owner setup</button></div></div><div class="auth-box" id="activateBox">',
    '<div class="auth-switch"><button class="auth-link" id="showReset" type="button">Forgot owner password?</button><br><button class="auth-link" id="showActivate" type="button">First-time owner setup</button></div></div><div class="auth-box" id="resetBox"><h3>Reset owner password</h3><p class="muted">Use the one-time reset code sent to you, then choose a new permanent password.</p><form class="auth-form" id="resetForm"><label>Owner email<input id="resetEmail" type="email" value="owner@roofbrokers.local" autocomplete="username" required></label><label>Reset code<input id="resetCode" type="password" autocomplete="one-time-code" required></label><label>New password<input id="resetPassword" type="password" autocomplete="new-password" minlength="12" required></label><label>Confirm password<input id="resetConfirm" type="password" autocomplete="new-password" minlength="12" required></label><div class="muted" style="margin-top:8px">12+ characters with uppercase, lowercase, number, and symbol.</div><button class="primary" type="submit" style="width:100%;margin-top:14px">Reset Password & Sign In</button><p class="muted" id="resetError" aria-live="polite"></p></form><div class="auth-switch"><button class="auth-link" id="resetBackToLogin" type="button">Back to sign in</button></div></div><div class="auth-box" id="activateBox">',
    'reset form',
)
old_show = "function showAuth(which){$('signInBox').classList.toggle('show',which==='login');$('activateBox').classList.toggle('show',which==='activate');$('loginError').textContent='';$('activateError').textContent='';}\n$('showActivate').onclick=()=>showAuth('activate');\n$('backToLogin').onclick=()=>showAuth('login');"
new_show = "function showAuth(which){$('signInBox').classList.toggle('show',which==='login');$('resetBox').classList.toggle('show',which==='reset');$('activateBox').classList.toggle('show',which==='activate');$('loginError').textContent='';$('resetError').textContent='';$('activateError').textContent='';}\n$('showReset').onclick=()=>showAuth('reset');\n$('resetBackToLogin').onclick=()=>showAuth('login');\n$('showActivate').onclick=()=>showAuth('activate');\n$('backToLogin').onclick=()=>showAuth('login');"
idx = replace_once(idx, old_show, new_show, 'auth switch')
reset_js = """$('resetForm').addEventListener('submit',async e=>{e.preventDefault();if($('resetPassword').value!==$('resetConfirm').value){$('resetError').textContent='Passwords do not match';return}$('resetError').textContent='Resetting…';try{const r=await fetch('/auth/reset-owner-password',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:$('resetEmail').value.trim(),reset_code:$('resetCode').value,password:$('resetPassword').value})});if(!r.ok){let m='Reset failed';try{const x=await r.json();m=x.detail||m}catch{}throw new Error(m)}$('resetCode').value='';$('resetPassword').value='';$('resetConfirm').value='';$('login').classList.add('hidden');await loadCompanies();}catch(e){$('resetError').textContent=e.message;}});
"""
idx = replace_once(idx, "$('activateForm').addEventListener", reset_js + "$('activateForm').addEventListener", 'reset submit handler')
INDEX.write_text(idx)

print('Owner password reset hotfix applied')
