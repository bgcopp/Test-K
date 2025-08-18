#!/usr/bin/env python3
"""Verificar estructura de tabla operator_call_data"""

import sqlite3

conn = sqlite3.connect('kronos.db')
cursor = conn.cursor()

print("=== ESTRUCTURA DE TABLA operator_call_data ===")
cursor.execute("PRAGMA table_info(operator_call_data)")
columns = cursor.fetchall()

for col in columns:
    print(f"  {col[1]}: {col[2]}")

conn.close()