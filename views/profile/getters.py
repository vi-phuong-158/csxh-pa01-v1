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
    df = pd.read_sql_query(
        "SELECT * FROM nhan_than WHERE cccd = ?", conn, params=(cccd,))
    conn.close()
    return df


def get_lien_he_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM lien_he WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_tai_chinh_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM tai_chinh WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_phuong_tien_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM phuong_tien WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_ho_so_dac_thu_by_cccd(cccd):
    conn = get_connection()
    query = "SELECT * FROM ho_so_dac_thu WHERE cccd = ? ORDER BY created_at DESC"
    df = pd.read_sql_query(query, conn, params=(cccd,))
    conn.close()
    return df


def get_tai_lieu_by_cccd(cccd):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM tai_lieu WHERE cccd = ? ORDER BY created_at DESC", conn, params=(cccd,))
    conn.close()
    return df


def get_file_path(tai_lieu_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT duong_dan, ten_file_goc FROM tai_lieu WHERE id = ?", (tai_lieu_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        # Resolve path relative to project root assuming app runs from root
        file_path = Path.cwd() / result[0]
        return file_path, result[1]
    return None, None
