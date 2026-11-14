"""Datavoorbereiding voor de analyse van fietsongevallen in België (2017-2024).

Elke stap is een aparte functie. Dit bestand importeert geen Streamlit:
app.py roept deze functies aan.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
ONGEVALLEN_BESTAND = DATA_DIR / "OPENDATA_MAP_2017-2024.xlsx"
BEVOLKING_BESTAND = DATA_DIR / "Bevolking_per_gemeente_2017-2024.xlsx"


def laad_ongevallen() -> pd.DataFrame:
    """Lees de ruwe ongevallendata in."""
    raise NotImplementedError


def laad_bevolking() -> pd.DataFrame:
    """Lees de ruwe bevolkingsdata per gemeente in."""
    raise NotImplementedError


def maak_schoon(ongevallen: pd.DataFrame) -> pd.DataFrame:
    """Kuis de ongevallendata op (types, ontbrekende waarden, kolomnamen)."""
    raise NotImplementedError


def filter_fietsongevallen(ongevallen: pd.DataFrame) -> pd.DataFrame:
    """Hou enkel de ongevallen met minstens één fietser over."""
    raise NotImplementedError


def voeg_regio_toe(ongevallen: pd.DataFrame) -> pd.DataFrame:
    """Voeg gemeente, provincie en gewest toe als kolommen."""
    raise NotImplementedError


def tel_per_regio(ongevallen: pd.DataFrame, niveau: str) -> pd.DataFrame:
    """Tel ongevallen en ernst per jaar op het gekozen niveau (gemeente/provincie/gewest)."""
    raise NotImplementedError


def koppel_bevolking(tellingen: pd.DataFrame, bevolking: pd.DataFrame) -> pd.DataFrame:
    """Voeg bevolking toe zodat je ongevallen per 100.000 inwoners kan berekenen."""
    raise NotImplementedError
