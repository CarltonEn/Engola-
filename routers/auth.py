"""
Owner authentication router (WebAuthn/passkey).

This is a direct migration of the auth endpoints from the v0.5 canonical
single-file app.py into its own router. The verification logic, error
messages and status codes are unchanged. No biometric template is ever
received or stored by the server -- only the WebAuthn public key credential
(a cryptographic assertion), consistent with OWNER-IDENTITY.md.
"""
import json
import secrets

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core import config
from core.db import db, has_owner
from core.security import (
    create_session,
    hash_token,
    origin,
    rp_id,
    save_challenge,
    take_challenge,
)

try:
    from webauthn import (
        base64url_to_bytes,
        generate_authentication_options,
        generate_registration_options,
        options_to_json,
        verify_authentication_response,
        verify_registration_response,
    )
    from webauthn.helpers.structs import (
        AuthenticatorSelectionCriteria,
        AuthenticatorAttachment,
        PublicKeyCredentialDescriptor,
        ResidentKeyRequirement,
        UserVerificationRequirement,
    )

    WEBAUTHN_OK = True
except Exception:
    WEBAUTHN_OK = False

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/status")
def auth_status(request: Request):
    from core.security import current_owner

    return {
        "authenticated": current_owner(request),
        "owner": config.OWNER_NAME,
        "setup_required": not has_owner(),
        "webauthn_available": WEBAUTHN_OK,
    }


@router.post("/setup/options")
async def setup_options(request: Request):
    if not WEBAUTHN_OK:
        return JSONResponse({"error": "WebAuthn server library is not installed."}, status_code=500)
    if has_owner():
        return JSONResponse({"error": "Owner passkey is already registered."}, status_code=409)
    body = await request.json()
    token = (body.get("setup_token") or "").strip()
    expected = config.ENGOLA_SETUP_TOKEN
    if not expected or not secrets.compare_digest(token, expected):
        return JSONResponse({"error": "Invalid owner setup authorization."}, status_code=403)
    options = generate_registration_options(
        rp_id=rp_id(request),
        rp_name=config.RP_NAME,
        user_id=secrets.token_bytes(32),
        user_name=config.OWNER_NAME,
        user_display_name=config.OWNER_NAME,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )
    save_challenge("registration", options.challenge)
    return json.loads(options_to_json(options))


@router.post("/setup/verify")
async def setup_verify(request: Request):
    if not WEBAUTHN_OK:
        return JSONResponse({"error": "WebAuthn server library is not installed."}, status_code=500)
    if has_owner():
        return JSONResponse({"error": "Owner passkey is already registered."}, status_code=409)
    body = await request.json()
    token = (body.pop("setup_token", "") or "").strip()
    expected = config.ENGOLA_SETUP_TOKEN
    if not expected or not secrets.compare_digest(token, expected):
        return JSONResponse({"error": "Invalid owner setup authorization."}, status_code=403)
    challenge = take_challenge("registration")
    if not challenge:
        return JSONResponse({"error": "Registration challenge expired. Start again."}, status_code=400)
    try:
        verification = verify_registration_response(
            credential=body,
            expected_challenge=challenge,
            expected_rp_id=rp_id(request),
            expected_origin=origin(request),
        )
        c = db()
        c.execute(
            "INSERT INTO owner_credentials(credential_id,public_key,sign_count,created_at) VALUES(?,?,?,?)",
            (
                verification.credential_id.hex(),
                verification.credential_public_key,
                verification.sign_count,
                __import__("time").time(),
            ),
        )
        c.commit()
        c.close()
        response = JSONResponse({"ok": True, "owner": config.OWNER_NAME})
        create_session(response)
        return response
    except Exception as e:
        return JSONResponse({"error": f"Passkey registration failed: {type(e).__name__}"}, status_code=400)


@router.post("/login/options")
def login_options(request: Request):
    if not WEBAUTHN_OK:
        return JSONResponse({"error": "WebAuthn server library is not installed."}, status_code=500)
    if not has_owner():
        return JSONResponse({"error": "Owner setup is required first."}, status_code=409)
    c = db()
    ids = [base64url_to_bytes(r[0]) for r in c.execute("SELECT credential_id FROM owner_credentials").fetchall()]
    c.close()
    options = generate_authentication_options(
        rp_id=rp_id(request),
        allow_credentials=[PublicKeyCredentialDescriptor(id=i) for i in ids],
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    save_challenge("authentication", options.challenge)
    return json.loads(options_to_json(options))


@router.post("/login/verify")
async def login_verify(request: Request):
    if not WEBAUTHN_OK:
        return JSONResponse({"error": "WebAuthn server library is not installed."}, status_code=500)
    body = await request.json()
    challenge = take_challenge("authentication")
    if not challenge:
        return JSONResponse({"error": "Authentication challenge expired. Start again."}, status_code=400)
    try:
        credential_id = (body.get("id") or "").strip()
        c = db()
        row = c.execute(
            "SELECT public_key,sign_count FROM owner_credentials WHERE credential_id=?", (credential_id,)
        ).fetchone()
        c.close()
        if not row:
            return JSONResponse({"error": "Unknown owner credential."}, status_code=403)
        verification = verify_authentication_response(
            credential=body,
            expected_challenge=challenge,
            expected_rp_id=rp_id(request),
            expected_origin=origin(request),
            credential_public_key=row[0],
            credential_current_sign_count=row[1],
        )
        c = db()
        c.execute(
            "UPDATE owner_credentials SET sign_count=? WHERE credential_id=?",
            (verification.new_sign_count, credential_id),
        )
        c.commit()
        c.close()
        response = JSONResponse({"ok": True, "owner": config.OWNER_NAME})
        create_session(response)
        return response
    except Exception as e:
        return JSONResponse({"error": f"Passkey authentication failed: {type(e).__name__}"}, status_code=403)


@router.post("/logout")
def logout(request: Request):
    token = request.cookies.get(config.SESSION_COOKIE)
    if token:
        c = db()
        c.execute("DELETE FROM sessions WHERE token_hash=?", (hash_token(token),))
        c.commit()
        c.close()
    response = JSONResponse({"ok": True})
    response.delete_cookie(config.SESSION_COOKIE, path="/")
    return response
