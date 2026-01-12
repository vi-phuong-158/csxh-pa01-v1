# -*- coding: utf-8 -*-
"""
Security Utilities
Common security functions for the application
"""
import pandas as pd


def sanitize_for_excel(value):
    """
    Sanitize value to prevent CSV/Excel Injection (Formula Injection).
    Prepends a single quote if the value starts with dangerous characters.
    """
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def sanitize_dataframe_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply sanitization to all string columns in a DataFrame.
    Returns a new DataFrame.
    """
    df_clean = df.copy()
    # Apply sanitization to object (string) columns
    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].apply(sanitize_for_excel)
    return df_clean
