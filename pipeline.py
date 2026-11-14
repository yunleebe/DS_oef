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


TOTAALRIJEN = {
    "België",
    "Vlaams Gewest",
    "Waals Gewest",
    "Brussels Hoofdstedelijk Gewest",
}

# Fusies en arrondissementswissels op 1 januari 2019: oude NIS-code -> nieuwe NIS-code.
# De bevolkingsbladen van 2017 en 2018 gebruiken nog de oude codes, de ongevallendata
# gebruikt overal de nieuwe.
OUDE_NAAR_NIEUWE_NIS = {
    # Vlaanderen: fusies (15 -> 7)
    "44001": "44084", "44029": "44084",  # Aalter
    "44011": "44083", "44049": "44083",  # Deinze
    "44036": "44085", "44072": "44085", "44080": "44085",  # Lievegem
    "45017": "45068", "45057": "45068",  # Kruisem
    "12030": "12041", "12034": "12041",  # Puurs-Sint-Amands
    "72040": "72042", "71047": "72042",  # Oudsbergen
    "72025": "72043", "72029": "72043",  # Pelt
    # Wallonië (Henegouwen): enkel een nieuwe code, geen fusie
    "55022": "58001",  # La Louvière
    "56011": "58002",  # Binche
    "56085": "58003",  # Estinnes
    "56087": "58004",  # Morlanwelz
    "52063": "55085",  # Seneffe
    "52043": "55086",  # Manage
    "55010": "51067",  # Edingen
    "55039": "51068",  # Opzullik
    "55023": "51069",  # Lessen
    "54007": "57096",  # Moeskroen
    "54010": "57097",  # Komen-Waasten
}
EERSTE_JAAR_NIEUWE_CODES = 2019


def laad_bevolking() -> pd.DataFrame:
    """Lees alle bladen van het bevolkingsbestand in en zet ze onder elkaar.

    Kolommen: NIS (tekst), Municipality, Total (geheel getal), Year (uit de bladnaam).
    Titelrij, kopregel, lege rijen en bronvermeldingen vallen weg: enkel rijen met een
    getal in 'Totaal' blijven over. Alle niveaus (België, gewesten, provincies,
    arrondissementen, gemeenten) zitten nog in het resultaat.
    """
    bladen = pd.read_excel(BEVOLKING_BESTAND, sheet_name=None, header=None, dtype=str)
    delen = []
    for bladnaam, blad in bladen.items():
        blad = blad.iloc[:, [0, 1, 4]]
        blad.columns = ["NIS", "Municipality", "Total"]
        blad = blad.assign(Total=pd.to_numeric(blad["Total"], errors="coerce"))
        blad = blad.dropna(subset=["Total"]).astype({"Total": "int64"})
        delen.append(blad.assign(Year=int(bladnaam.split()[-1])))
    return pd.concat(delen, ignore_index=True)


def verwijder_totaalrijen(bevolking: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Verwijder België, gewesten, provincies en arrondissementen.

    Controleert per jaar dat de som van de overblijvende rijen gelijk is aan de rij
    'België'. Geeft (gemeenten, controletabel) terug en gooit een ValueError als de
    controle voor één jaar mislukt.
    """
    is_totaal = bevolking["Municipality"].isin(TOTAALRIJEN) | bevolking[
        "Municipality"
    ].str.contains("Provincie|Arrondissement")
    gemeenten = bevolking[~is_totaal]

    belgie = bevolking[bevolking["Municipality"] == "België"].set_index("Year")["Total"]
    controle = pd.DataFrame(
        {
            "Aantal gemeenten": gemeenten.groupby("Year").size(),
            "Som gemeenten": gemeenten.groupby("Year")["Total"].sum(),
            "Rij België": belgie,
        }
    )
    controle["Verschil"] = controle["Som gemeenten"] - controle["Rij België"]
    controle["OK"] = controle["Verschil"] == 0
    if not controle["OK"].all():
        raise ValueError(f"Controle bevolking mislukt:\n{controle}")
    return gemeenten.reset_index(drop=True), controle


def koppel_oude_nis_codes(bevolking: pd.DataFrame) -> pd.DataFrame:
    """Zet de oude NIS-codes van 2017 en 2018 om naar de nieuwe codes (sinds 2019).

    Bij een fusie worden de aantallen opgeteld. De gemeentenaam komt dan uit 2019.
    """
    namen_2019 = bevolking.loc[bevolking["Year"] == EERSTE_JAAR_NIEUWE_CODES].set_index(
        "NIS"
    )["Municipality"]
    oud = bevolking["Year"] < EERSTE_JAAR_NIEUWE_CODES
    nieuwe_nis = bevolking["NIS"].map(OUDE_NAAR_NIEUWE_NIS).where(oud)
    omgezet = nieuwe_nis.notna()

    resultaat = bevolking.copy()
    resultaat.loc[omgezet, "NIS"] = nieuwe_nis[omgezet]
    resultaat.loc[omgezet, "Municipality"] = resultaat.loc[omgezet, "NIS"].map(namen_2019)
    return (
        resultaat.groupby(["NIS", "Year"], as_index=False)
        .agg(Municipality=("Municipality", "first"), Total=("Total", "sum"))
        .loc[:, ["NIS", "Municipality", "Total", "Year"]]
    )


def maak_fact_population() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Alle bevolkingsstappen na elkaar. Geeft (Fact_Population, controletabel) terug."""
    gemeenten, controle = verwijder_totaalrijen(laad_bevolking())
    return koppel_oude_nis_codes(gemeenten), controle


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
