# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime
import pandas as pd

EXCEL_FILE = "Clients BL.xlsx"
SHEET_CLIENTS = "Clients"
SHEET_ESCROW = "Escrow"
DEFAULT_SHEETS = [SHEET_CLIENTS, "Visa", "ComptaCli", SHEET_ESCROW]

def ensure_workbook(path: Path = Path(EXCEL_FILE)) -> None:
    if not path.exists():
        dfs = {
            SHEET_CLIENTS: pd.DataFrame(columns=[
                "Dossier N","Nom","Date","Montant total","Acompte 1","Date Acompte 1",
                "Dossier envoyé","Date envoi","Escrow"
            ]),
            "Visa": pd.DataFrame(),
            "ComptaCli": pd.DataFrame(),
            SHEET_ESCROW: pd.DataFrame(columns=[
                "Dossier N","Nom","Montant","Date envoi","État","Date réclamation"
            ]),
        }
        with pd.ExcelWriter(path, engine="openpyxl") as w:
            for sh, df in dfs.items():
                df.to_excel(w, index=False, sheet_name=sh)

def load_all(path: Path = Path(EXCEL_FILE)):
    ensure_workbook(path)
    xls = pd.ExcelFile(path)
    changed = False
    for sh in DEFAULT_SHEETS:
        if sh not in xls.sheet_names:
            with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="overlay") as w:
                pd.DataFrame().to_excel(w, index=False, sheet_name=sh)
            changed = True
    if changed:
        xls = pd.ExcelFile(path)
    clients = pd.read_excel(xls, SHEET_CLIENTS) if SHEET_CLIENTS in xls.sheet_names else pd.DataFrame()
    escrow = pd.read_excel(xls, SHEET_ESCROW) if SHEET_ESCROW in xls.sheet_names else pd.DataFrame(
        columns=["Dossier N","Nom","Montant","Date envoi","État","Date réclamation"])
    return clients, escrow

def save_clients_and_escrow(clients: pd.DataFrame, escrow: pd.DataFrame, path: Path = Path(EXCEL_FILE)) -> None:
    ensure_workbook(path)
    xls = pd.ExcelFile(path)
    with pd.ExcelWriter(path, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        for sh in xls.sheet_names:
            if sh == SHEET_CLIENTS:
                (clients if clients is not None else pd.DataFrame()).to_excel(w, index=False, sheet_name=sh)
            elif sh == SHEET_ESCROW:
                (escrow if escrow is not None else pd.DataFrame()).to_excel(w, index=False, sheet_name=sh)
            else:
                pd.read_excel(xls, sh).to_excel(w, index=False, sheet_name=sh)

def to_float(x):
    try:
        if pd.isna(x): return 0.0
        s = str(x).replace("€","").replace("\u202f","").replace("\xa0","").replace(" ", "").replace(",", ".")
        return float(s)
    except Exception:
        try: return float(x)
        except Exception: return 0.0

def sync_escrow_from_clients(clients: pd.DataFrame, escrow: pd.DataFrame):
    if escrow is None or escrow.empty:
        escrow = pd.DataFrame(columns=["Dossier N","Nom","Montant","Date envoi","État","Date réclamation"])
    for col in ["Dossier N","Nom","Acompte 1","Dossier envoyé","Date envoi","Escrow"]:
        if col not in clients.columns:
            clients[col] = pd.NA
    existing = set(escrow["Dossier N"].astype(str)) if not escrow.empty and "Dossier N" in escrow.columns else set()
    added_rows = []
    for _, r in clients.iterrows():
        try:
            escf = int(r.get("Escrow", 0)) if pd.notna(r.get("Escrow", 0)) else 0
            sent = int(r.get("Dossier envoyé", 0)) if pd.notna(r.get("Dossier envoyé", 0)) else 0
        except Exception:
            escf = 0; sent = 0
        if escf == 1 and sent == 1:
            num = str(r.get("Dossier N","")).strip()
            if num and num not in existing:
                added_rows.append({
                    "Dossier N": num,
                    "Nom": r.get("Nom",""),
                    "Montant": to_float(r.get("Acompte 1",0)),
                    "Date envoi": r.get("Date envoi",""),
                    "État": "À réclamer",
                    "Date réclamation": ""
                })
                existing.add(num)
    if added_rows:
        escrow = pd.concat([escrow, pd.DataFrame(added_rows)], ignore_index=True)
    return escrow, len(added_rows)

def mark_escrow_reclaimed(escrow: pd.DataFrame, dossier_num: str):
    if escrow is None or escrow.empty: return escrow, False
    idx = escrow.index[escrow["Dossier N"].astype(str) == str(dossier_num)]
    if len(idx):
        j = idx[0]
        escrow.at[j, "État"] = "Réclamé"
        escrow.at[j, "Date réclamation"] = datetime.now().strftime("%Y-%m-%d")
        return escrow, True
    return escrow, False

def pending(escrow: pd.DataFrame):
    if escrow is None or escrow.empty: return escrow.iloc[0:0]
    if "État" not in escrow.columns: return escrow.iloc[0:0]
    return escrow[escrow["État"].fillna("") == "À réclamer"]

def claimed(escrow: pd.DataFrame):
    if escrow is None or escrow.empty: return escrow.iloc[0:0]
    if "État" not in escrow.columns: return escrow.iloc[0:0]
    return escrow[escrow["État"].fillna("") == "Réclamé"]
