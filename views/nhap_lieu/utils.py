# -*- coding: utf-8 -*-
from services import check_cccd_exists
from constants import Messages


def validate_cccd_for_action(cccd: str, *required_fields) -> tuple[bool, str | None]:
    if not cccd:
        return False, Messages.MISSING_REQUIRED
    if not cccd.strip():
        return False, Messages.MISSING_REQUIRED
    for field in required_fields:
        if not field:
            return False, Messages.MISSING_REQUIRED
    if not check_cccd_exists(cccd):
        return False, Messages.CCCD_NOT_FOUND
    return True, None
