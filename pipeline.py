"""Datavoorbereiding voor de analyse van fietsongevallen in België (2017-2024).

Elke stap is een aparte functie. Dit bestand importeert geen Streamlit:
app.py roept deze functies aan.
"""

from pathlib import Path

import pandas as pd
from pyproj import Transformer

DATA_DIR = Path(__file__).parent / "data"
ONGEVALLEN_BESTAND = DATA_DIR / "OPENDATA_MAP_2017-2024.xlsx"
BEVOLKING_BESTAND = DATA_DIR / "Bevolking_per_gemeente_2017-2024.xlsx"

BRUSSEL = "Brussels Hoofdstedelijk Gewest"
AUTOSNELWEG_ID = "1"
AUTOSNELWEG_LABEL = "Autosnelweg"
FIETS_LABEL = "Fiets"
ERNSTIGE_KLASSEN = {"met doden", "dodelijk gewonden", "met zwaargewonden"}

# De coördinaten in de ongevallendata zijn Belgisch Lambert 72; de kaart heeft WGS84 nodig.
COORDINATEN_VAN = "EPSG:31370"
COORDINATEN_NAAR = "EPSG:4326"
# Omhullende rechthoek van België (lat, lon). Punten daarbuiten tellen als "geen coördinaten".
BELGIE_LAT = (49.49, 51.51)
BELGIE_LON = (2.54, 6.41)

# Dimensie -> {bronkolom: nieuwe kolomnaam}. De eerste kolom is telkens de ID.
DIMENSIES = {
    "Dim_NIS": {
        "CD_NIS": "NIS",
        "TX_RGN_COLLISION_NL": "Region",
        "TX_PROV_COLLISION_NL": "Province",
        "TX_MUNTY_COLLISION_NL": "Municipality",
    },
    "Dim_Crossway": {"CD_CROSSWAY": "Crossway ID", "TX_CROSSWAY_NL": "Crossway"},
    "Dim_Weather": {"CD_WEATHER": "Weather ID", "TX_WEATHER_NL": "Weather"},
    "Dim_Road_Condition": {
        "CD_ROAD_CONDITION": "Road Condition ID",
        "TX_ROAD_CONDITION_NL": "Road Condition",
    },
    "Dim_Light_Condition": {
        "CD_LIGHT_CONDITION": "Light Condition ID",
        "TX_LIGHT_CONDITION_NL": "Light Condition",
    },
    "Dim_Road_Type": {"CD_ROAD_TYPE": "Road Type ID", "CD_ROAD_TYPE_NL": "Road Type"},
    "Dim_Class_Accidents": {
        "CD_CLASS_ACCIDENTS": "Class Accidents ID",
        "TX_CLASS_ACCIDENTS_NL": "Class Accidents",
    },
    "Dim_Obstacles": {"CD_OBSTACLES": "Obstacle ID", "TX_OBSTACLES_NL": "Obstacle"},
}
# Dim_Road_User wordt uit twee kolomparen samengesteld (weggebruiker 1 en 2).
ROAD_USER_BRONNEN = [
    {"CD_ROAD_USR_TYPE1": "Road User Type ID", "TX_ROAD_USR_TYPE1_NL": "Road User Type"},
    {"CD_ROAD_USR_TYPE2": "Road User Type ID", "TX_ROAD_USR_TYPE2_NL": "Road User Type"},
]

# Fact_Accidents: bronkolom -> nieuwe naam, in de volgorde van de tabel.
# Latitude en Longitude ontstaan in zet_coordinaten_om.
FACT_ACCIDENTS_KOLOMMEN = {
    "DT_YEAR_COLLISION": "Year",
    "DT_MONTH_COLLISION": "Month",
    "DT_TIME": "Hour",
    "CD_NIS": "NIS",
    "Latitude": "Latitude",
    "Longitude": "Longitude",
    "CD_WEATHER": "Weather ID",
    "CD_ROAD_CONDITION": "Road Condition ID",
    "CD_LIGHT_CONDITION": "Light Condition ID",
    "CD_CROSSWAY": "Crossway ID",
    "CD_ROAD_TYPE": "Road Type ID",
    "CD_CLASS_ACCIDENTS": "Class Accidents ID",
    "CD_OBSTACLES": "Obstacle ID",
    "CD_ROAD_USR_TYPE1": "Road User Type1 ID",
    "CD_ROAD_USR_TYPE2": "Road User Type2 ID",
}


