"""Admin license governance endpoints (spec 6.7, FR-27)."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import models
from app.auth.dependencies import require_role
from app.services.license_service import list_licenses, set_license_status


router = APIRouter(prefix="/admin/license", tags=["admin-license"])


class LicenseUpdate(BaseModel):
    status: str
    next_review_at: Optional[str] = None
    legal_basis: Optional[str] = None


@router.get("/all")
def get_all_licenses(
    user: models.User = Depends(require_role("admin", "reviewer")),
):
    return {"licenses": list_licenses()}


@router.patch("/{source_name}")
def patch_license(
    source_name: str,
    payload: LicenseUpdate,
    user: models.User = Depends(require_role("admin")),
):
    try:
        result = set_license_status(
            source_name=source_name,
            status=payload.status,
            next_review_at=payload.next_review_at,
            legal_basis=payload.legal_basis,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))
    return {"ok": True, **result, "updated_by": user.email}
