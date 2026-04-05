from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import AdminUserDep, CurrentUserDep, ServiceProviderDep
from app.models.loco import IndexSettings
from app.schemas.index_settings import IndexSettingOut, IndexSettingPatch

router = APIRouter(prefix="/index-settings", tags=["index-settings"])


@router.get("", response_model=list[IndexSettingOut])
async def list_index_settings(
    _user: CurrentUserDep,
    provider: ServiceProviderDep,
) -> list[IndexSettings]:
    """Список порогов индекса (любой аутентифицированный пользователь)."""
    return await provider.index_settings_service().list_all()


@router.get("/{metric_name}", response_model=IndexSettingOut)
async def get_index_setting(
    metric_name: str,
    _user: CurrentUserDep,
    provider: ServiceProviderDep,
) -> IndexSettings:
    return await provider.index_settings_service().require_by_metric_name(metric_name)


@router.patch("/{metric_name}", response_model=IndexSettingOut)
async def patch_index_setting(
    metric_name: str,
    body: IndexSettingPatch,
    admin: AdminUserDep,
    provider: ServiceProviderDep,
) -> IndexSettings:
    """Изменение порогов — только роль ``admin``."""
    return await provider.index_settings_service().patch_by_metric_name(
        metric_name,
        body,
        updated_by=admin.id,
    )