def laad_ongevallen() -> pd.DataFrame:
    """Lees de ruwe ongevallendata in.

    Alles wordt eerst als tekst ingelezen, zodat codes zoals '01' hun voorloopnul houden.
    Daarna worden jaar, maand en uur gehele getallen en de coördinaten kommagetallen.
    Alle `CD_`-kolommen (en dus ook `CD_NIS`) blijven tekst.
    """
    ongevallen = pd.read_excel(ONGEVALLEN_BESTAND, dtype=str)
    for kolom in ["DT_YEAR_COLLISION", "DT_MONTH_COLLISION", "DT_TIME"]:
        ongevallen[kolom] = pd.to_numeric(ongevallen[kolom]).astype("int64")
    for kolom in ["MS_X_COORD", "MS_Y_COORD"]:
        ongevallen[kolom] = pd.to_numeric(ongevallen[kolom], errors="coerce")
    return ongevallen


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
    """Verwijder de `_FR`-kolommen en vul de provincie van Brussel in.

    Brussel heeft in de bron geen provincie; het krijgt 'Brussels Hoofdstedelijk Gewest'.
    Er worden geen rijen verwijderd.
    """
    schoon = ongevallen.drop(columns=[k for k in ongevallen.columns if k.endswith("_FR")])
    brussel_zonder_provincie = schoon["TX_PROV_COLLISION_NL"].isna() & (
        schoon["TX_RGN_COLLISION_NL"] == BRUSSEL
    )
    schoon.loc[brussel_zonder_provincie, "TX_PROV_COLLISION_NL"] = BRUSSEL
    return schoon


def zet_coordinaten_om(ongevallen: pd.DataFrame) -> pd.DataFrame:
    """Zet MS_X_COORD / MS_Y_COORD (Lambert 72) om naar Latitude en Longitude (WGS84).

    Lege waarden en punten buiten België krijgen NaN in beide kolommen ("geen coördinaten").
    """
    x, y = ongevallen["MS_X_COORD"], ongevallen["MS_Y_COORD"]
    aanwezig = x.notna() & y.notna()
    transformer = Transformer.from_crs(COORDINATEN_VAN, COORDINATEN_NAAR, always_xy=True)
    lon, lat = transformer.transform(x[aanwezig].to_numpy(), y[aanwezig].to_numpy())

    resultaat = ongevallen.copy()
    resultaat["Latitude"] = pd.Series(lat, index=x[aanwezig].index, dtype="float64")
    resultaat["Longitude"] = pd.Series(lon, index=x[aanwezig].index, dtype="float64")
    in_belgie = resultaat["Latitude"].between(*BELGIE_LAT) & resultaat["Longitude"].between(
        *BELGIE_LON
    )
    resultaat.loc[~in_belgie, ["Latitude", "Longitude"]] = float("nan")
    return resultaat


def maak_dimensie(ongevallen: pd.DataFrame, kolommen: dict[str, str]) -> pd.DataFrame:
    """Unieke rijen van de bronkolommen, hernoemd en gesorteerd op de ID (eerste kolom)."""
    dimensie = ongevallen[list(kolommen)].rename(columns=kolommen).drop_duplicates()
    return dimensie.sort_values(dimensie.columns[0]).reset_index(drop=True)


