from .ui import page_profile_view
from .getters import (
    get_doi_tuong_detail,
    get_nhan_than_by_cccd,
    get_lien_he_by_cccd,
    get_tai_chinh_by_cccd,
    get_phuong_tien_by_cccd,
    get_ho_so_dac_thu_by_cccd,
    get_tai_lieu_by_cccd,
    get_file_path
)
from .actions import (
    delete_nhan_than,
    delete_lien_he,
    delete_tai_chinh,
    delete_phuong_tien,
    delete_ho_so_dac_thu,
    delete_tai_lieu,
    delete_doi_tuong
)

__all__ = [
    'page_profile_view',
    'get_doi_tuong_detail',
    'get_nhan_than_by_cccd',
    'get_lien_he_by_cccd',
    'get_tai_chinh_by_cccd',
    'get_phuong_tien_by_cccd',
    'get_ho_so_dac_thu_by_cccd',
    'get_tai_lieu_by_cccd',
    'get_file_path',
    'delete_nhan_than',
    'delete_lien_he',
    'delete_tai_chinh',
    'delete_phuong_tien',
    'delete_ho_so_dac_thu',
    'delete_tai_lieu',
    'delete_doi_tuong'
]
