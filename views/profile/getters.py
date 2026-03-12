# -*- coding: utf-8 -*-
import pandas as pd
from pathlib import Path
from database import get_connection

def get_doi_tuong_detail(cccd):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doi_tuong WHERE cccd = ?", (cccd,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def get_nhan_than_by_cccd(cccd):
    conn = get_connection()
    try:
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
    finally:
        conn.close()


def get_lien_he_by_cccd(cccd):
    conn = get_connection()
    try:
        query = "SELECT * FROM lien_he WHERE cccd = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn, params=(cccd,))
        return df
    finally:
        conn.close()


def get_tai_chinh_by_cccd(cccd):
    conn = get_connection()
    try:
        query = "SELECT * FROM tai_chinh WHERE cccd = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn, params=(cccd,))
        return df
    finally:
        conn.close()


def get_phuong_tien_by_cccd(cccd):
    conn = get_connection()
    try:
        query = "SELECT * FROM phuong_tien WHERE cccd = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn, params=(cccd,))
        return df
    finally:
        conn.close()


def get_ho_so_dac_thu_by_cccd(cccd):
    conn = get_connection()
    try:
        query = "SELECT * FROM ho_so_dac_thu WHERE cccd = ? ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn, params=(cccd,))
        return df
    finally:
        conn.close()


def get_tai_lieu_by_cccd(cccd):
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM tai_lieu WHERE cccd = ? ORDER BY created_at DESC", conn, params=(cccd,))
        return df
    finally:
        conn.close()


def get_file_path(tai_lieu_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT duong_dan, ten_file_goc FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
        result = cursor.fetchone()

        if result:
            # Resolve path relative to project root assuming app runs from root
            file_path = Path.cwd() / result[0]
            return file_path, result[1]
        return None, None
    finally:
        conn.close()
