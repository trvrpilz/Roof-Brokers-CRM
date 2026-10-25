from pathlib import Path

ROOT = Path('/runtime')
CONFIG = ROOT / 'backend/app/config.py'
MAIN = ROOT / 'backend/app/main.py'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'Owner reset hash patch mismatch for {label}: expected 1 match, found {count}')
    return text.replace(old, new, 1)


cfg = CONFIG.read_text()
cfg = replace_once(
    cfg,
    "    owner_reset_token: str = os.getenv('RB_OWNER_RESET_TOKEN', '')\n",
    "    owner_reset_token_sha256: str = os.getenv('RB_OWNER_RESET_TOKEN_SHA256', '')\n",
    'reset token config',
)
CONFIG.write_text(cfg)

main = MAIN.read_text()
main = replace_once(
    main,
    "    configured=settings.owner_reset_token\n    target_email=settings.owner_reset_email.strip().lower()\n    if not configured or not target_email:\n        raise HTTPException(404,'Owner password reset is not available')\n    if not secrets.compare_digest(data.reset_code,configured):\n        raise HTTPException(401,'Invalid reset code')\n    token_fingerprint=hashlib.sha256(configured.encode()).hexdigest()\n",
    "    configured_hash=settings.owner_reset_token_sha256.strip().lower()\n    target_email=settings.owner_reset_email.strip().lower()\n    if not configured_hash or not target_email:\n        raise HTTPException(404,'Owner password reset is not available')\n    submitted_hash=hashlib.sha256(data.reset_code.encode()).hexdigest()\n    if not secrets.compare_digest(submitted_hash,configured_hash):\n        raise HTTPException(401,'Invalid reset code')\n    token_fingerprint=configured_hash\n",
    'hashed reset token verification',
)
MAIN.write_text(main)

print('Owner password reset hash patch applied')
