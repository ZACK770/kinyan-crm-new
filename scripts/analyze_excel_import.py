"""Dry-run simulation of import — test field extraction and phone normalization"""
import openpyxl
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.import_api import normalize_phone, _get_cell, parse_date, SALESPERSON_MAPPING, STATUS_MAPPING, RESPONSE_MAPPING, COURSE_MAPPING
from collections import Counter

path = r"C:\Users\משתמש\Documents\Downloads\_הורדה-לסנכרון-12-2-2026-22.30_02_12_2026.xlsx"
wb = openpyxl.load_workbook(path)
ws = wb.active
headers = [cell.value for cell in ws[1]]
total_rows = ws.max_row - 1

print(f"Total rows: {total_rows}")

# Simulate import
stats = {"ok": 0, "no_phone": 0, "bad_date": 0, "unmapped_status": 0, "unmapped_sp": 0}
unmapped_statuses = Counter()
unmapped_sp = Counter()
phone_samples = []

for row_idx in range(2, ws.max_row + 1):
    row = {}
    for i, h in enumerate(headers):
        if h:
            row[h] = ws.cell(row_idx, i + 1).value

    phone_raw = row.get("טלפון ראשי")
    phone = normalize_phone(phone_raw)
    if not phone:
        stats["no_phone"] += 1
        continue

    if len(phone_samples) < 10:
        phone_samples.append(f"{phone_raw} -> {phone}")

    # Status
    status_raw = _get_cell(row, "סטאטוס ליד") or "ליד חדש"
    status = STATUS_MAPPING.get(str(status_raw).strip())
    if not status:
        unmapped_statuses[str(status_raw).strip()] += 1
        stats["unmapped_status"] += 1

    # Salesperson
    sp_n = _get_cell(row, "איש מכירות", "איש מכירות ")
    if sp_n:
        sp_mapped = SALESPERSON_MAPPING.get(sp_n.strip())
        if sp_mapped is None and sp_n.strip() != "N/A":
            unmapped_sp[sp_n.strip()] += 1
            stats["unmapped_sp"] += 1

    # Date
    created_date = parse_date(_get_cell(row, "תאריך יצירה", "תאריך הגעה"))
    if not created_date:
        stats["bad_date"] += 1

    stats["ok"] += 1

print(f"\nStats: {stats}")
print(f"\nPhone samples: {phone_samples}")
if unmapped_statuses:
    print(f"\nUnmapped statuses: {dict(unmapped_statuses)}")
if unmapped_sp:
    print(f"\nUnmapped salespeople: {dict(unmapped_sp)}")
