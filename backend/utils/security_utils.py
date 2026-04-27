# -*- coding: utf-8 -*-
"""
Security Utility Functions
"""
import pandas as pd

def sanitize_for_csv(value):
    """
    Sanitize a value to prevent CSV Injection (Excel Formula Injection).
    Prepends a single quote (') if the value starts with =, +, -, or @.
    """
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value

def sanitize_dataframe_for_csv(df):
    """
    Sanitize all string columns in a DataFrame to prevent CSV Injection.
    Returns a new DataFrame with sanitized values.
    """
    if df is None:
        return None

    # Create a copy to avoid modifying the original dataframe
    df_sanitized = df.copy()

    # Apply sanitization to object (string) columns
    for col in df_sanitized.select_dtypes(include=['object']).columns:
        df_sanitized[col] = df_sanitized[col].apply(sanitize_for_csv)

    return df_sanitized
