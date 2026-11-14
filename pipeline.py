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

# De parquet-bestanden (het verwerkte datamodel) staan wel in git: Streamlit Community Cloud
# heeft de Excel-bestanden niet, en inlezen uit parquet duurt 0,3 s in plaats van ~1,5 minuut.
PARQUET_DIR = DATA_DIR / "parquet"
CONTROLE_BEVOLKING = "Controle_Bevolking"
DATAKWALITEIT_NIS = "Datakwaliteit_NIS"
CONTROLE_ONGEVALLEN = "Controle_Ongevallen"

BRUSSEL = "Brussels Hoofdstedelijk Gewest"
AUTOSNELWEG_LABEL = "Autosnelweg"
# Waarden die in de zijbalk standaard niet geselecteerd zijn (ze blijven wel in de data).
# Fietsers mogen niet op de autosnelweg; ze zouden het aandeel fietsongevallen verlagen.
STANDAARD_UIT = {"Road Type": [AUTOSNELWEG_LABEL]}
# Enkel Road User Type ID 03 telt als fiets. De data maakt geen onderscheid tussen een gewone fiets
# en een e-bike; bromfiets (06) en motorfiets (07) hebben andere snelheden en wegen en tellen niet.
FIETS_ID = "03"
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


# Filters in de zijbalk. De geografische filters beperken elkaar (Region > Province > Municipality).
GEOGRAFIE_FILTERS = ["Region", "Province", "Municipality"]
# Filternaam -> (dimensie, labelkolom, ID-kolom in de dimensie, ID-kolommen in Fact_Accidents).
FILTER_DIMENSIES = {
    "Weather": ("Dim_Weather", "Weather", "Weather ID", ["Weather ID"]),
    "Road Condition": (
        "Dim_Road_Condition", "Road Condition", "Road Condition ID", ["Road Condition ID"]
    ),
    "Light Condition": (
        "Dim_Light_Condition", "Light Condition", "Light Condition ID", ["Light Condition ID"]
    ),
    "Crossway": ("Dim_Crossway", "Crossway", "Crossway ID", ["Crossway ID"]),
    "Road Type": ("Dim_Road_Type", "Road Type", "Road Type ID", ["Road Type ID"]),
    "Class Accidents": (
        "Dim_Class_Accidents", "Class Accidents", "Class Accidents ID", ["Class Accidents ID"]
    ),
    "Obstacle": ("Dim_Obstacles", "Obstacle", "Obstacle ID", ["Obstacle ID"]),
    "Road User Type": (
        "Dim_Road_User",
        "Road User Type",
        "Road User Type ID",
        ["Road User Type1 ID", "Road User Type2 ID"],
    ),
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
    # Eerste letter een hoofdletter ("personenauto" -> "Personenauto"); de rest blijft zoals het is.
    dimensie["Road User Type"] = dimensie["Road User Type"].str[:1].str.upper() + dimensie[
        "Road User Type"
    ].str[1:]
    dimensie = dimensie.drop_duplicates()
    conflicten = dimensie[dimensie.duplicated("Road User Type ID", keep=False)]
    if not conflicten.empty:
        raise ValueError(f"Eén code met meerdere labels in Dim_Road_User:\n{conflicten}")
    return dimensie.sort_values("Road User Type ID").reset_index(drop=True)


def maak_dimensies(ongevallen: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Maak alle dimensietabellen (Dim_NIS, Dim_Weather, ..., Dim_Road_User)."""
    dimensies = {naam: maak_dimensie(ongevallen, kol) for naam, kol in DIMENSIES.items()}
    dimensies["Dim_Road_User"] = maak_dim_road_user(ongevallen)
    return dimensies


def maak_fact_accidents(ongevallen: pd.DataFrame) -> pd.DataFrame:
    """Fact_Accidents: één rij per ongeval, met ID's die verwijzen naar de dimensies.

    Alle ongevallen blijven erin, ook die op de autosnelweg: die worden via het filter
    Road Type standaard uitgezet (zie STANDAARD_UIT).
    """
    return ongevallen[list(FACT_ACCIDENTS_KOLOMMEN)].rename(columns=FACT_ACCIDENTS_KOLOMMEN)


def _is_fietsongeval(fact_accidents: pd.DataFrame, dim_road_user: pd.DataFrame) -> pd.Series:
    """True als weggebruiker 1 of 2 Road User Type ID 03 ('Fiets') is (een ongeval telt één keer).

    Gooit een ValueError als ID 03 in Dim_Road_User niet het label 'Fiets' heeft.
    """
    label = dim_road_user.loc[dim_road_user["Road User Type ID"] == FIETS_ID, "Road User Type"]
    if list(label) != [FIETS_LABEL]:
        raise ValueError(f"Road User Type ID {FIETS_ID} is niet '{FIETS_LABEL}': {list(label)}")
    return (fact_accidents["Road User Type1 ID"] == FIETS_ID) | (
        fact_accidents["Road User Type2 ID"] == FIETS_ID
    )


def _is_ernstig(fact_accidents: pd.DataFrame, dim_class_accidents: pd.DataFrame) -> pd.Series:
    """True bij 'Met doden', 'dodelijk gewonden' of 'met zwaargewonden'."""
    ernstige_ids = dim_class_accidents.loc[
        dim_class_accidents["Class Accidents"].str.lower().isin(ERNSTIGE_KLASSEN),
        "Class Accidents ID",
    ]
    return fact_accidents["Class Accidents ID"].isin(ernstige_ids)


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
    fiets = _is_fietsongeval(fact_accidents, dim_road_user)
    ernstig = _is_ernstig(fact_accidents, dim_class_accidents)
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


def selecteer_gemeenten(dim_nis: pd.DataFrame, keuzes: dict[str, list]) -> pd.DataFrame:
    """De gemeenten (rijen van Dim_NIS) die voldoen aan de gekozen Region, Province en Municipality.

    Een lege of ontbrekende keuze betekent "alles". De drie niveaus beperken elkaar.
    """
    gemeenten = dim_nis
    for niveau in GEOGRAFIE_FILTERS:
        if keuzes.get(niveau):
            gemeenten = gemeenten[gemeenten[niveau].isin(keuzes[niveau])]
    return gemeenten


def filter_opties(tabellen: dict[str, pd.DataFrame], keuzes: dict[str, list]) -> dict[str, list]:
    """De keuzes die elk filter aanbiedt, gegeven de al gemaakte keuzes.

    Region beperkt Province, en Region en Province beperken samen Municipality. Bij de andere
    filters staan enkel waarden die in Fact_Accidents voorkomen (bij Road Type dus ook de autosnelweg).
    """
    dim_nis = tabellen["Dim_NIS"]
    in_regio = selecteer_gemeenten(dim_nis, {"Region": keuzes.get("Region")})
    in_provincie = selecteer_gemeenten(in_regio, {"Province": keuzes.get("Province")})
    opties = {
        "Year": sorted(tabellen["Fact_Accidents"]["Year"].unique().tolist()),
        "Region": sorted(dim_nis["Region"].unique()),
        "Province": sorted(in_regio["Province"].unique()),
        "Municipality": sorted(in_provincie["Municipality"].unique()),
    }
    fact = tabellen["Fact_Accidents"]
    for naam, (dimensie, label, id_kolom, fact_kolommen) in FILTER_DIMENSIES.items():
        voorkomend = set().union(*(fact[k].unique() for k in fact_kolommen))
        dim = tabellen[dimensie]
        opties[naam] = dim.loc[dim[id_kolom].isin(voorkomend), label].tolist()
    return opties


def filter_ongevallen(
    tabellen: dict[str, pd.DataFrame], keuzes: dict[str, list]
) -> pd.DataFrame:
    """Fact_Accidents beperkt tot de gekozen waarden. Een lege keuze betekent "alles".

    Alle filters gelden samen (EN). Binnen één filter volstaat één geselecteerde waarde (OF). Bij
    Road User Type telt een ongeval mee als Road User Type1 OF Road User Type2 geselecteerd is.
    """
    fact = tabellen["Fact_Accidents"]
    masker = pd.Series(True, index=fact.index)
    if keuzes.get("Year"):
        masker &= fact["Year"].isin(keuzes["Year"])
    if any(keuzes.get(niveau) for niveau in GEOGRAFIE_FILTERS):
        gemeenten = selecteer_gemeenten(tabellen["Dim_NIS"], keuzes)
        masker &= fact["NIS"].isin(gemeenten["NIS"])
    for naam, (dimensie, label, id_kolom, fact_kolommen) in FILTER_DIMENSIES.items():
        if keuzes.get(naam):
            dim = tabellen[dimensie]
            ids = dim.loc[dim[label].isin(keuzes[naam]), id_kolom]
            masker &= pd.concat([fact[k].isin(ids) for k in fact_kolommen], axis=1).any(axis=1)
    return fact[masker]


def standaard_selectie(naam: str, opties: list) -> list:
    """De waarden die een filter standaard geselecteerd heeft.

    Meestal niets (= alles). Bij een filter in STANDAARD_UIT zijn dat alle opties behalve de
    standaard uitgezette (bij Road Type dus alles behalve de autosnelweg).
    """
    if naam not in STANDAARD_UIT:
        return []
    return [optie for optie in opties if optie not in STANDAARD_UIT[naam]]


def _selecteer_bevolking(tabellen: dict[str, pd.DataFrame], keuzes: dict[str, list]) -> pd.DataFrame:
    """Fact_Population voor de gekozen jaren en gemeenten (Year, Region, Province, Municipality)."""
    bevolking = tabellen["Fact_Population"]
    if keuzes.get("Year"):
        bevolking = bevolking[bevolking["Year"].isin(keuzes["Year"])]
    gemeenten = selecteer_gemeenten(tabellen["Dim_NIS"], keuzes)
    return bevolking[bevolking["NIS"].isin(gemeenten["NIS"])]


def maak_gemeente_jaar(
    gefilterd: pd.DataFrame, tabellen: dict[str, pd.DataFrame], keuzes: dict[str, list]
) -> pd.DataFrame:
    """Eén rij per gemeente en jaar: bevolking en tellingen van de gefilterde ongevallen.

    De tellingen volgen alle filters (dus ook Road Type: zonder autosnelweg zijn het de cijfers
    zonder autosnelweg). De rijen zijn de gemeenten en jaren van de selectie; een gemeente zonder
    ongevallen in een jaar krijgt 0.
    """
    tellingen = tel_ongevallen_per_gemeente_jaar(
        gefilterd, tabellen["Dim_Road_User"], tabellen["Dim_Class_Accidents"]
    )
    return koppel_bevolking(_selecteer_bevolking(tabellen, keuzes), tellingen, tabellen["Dim_NIS"])


def aantal_autosnelweg(tabellen: dict[str, pd.DataFrame]) -> int:
    """Aantal ongevallen op de autosnelweg in Fact_Accidents (alle jaren en gemeenten)."""
    dim = tabellen["Dim_Road_Type"]
    ids = dim.loc[dim["Road Type"] == AUTOSNELWEG_LABEL, "Road Type ID"]
    return int(tabellen["Fact_Accidents"]["Road Type ID"].isin(ids).sum())


def bereken_kerncijfers(
    gefilterd: pd.DataFrame, tabellen: dict[str, pd.DataFrame], keuzes: dict[str, list]
) -> dict:
    """De cijfers voor de kaarten bovenaan, voor de gefilterde ongevallen.

    - Fietsongevallengraad: fietsongevallen per 100.000 inwoners per jaar. De noemer is de
      bevolking (Fact_Population) van de gekozen jaren en gemeenten, opgeteld over alle
      combinaties van gemeente en jaar; zonder keuze telt alles mee. Enkel Year, Region,
      Province en Municipality beïnvloeden de noemer.
    - Een aandeel is None als de noemer 0 is.
    """
    fiets = _is_fietsongeval(gefilterd, tabellen["Dim_Road_User"])
    ernstig = _is_ernstig(gefilterd, tabellen["Dim_Class_Accidents"])
    bevolking = _selecteer_bevolking(tabellen, keuzes)

    ongevallen, fietsongevallen = len(gefilterd), int(fiets.sum())
    ernstige_fietsongevallen = int((fiets & ernstig).sum())
    inwonerjaren = int(bevolking["Total"].sum())
    return {
        "Ongevallen": ongevallen,
        "Fietsongevallen": fietsongevallen,
        "Ernstige fietsongevallen": ernstige_fietsongevallen,
        "Aandeel fietsongevallen": fietsongevallen / ongevallen * 100 if ongevallen else None,
        "Aandeel ernstig (fiets)": (
            ernstige_fietsongevallen / fietsongevallen * 100 if fietsongevallen else None
        ),
        "Fietsongevallengraad": fietsongevallen / inwonerjaren * 100_000 if inwonerjaren else None,
    }


def maak_datamodel() -> tuple[dict[str, pd.DataFrame], dict]:
    """Alle stappen na elkaar. Geeft (tabellen, controles) terug.

    Er gaan geen ongevallen verloren: Fact_Accidents bevat ook de autosnelwegongevallen.
    Gemeente_Jaar zit hier niet in: die tabel volgt de filters en wordt per selectie berekend
    (maak_gemeente_jaar).
    """
    ongevallen = zet_coordinaten_om(maak_schoon(laad_ongevallen()))
    dimensies = maak_dimensies(ongevallen)
    fact_accidents = maak_fact_accidents(ongevallen)
    fact_population, controle_bevolking = maak_fact_population()

    tabellen = {
        **dimensies,
        "Fact_Accidents": fact_accidents,
        "Fact_Population": fact_population,
    }
    controles = {
        "Ongevallen ingelezen": len(ongevallen),
        "Controle bevolking": controle_bevolking,
        "Datakwaliteit NIS": datakwaliteit_nis(fact_accidents, fact_population, dimensies["Dim_NIS"]),
    }
    return tabellen, controles


def schrijf_parquet(
    tabellen: dict[str, pd.DataFrame], controles: dict, map: Path = PARQUET_DIR
) -> None:
    """Schrijf het datamodel en de controles als parquet-bestanden (één per tabel)."""
    map.mkdir(parents=True, exist_ok=True)
    for naam, tabel in tabellen.items():
        tabel.to_parquet(map / f"{naam}.parquet", index=False)
    controles["Controle bevolking"].to_parquet(map / f"{CONTROLE_BEVOLKING}.parquet")
    controles["Datakwaliteit NIS"].to_parquet(map / f"{DATAKWALITEIT_NIS}.parquet", index=False)
    aantallen = pd.DataFrame({"Ongevallen ingelezen": [controles["Ongevallen ingelezen"]]})
    aantallen.to_parquet(map / f"{CONTROLE_ONGEVALLEN}.parquet", index=False)


def lees_parquet(map: Path = PARQUET_DIR) -> tuple[dict[str, pd.DataFrame], dict]:
    """Lees het datamodel en de controles terug uit parquet. Geeft (tabellen, controles) terug."""
    bestanden = {f.stem: pd.read_parquet(f) for f in sorted(map.glob("*.parquet"))}
    aantallen = bestanden.pop(CONTROLE_ONGEVALLEN).iloc[0]
    controles = {
        "Ongevallen ingelezen": int(aantallen["Ongevallen ingelezen"]),
        "Controle bevolking": bestanden.pop(CONTROLE_BEVOLKING),
        "Datakwaliteit NIS": bestanden.pop(DATAKWALITEIT_NIS),
    }
    return bestanden, controles


def parquet_is_actueel(map: Path = PARQUET_DIR) -> bool:
    """Is de parquet bruikbaar? Bestaan de bestanden, en zijn ze nieuwer dan hun bronnen?

    Zijn de Excel-bestanden er niet (bv. op Streamlit Community Cloud), dan wordt de parquet
    gebruikt zoals ze is. Staan ze er wel, dan moet de parquet nieuwer zijn dan de Excel-bestanden
    en dan pipeline.py; anders is ze verouderd.
    """
    bestanden = list(map.glob("*.parquet"))
    if not bestanden:
        return False
    if not (ONGEVALLEN_BESTAND.exists() and BEVOLKING_BESTAND.exists()):
        return True
    nieuwste_bron = max(
        b.stat().st_mtime for b in [ONGEVALLEN_BESTAND, BEVOLKING_BESTAND, Path(__file__)]
    )
    return min(f.stat().st_mtime for f in bestanden) > nieuwste_bron


def laad_of_bouw_datamodel() -> tuple[dict[str, pd.DataFrame], dict]:
    """Lees de parquet als die actueel is; bouw anders het datamodel uit Excel en schrijf parquet."""
    if parquet_is_actueel():
        return lees_parquet()
    tabellen, controles = maak_datamodel()
    schrijf_parquet(tabellen, controles)
    return tabellen, controles


if __name__ == "__main__":
    # `python pipeline.py` herbouwt de parquet uit de Excel-bestanden (ongeveer 1,5 minuut).
    schrijf_parquet(*maak_datamodel())
    print(f"Parquet geschreven naar {PARQUET_DIR}")
