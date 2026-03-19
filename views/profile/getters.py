# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from pathlib import Path
from contextlib import closing
from database import get_connection


@st.cache_data(ttl=30, show_spinner=False)
def get_doi_tuong_detail(cccd):
    """Lấy chi tiết đối tượng (cached 30s)"""
    if not cccd or not str(cccd).isalnum():
        return None
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doi_tuong WHERE cccd = ?", (cccd,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


@st.cache_data(ttl=30, show_spinner=False)
def get_nhan_than_by_cccd(cccd):
    """Lấy danh sách nhân thân (cached 30s)"""
    if not cccd or not str(cccd).isalnum():
        return pd.DataFrame()
    with closing(get_connection()) as conn:
        query = """
            SELECT 
                nt.id,
                nt.cccd,
                nt.loai_quan_he,
                nt.cccd_nhan_than,
                COALESCE(dt.ho_ten, nt.ho_ten) AS ho_ten,
                COALESCE(dt.ngay_sinh, nt.ngay_sinh) AS ngay_sinh,
                COALESCE(dt.gioi_tinh, nt.gioi_tinh) AS gioi_tinh,
                COALESCE(dt.dia_chi_tinh, nt.dia_chi_tinh) AS dia_chi_tinh,
                COALESCE(dt.dia_chi_xa, nt.dia_chi_xa) AS dia_chi_xa,
                COALESCE(dt.dia_chi_chi_tiet, nt.dia_chi_chi_tiet) AS dia_chi_chi_tiet,
                COALESCE(dt.phan_loai_nghe_nghiep, nt.nghe_nghiep) AS nghe_nghiep,
                COALESCE(dt.dia_chi_xa, nt.noi_o) AS noi_o,
                nt.ghi_chu,
                nt.created_at
            FROM nhan_than nt
            LEFT JOIN doi_tuong dt ON nt.cccd_nhan_than = dt.cccd
            WHERE nt.cccd = ?
        """
        df = pd.read_sql_query(query, conn, params=(cccd,))
        return df


@st.cache_data(ttl=30, show_spinner=False)
def get_lien_he_by_cccd(cccd):
    """Lấy danh sách liên hệ (cached 30s)"""
    if not cccd or not str(cccd).isalnum():
        return pd.DataFrame()
    with closing(get_connection()) as conn:
        query = "SELECT * FROM lien_he WHERE cccd = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn, params=(cccd,))
        return df


@st.cache_data(ttl=30, show_spinner=False)
def get_tai_chinh_by_cccd(cccd):
    """Lấy danh sách tài chính (cached 30s)"""
    if not cccd or not str(cccd).isalnum():
        return pd.DataFrame()
    with closing(get_connection()) as conn:
        query = "SELECT * FROM tai_chinh WHERE cccd = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn, params=(cccd,))
        return df


@st.cache_data(ttl=30, show_spinner=False)
def get_phuong_tien_by_cccd(cccd):
    """Lấy danh sách phương tiện (cached 30s)"""
    if not cccd or not str(cccd).isalnum():
        return pd.DataFrame()
    with closing(get_connection()) as conn:
        query = "SELECT * FROM phuong_tien WHERE cccd = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn, params=(cccd,))
        return df


@st.cache_data(ttl=30, show_spinner=False)
def get_ho_so_dac_thu_by_cccd(cccd):
    """Lấy danh sách hồ sơ đặc thù (cached 30s)"""
    if not cccd or not str(cccd).isalnum():
        return pd.DataFrame()
    with closing(get_connection()) as conn:
        query = "SELECT * FROM ho_so_dac_thu WHERE cccd = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn, params=(cccd,))
        return df


@st.cache_data(ttl=30, show_spinner=False)
def get_tai_lieu_by_cccd(cccd):
    """Lấy danh sách tài liệu (cached 30s)"""
    if not cccd or not str(cccd).isalnum():
        return pd.DataFrame()
    with closing(get_connection()) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM tai_lieu WHERE cccd = ? ORDER BY created_at DESC", conn, params=(cccd,))
        return df


def get_file_path(tai_lieu_id):
    """Lấy đường dẫn file - không cache vì trả về Path object"""
    if not tai_lieu_id or not str(tai_lieu_id).isdigit():
        return None, None
    with closing(get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT duong_dan, ten_file_goc FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
        result = cursor.fetchone()

        if result:
            # Resolve path relative to project root assuming app runs from root
            file_path = Path.cwd() / result[0]
            return file_path, result[1]
        return None, None