def maak_dim_road_user(ongevallen: pd.DataFrame) -> pd.DataFrame:
    """Eén gedeelde dimensie voor weggebruiker 1 en 2: unieke (code, label)-combinaties.

    Gooit een ValueError als dezelfde code in TYPE1 en TYPE2 een ander label heeft.
    """
    delen = [
        ongevallen[list(bron)].rename(columns=bron).drop_duplicates()
        for bron in ROAD_USER_BRONNEN
    ]
    dimensie = pd.concat(delen).drop_duplicates()
    conflicten = dimensie[dimensie.duplicated("Road User Type ID", keep=False)]
    if not conflicten.empty:
        raise ValueError(f"Eén code met meerdere labels in Dim_Road_User:\n{conflicten}")
    return dimensie.sort_values("Road User Type ID").reset_index(drop=True)


def maak_dimensies(ongevallen: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Maak alle dimensietabellen (Dim_NIS, Dim_Weather, ..., Dim_Road_User)."""
    dimensies = {naam: maak_dimensie(ongevallen, kol) for naam, kol in DIMENSIES.items()}
    dimensies["Dim_Road_User"] = maak_dim_road_user(ongevallen)
    return dimensies


def sluit_autosnelweg_uit(ongevallen: pd.DataFrame) -> pd.DataFrame:
    """Verwijder de ongevallen op de autosnelweg (de enige rijen die we weglaten)."""
    labels = ongevallen.loc[ongevallen["CD_ROAD_TYPE"] == AUTOSNELWEG_ID, "CD_ROAD_TYPE_NL"]
    if not (labels == AUTOSNELWEG_LABEL).all():
        raise ValueError(f"Road type {AUTOSNELWEG_ID} is niet overal '{AUTOSNELWEG_LABEL}'")
    return ongevallen[ongevallen["CD_ROAD_TYPE"] != AUTOSNELWEG_ID].reset_index(drop=True)


def maak_fact_accidents(ongevallen: pd.DataFrame) -> pd.DataFrame:
    """Fact_Accidents: één rij per ongeval, met ID's die verwijzen naar de dimensies."""
    return ongevallen[list(FACT_ACCIDENTS_KOLOMMEN)].rename(columns=FACT_ACCIDENTS_KOLOMMEN)


def _is_fietsongeval(fact_accidents: pd.DataFrame, dim_road_user: pd.DataFrame) -> pd.Series:
    """True als weggebruiker 1 of 2 'Fiets' is (een ongeval telt één keer)."""
    fiets_ids = dim_road_user.loc[dim_road_user["Road User Type"] == FIETS_LABEL, "Road User Type ID"]
    return fact_accidents["Road User Type1 ID"].isin(fiets_ids) | fact_accidents[
        "Road User Type2 ID"
    ].isin(fiets_ids)


def filter_fietsongevallen(
    fact_accidents: pd.DataFrame, dim_road_user: pd.DataFrame
) -> pd.DataFrame:
    """Hou enkel de ongevallen met minstens één fiets over."""
    return fact_accidents[_is_fietsongeval(fact_accidents, dim_road_user)]


def tel_ongevallen_per_gemeente_jaar(
    fact_accidents: pd.DataFrame,
    dim_road_user: pd.DataFrame,
    dim_class_accidents: pd.DataFrame,
) -> pd.DataFrame:
    """Tel per NIS en jaar: alle ongevallen, fietsongevallen en ernstige fietsongevallen.

    Gemeenten zonder ongeval in een jaar staan hier niet in; koppel_bevolking maakt er 0 van.
    """
    ernstige_ids = dim_class_accidents.loc[
        dim_class_accidents["Class Accidents"].str.lower().isin(ERNSTIGE_KLASSEN),
        "Class Accidents ID",
    ]
    fiets = _is_fietsongeval(fact_accidents, dim_road_user)
    ernstig = fact_accidents["Class Accidents ID"].isin(ernstige_ids)
    return (
        fact_accidents.assign(Bike_Accidents=fiets, Serious_Bike_Accidents=fiets & ernstig)
        .groupby(["NIS", "Year"], as_index=False)
        .agg(
            Accidents=("NIS", "size"),
            Bike_Accidents=("Bike_Accidents", "sum"),
            Serious_Bike_Accidents=("Serious_Bike_Accidents", "sum"),
        )
    )


def koppel_bevolking(
    fact_population: pd.DataFrame, tellingen: pd.DataFrame, dim_nis: pd.DataFrame
) -> pd.DataFrame:
    """Koppel de tellingen aan de bevolking op NIS + Year.

    Een gemeente zonder ongevallen in een jaar krijgt 0 (niet 'ontbrekend'). Een NIS + Year
    die enkel in de ongevallen voorkomt blijft staan, met lege `Total`: die wordt gemeld in
    datakwaliteit_nis. De gemeentenaam, provincie en gewest komen uit Dim_NIS.
    """
    tel_kolommen = ["Accidents", "Bike_Accidents", "Serious_Bike_Accidents"]
    gekoppeld = fact_population.drop(columns="Municipality").merge(
        tellingen, on=["NIS", "Year"], how="outer"
    )
    gekoppeld[tel_kolommen] = gekoppeld[tel_kolommen].fillna(0).astype("int64")
    gekoppeld = gekoppeld.merge(dim_nis[["NIS", "Municipality", "Province", "Region"]], on="NIS", how="left")
    kolommen = ["NIS", "Year", "Municipality", "Province", "Region", "Total", *tel_kolommen]
    return gekoppeld[kolommen].sort_values(["NIS", "Year"]).reset_index(drop=True)


def datakwaliteit_nis(
    fact_accidents: pd.DataFrame, fact_population: pd.DataFrame, dim_nis: pd.DataFrame
) -> pd.DataFrame:
    """NIS-codes (per jaar) die in het ene bestand voorkomen maar niet in het andere.

    'Alleen in ongevallen': geen bevolking voor die code in dat jaar (een echt probleem).
    'Alleen in bevolking': geen enkel ongeval in dat jaar; die gemeente krijgt 0 ongevallen.
    """
    in_ongevallen = fact_accidents[["NIS", "Year"]].drop_duplicates()
    in_bevolking = fact_population[["NIS", "Year"]]
    vergelijking = in_ongevallen.merge(in_bevolking, on=["NIS", "Year"], how="outer", indicator=True)
    verschillen = vergelijking[vergelijking["_merge"] != "both"].copy()
    verschillen["Alleen in"] = verschillen["_merge"].map(
        {"left_only": "ongevallen", "right_only": "bevolking"}
    )
    verschillen = verschillen.merge(dim_nis[["NIS", "Municipality"]], on="NIS", how="left")
    return (
        verschillen[["Year", "NIS", "Municipality", "Alleen in"]]
        .sort_values(["Year", "Alleen in", "NIS"])
        .reset_index(drop=True)
    )


def maak_datamodel() -> tuple[dict[str, pd.DataFrame], dict]:
    """Alle stappen na elkaar. Geeft (tabellen, controles) terug.

    De dimensies worden gemaakt vóór de autosnelweg wegvalt, zodat ze volledig zijn
    (alle 581 gemeenten). Fact_Accidents bevat geen autosnelwegongevallen.
    """
    ongevallen = zet_coordinaten_om(maak_schoon(laad_ongevallen()))
    dimensies = maak_dimensies(ongevallen)
    fact_accidents = maak_fact_accidents(sluit_autosnelweg_uit(ongevallen))
    fact_population, controle_bevolking = maak_fact_population()

    tellingen = tel_ongevallen_per_gemeente_jaar(
        fact_accidents, dimensies["Dim_Road_User"], dimensies["Dim_Class_Accidents"]
    )
    tabellen = {
        **dimensies,
        "Fact_Accidents": fact_accidents,
        "Fact_Population": fact_population,
        "Gemeente_Jaar": koppel_bevolking(fact_population, tellingen, dimensies["Dim_NIS"]),
    }
    controles = {
        "Ongevallen ingelezen": len(ongevallen),
        "Autosnelweg uitgesloten": len(ongevallen) - len(fact_accidents),
        "Controle bevolking": controle_bevolking,
        "Datakwaliteit NIS": datakwaliteit_nis(fact_accidents, fact_population, dimensies["Dim_NIS"]),
    }
    return tabellen, controles
