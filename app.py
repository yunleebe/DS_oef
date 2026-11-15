"""Streamlit-interface: fietsongevallen in België, 2017-2024.

Start met: streamlit run app.py
De datavoorbereiding en de filterlogica zitten in pipeline.py.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import pipeline

st.set_page_config(page_title="Fietsongevallen in België", layout="wide")

LIJNKLEUR = "#2a6fdb"  # één serie = één kleur

# Streamlit laat standaard ± 6 rem leeg boven de titel; dat verkleinen we, zodat er meer op het
# scherm past zonder te scrollen. De titel zelf krijgt minder ruimte erboven.
st.markdown(
    """
    <style>
    [data-testid="stMainBlockContainer"] { padding-top: 2.5rem; }
    [data-testid="stMainBlockContainer"] h1 { padding-top: 0; padding-bottom: 0.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Filternaam in de data -> tekst in de zijbalk, in de volgorde van de zijbalk.
FILTER_LABELS = {
    "Year": "Jaar",
    "Region": "Gewest",
    "Province": "Provincie",
    "Municipality": "Gemeente",
    "Weather": "Weer",
    "Road Condition": "Wegdek",
    "Light Condition": "Licht",
    "Crossway": "Kruispunt",
    "Road Type": "Wegtype",
    "Class Accidents": "Ernst van het ongeval",
    "Obstacle": "Hindernis",
    "Road User Type": "Weggebruiker",
}
FILTER_HULP = {
    "Region": "Beperkt de keuze bij Provincie.",
    "Province": "Beperkt de keuze bij Gemeente.",
    "Road Type": (
        "De autosnelweg staat standaard uit. Een lege keuze betekent alle wegtypes, "
        "dus mét autosnelweg."
    ),
    "Road User Type": "Een ongeval telt mee als weggebruiker 1 of weggebruiker 2 geselecteerd is.",
}


@st.cache_data(show_spinner="Data wordt geladen...")
def laad_datamodel():
    return pipeline.laad_of_bouw_datamodel()


def fmt_getal(waarde: float, decimalen: int = 0) -> str:
    """Belgische notatie: punt als duizendtalscheiding, komma als decimaalteken (86.300; 13,0)."""
    tekst = f"{waarde:,.{decimalen}f}"
    return tekst.replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_pct(waarde: float | None) -> str:
    return "–" if waarde is None else f"{fmt_getal(waarde, 1)} %"


def fmt_graad(waarde: float | None) -> str:
    return "–" if waarde is None else fmt_getal(waarde, 1)


def toon_filters(tabellen: dict) -> dict[str, list]:
    """Zet de filters in de zijbalk en geef de keuzes terug. Geen keuze betekent "alles"."""
    st.sidebar.header("Filters")
    st.sidebar.caption(
        "Geen keuze = alles. De filters gelden voor alle cijfers hieronder. "
        "Bij Wegtype staat de autosnelweg standaard uit."
    )
    keuzes: dict[str, list] = {}
    opties = pipeline.filter_opties(tabellen, keuzes)
    for naam, tekst in FILTER_LABELS.items():
        if naam in ("Province", "Municipality"):  # die lijsten hangen af van de keuze hierboven
            opties = pipeline.filter_opties(tabellen, keuzes)
        # Bij een andere keuze hierboven verandert de sleutel, zodat dit filter terug op "alles"
        # staat en geen waarden bewaart die niet meer in de lijst staan.
        sleutel = f"filter_{naam}"
        if naam == "Province":
            sleutel += "|" + "|".join(keuzes["Region"])
        elif naam == "Municipality":
            sleutel += "|" + "|".join(keuzes["Region"]) + "|" + "|".join(keuzes["Province"])
        keuzes[naam] = st.sidebar.multiselect(
            tekst,
            opties[naam],
            default=pipeline.standaard_selectie(naam, opties[naam]),
            key=sleutel,
            placeholder="Alles",
            help=FILTER_HULP.get(naam),
        )
    return keuzes


def toon_kaarten(kern: dict) -> None:
    """De belangrijkste cijfers bovenaan, als kaarten."""
    kaarten = [
        ("Ongevallen", fmt_getal(kern["Ongevallen"]), "Alle ongevallen na de filters."),
        (
            "Fietsongevallen",
            fmt_getal(kern["Fietsongevallen"]),
            "Ongevallen waarbij weggebruiker 1 of 2 een fiets is. Elk ongeval telt één keer.",
        ),
        (
            "Ernstige fietsongevallen",
            fmt_getal(kern["Ernstige fietsongevallen"]),
            "Fietsongevallen met doden, dodelijk gewonden of zwaargewonden.",
        ),
        (
            "Aandeel fietsongevallen",
            fmt_pct(kern["Aandeel fietsongevallen"]),
            "Fietsongevallen als % van alle ongevallen na de filters. Standaard zonder autosnelweg.",
        ),
        (
            "Aandeel ernstig (fiets)",
            fmt_pct(kern["Aandeel ernstig (fiets)"]),
            "Ernstige fietsongevallen als % van alle fietsongevallen.",
        ),
        (
            "Fietsongevallen per 100.000 inwoners",
            fmt_graad(kern["Fietsongevallengraad"]),
            "Gemiddeld per jaar. De bevolking is die van de gekozen jaren en gemeenten; enkel "
            "de filters Jaar, Gewest, Provincie en Gemeente beïnvloeden die.",
        ),
    ]
    for rij in (kaarten[:3], kaarten[3:]):
        for kolom, (titel, waarde, hulp) in zip(st.columns(3), rij):
            kolom.metric(titel, waarde, help=hulp, border=True)


def formatteer_tabel(tabel):
    """Kopie met Belgische getalnotatie; het jaar blijft een jaartal zonder scheidingsteken."""
    tabel = tabel.copy()
    for kolom in tabel.columns:
        if kolom == "Year":
            tabel[kolom] = tabel[kolom].astype(str)
        elif tabel[kolom].dtype.kind in "iuf":
            tabel[kolom] = tabel[kolom].map(fmt_getal)
    return tabel


st.title("Fietsongevallen in België, 2017–2024")
st.write(
    "Waar zijn fietsongevallen het talrijkst en het ernstigst "
    "(gemeente, provincie, gewest), en is dat veranderd sinds 2017?"
)

tabellen, controles = laad_datamodel()
keuzes = toon_filters(tabellen)
gefilterd = pipeline.filter_ongevallen(tabellen, keuzes)
kern = pipeline.bereken_kerncijfers(gefilterd, tabellen, keuzes)

wegtypes = keuzes["Road Type"]
if not wegtypes or pipeline.AUTOSNELWEG_LABEL in wegtypes:
    st.warning(
        "**De autosnelweg is meegerekend.** Fietsers mogen daar niet rijden, dus het aandeel "
        "fietsongevallen is lager dan met de standaardinstelling (autosnelweg uit)."
    )
else:
    st.info(
        "**De autosnelweg staat standaard uit.** Fietsers mogen daar niet rijden en ze zouden "
        "het aandeel fietsongevallen in gemeenten met een autosnelweg verlagen. Selecteer "
        "'Autosnelweg' bij Wegtype in de zijbalk om ze mee te rekenen en het verschil te zien."
    )

toon_kaarten(kern)
if gefilterd.empty:
    st.info("Geen ongevallen voor deze selectie. Pas de filters in de zijbalk aan.")

MAAT_UITLEG = {
    "graad": (
        "**Maat:** fietsongevallen (met doden of gewonden, dus geen aantal slachtoffers) per "
        "100.000 inwoners van dat jaar. Er zijn geen gegevens over hoeveel er gefietst wordt: dit "
        "is niet het risico per gefietste kilometer."
    ),
    "aandeel": (
        "**Maat:** fietsongevallen als % van alle ongevallen met doden of gewonden in dat jaar "
        "(na de filters)."
    ),
    "ernstig": (
        "**Maat:** ernstige fietsongevallen (met doden, dodelijk gewonden of zwaargewonden) als % "
        "van alle fietsongevallen in dat jaar. Zegt of de ongevallen zwaarder werden, los van "
        "hoeveel er zijn."
    ),
}


def lijngrafiek(per_jaar, kolom: str, titel: str, eenheid: str):
    """Eén lijn per grafiek (geen dubbele as); 2020–2021 (corona) is gearceerd."""
    fig = px.line(per_jaar, x="Year", y=kolom, markers=True)
    fig.update_traces(
        line_color=LIJNKLEUR,
        line_width=2,
        marker_size=8,
        hovertemplate="%{x}: %{y:,.1f}" + eenheid + "<extra></extra>",
    )
    if per_jaar["Year"].min() <= 2021 and per_jaar["Year"].max() >= 2020:
        fig.add_vrect(
            x0=2019.5, x1=2021.5, fillcolor="gray", opacity=0.12, line_width=0,
            annotation_text="corona", annotation_position="top left",
        )
    fig.update_layout(
        title=titel,
        xaxis_title=None,
        yaxis_title=None,
        xaxis={"dtick": 1, "tickformat": "d"},
        yaxis={"rangemode": "tozero", "separatethousands": True},
        margin={"t": 50, "b": 20, "l": 10, "r": 10},
        height=340,
        separators=",.",
    )
    return fig


MAANDEN = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]


def toon_maandgrafiek(maandtelling) -> None:
    """Fietsongevallen per maand, één lijn per jaar. Jaren zijn geordend, dus lichter = ouder."""
    jaren = sorted(maandtelling["Year"].unique())
    # oudste jaar = lichtste blauw, recentste = donkerste
    kleuren = px.colors.sample_colorscale(
        "Blues", [0.35 + 0.65 * i / max(len(jaren) - 1, 1) for i in range(len(jaren))]
    )
    kleur_per_jaar = {str(j): k for j, k in zip(jaren, kleuren)}
    fig = px.line(
        maandtelling.assign(Jaar=maandtelling["Year"].astype(str)),
        x="Month", y="Bike_Accidents", color="Jaar", markers=True,
        category_orders={"Jaar": [str(j) for j in jaren]},
        color_discrete_map=kleur_per_jaar,
    )
    fig.update_traces(line_width=2, marker_size=8, hovertemplate="%{y:,.0f} fietsongevallen<extra>%{fullData.name}</extra>")
    fig.update_layout(
        title="Fietsongevallen per maand",
        xaxis={"tickmode": "array", "tickvals": list(range(1, 13)), "ticktext": MAANDEN, "title": None},
        yaxis={"rangemode": "tozero", "title": None, "separatethousands": True},
        legend_title_text=None,
        legend_traceorder="reversed",  # recentste jaar bovenaan, zoals de lijnen bovenaan liggen
        margin={"t": 50, "b": 20, "l": 10, "r": 10},
        height=380,
        separators=",.",
        hovermode="x unified",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "**Maat:** aantal fietsongevallen (met doden of gewonden) per maand, één lijn per gekozen "
        "jaar; hoe donkerder de lijn, hoe recenter het jaar. Dit is een aantal en geen graad: "
        "maanden met meer dagen of meer fietsers tellen meer ongevallen."
    )


def toon_kaart(gefilterd, tabellen) -> None:
    """Kaart van de ongevallen met coördinaten: concentratie (standaard) of afzonderlijke punten."""
    links, rechts = st.columns(2)
    keuze = links.radio("Toon", ["Fietsongevallen", "Alle ongevallen"], horizontal=True, key="kaart_toon")
    weergave = rechts.radio("Weergave", ["Concentratie", "Afzonderlijke punten"], horizontal=True, key="kaart_weergave")
    ongevallen = pipeline.selecteer_kaartongevallen(gefilterd, tabellen, keuze == "Fietsongevallen")
    met = int(ongevallen["Latitude"].notna().sum())
    totaal = len(ongevallen)
    if totaal == 0:
        st.info("Geen ongevallen voor deze selectie.")
        return

    midden = {"lat": 50.65, "lon": 4.45}
    if weergave == "Concentratie":
        data = pipeline.maak_kaartdata(ongevallen)
        fig = px.density_map(
            data, lat="Latitude", lon="Longitude", z="Accidents", radius=9,
            center=midden, zoom=6.6, map_style="carto-positron",
            color_continuous_scale="Blues",
        )
        fig.update_traces(hovertemplate="%{z:,.0f} ongevallen<extra></extra>")
        fig.update_layout(coloraxis_colorbar={"title": "Ongevallen<br>per ± 1 km²"})
    else:
        data = pipeline.maak_kaartpunten(ongevallen)
        fig = px.scatter_map(
            data, lat="Latitude", lon="Longitude", hover_name="Year",
            center=midden, zoom=6.6, map_style="carto-positron",
        )
        fig.update_traces(marker={"size": 5, "opacity": 0.45, "color": LIJNKLEUR},
                          hovertemplate="Jaar %{hovertext}<extra></extra>")
        if len(data) < met:
            st.caption(
                f"Er worden {fmt_getal(len(data))} van {fmt_getal(met)} punten getoond (een vaste "
                "willekeurige steekproef). Filter verder om alle punten te zien."
            )
    fig.update_layout(margin={"t": 10, "b": 0, "l": 0, "r": 0}, height=560, separators=",.")
    st.plotly_chart(fig, width="stretch")

    st.caption(
        f"**Maat:** deze kaart toont {fmt_getal(met)} van {fmt_getal(totaal)} "
        f"{keuze.lower()} ({fmt_pct(met / totaal * 100)}); de rest heeft geen (geldige) coördinaten "
        "en ontbreekt op de kaart, maar telt wel mee in alle andere cijfers. Een donkerder vlak "
        "betekent meer ongevallen, niet meer risico: drukke gebieden hebben meer fietsers."
    )

    jaren = gefilterd["Year"].unique()
    if (jaren < pipeline.JAAR_BETERE_COORDINATEN).any() and (jaren >= pipeline.JAAR_BETERE_COORDINATEN).any():
        st.warning(
            f"De gekozen jaren lopen over {pipeline.JAAR_BETERE_COORDINATEN}. Voor die tijd "
            "ontbreken er veel meer coördinaten (zie de tabel hieronder): de kaart onderschat "
            "dan de oudere jaren. Vergelijk jaren op de kaart dus voorzichtig."
        )

    with st.expander("Ongevallen zonder coördinaten, per provincie en jaar (%)"):
        tabel = pipeline.zonder_coordinaten_per_provincie_jaar(ongevallen, tabellen["Dim_NIS"])
        tabel.columns = [str(k) for k in tabel.columns]
        tabel = tabel.map(lambda x: "–" if x != x else fmt_getal(x, 1)).reset_index(names="Provincie")
        st.dataframe(tabel, hide_index=True)
        st.caption("Aandeel van de ongevallen (na de filters) dat niet op de kaart kan staan.")


KLEUR_BEVOLKING = "#195C8F"
KLEUR_GRAAD = "#FF8F1C"


# Per niveau: kolom in de data, en de woorden voor titels en zinnen.
NIVEAUS = {
    "Gewest": {"kolom": "Region", "meervoud": "gewesten", "elk": "Elk gewest", "dit": "het gewest", "dat": "dit gewest", "top": None},
    "Provincie": {"kolom": "Province", "meervoud": "provincies", "elk": "Elke provincie", "dit": "de provincie", "dat": "deze provincie", "top": None},
    "Gemeente": {"kolom": "Municipality", "meervoud": "gemeenten", "elk": "Elke gemeente", "dit": "de gemeente", "dat": "deze gemeente", "top": pipeline.TOP_GEMEENTEN},
}


MAAT_SORTEER = {
    "Bike_Accidents": "het aantal fietsongevallen in de gekozen jaren.",
    "Serious_Bike_Accidents": "het aantal ernstige fietsongevallen (met doden, dodelijk gewonden of zwaargewonden).",
    "Bike_Rate": (
        "fietsongevallen per 100.000 inwoners per jaar, met een 95 %-marge: de echte waarde ligt "
        "waarschijnlijk tussen die twee getallen. Er zijn geen gegevens over hoeveel er gefietst wordt "
        "en toeristen of pendelaars tellen mee in de ongevallen maar niet in de inwoners; dit is dus "
        "niet het risico per gefietste kilometer."
    ),
    "Bike_Share": "fietsongevallen als % van alle ongevallen met doden of gewonden.",
    "Serious_Share": "ernstige fietsongevallen als % van alle fietsongevallen.",
    "Trend_Pct": (
        "de helling van de rechte lijn door de jaarlijkse fietsongevallengraad, in % van het gemiddelde "
        f"per jaar. Boven +{pipeline.TREND_DREMPEL:.0f} % per jaar is stijgend, onder "
        f"−{pipeline.TREND_DREMPEL:.0f} % dalend, ertussen stabiel. Dit vraagt minstens "
        f"{pipeline.MIN_JAREN_TREND} gekozen jaren."
    ),
}
TREND_PIJL = {"stijgend": "↑", "dalend": "↓", "stabiel": "→"}


def toon_ranglijst(gemeente_jaar, keuze: str, n: dict) -> None:
    """Ranglijst per gewest, provincie of gemeente, met 'Sorteer op' en een minimum aantal."""
    st.markdown(f"#### Ranglijst per {keuze.lower()}")
    sorteer = "Aantal fietsongevallen"
    laagste, top, minimum = False, None, pipeline.MIN_FIETSONGEVALLEN
    if keuze == "Gemeente":
        # Er zijn 581 gemeenten: de keuze bepaalt welke 20 (of meer) je ziet.
        c1, c2, c3, c4 = st.columns([1.2, 3.4, 2, 2])
        top = int(c1.number_input("Aantal gemeenten tonen", min_value=5, max_value=100, value=20, step=5, key="rang_top"))
        sorteer = c2.selectbox(f"Toon de top {top} gemeenten volgens", list(pipeline.SORTEER_OP), key="rang_sorteer")
        laagste = c3.radio("Volgorde", ["Hoogste eerst", "Laagste eerst"], key="rang_volgorde") == "Laagste eerst"
        minimum = int(c4.number_input(
            "Minimum aantal fietsongevallen", min_value=0, max_value=1000, value=pipeline.MIN_FIETSONGEVALLEN,
            step=5, key="rang_minimum",
            help="Geldt enkel bij een verhouding (graad, aandeel of trend): kleine aantallen geven "
            "onbetrouwbare percentages. Telt over de gekozen jaren samen.",
        ))
    kolom = pipeline.SORTEER_OP[sorteer]
    lijst, uitgesloten = pipeline.maak_ranglijst(
        gemeente_jaar, n["kolom"], kolom, minimum, laagste, top
    )
    if lijst.empty:
        st.info("Geen eenheden die aan het minimum voldoen. Verlaag het minimum of kies andere jaren.")
        return

    wegens = "te weinig data"
    tabel = pd.DataFrame({
        "Rang": range(1, len(lijst) + 1),
        keuze: lijst.index,
        "Fietsongevallen": lijst["Bike_Accidents"].map(fmt_getal),
        "Ernstig": lijst["Serious_Bike_Accidents"].map(fmt_getal),
    })
    genoeg = lijst["Genoeg_Data"].to_numpy()

    def toon(waarden, formatter):
        return [formatter(w) if ok and w == w else wegens for w, ok in zip(waarden, genoeg)]

    tabel["Per 100.000 inwoners"] = toon(lijst["Bike_Rate"], fmt_graad)
    tabel["Marge (95 %)"] = [
        f"{fmt_getal(lo, 1)} – {fmt_getal(hi, 1)}" if ok else wegens
        for lo, hi, ok in zip(lijst["Rate_Low"], lijst["Rate_High"], genoeg)
    ]
    tabel["Aandeel fietsongevallen"] = toon(lijst["Bike_Share"], fmt_pct)
    tabel["Aandeel ernstig"] = toon(lijst["Serious_Share"], fmt_pct)
    trends = []
    for soort, pct, ok in zip(lijst["Trend"], lijst["Trend_Pct"], genoeg):
        if not ok:
            trends.append(wegens)
        elif soort == "–":
            trends.append("– (minder dan 4 jaren)")
        else:
            trends.append(f"{TREND_PIJL[soort]} {soort} ({fmt_getal(pct, 1)} % per jaar)")
    tabel["Trend"] = trends
    tabel["Graad per jaar"] = lijst["Rate_Per_Year"].to_list()
    st.dataframe(
        tabel, hide_index=True,
        column_config={"Graad per jaar": st.column_config.LineChartColumn("Graad per jaar", y_min=0)},
    )

    uitleg = f"**Maat ({sorteer.lower()}):** {MAAT_SORTEER[kolom]}"
    st.caption(uitleg)
    if uitgesloten:
        st.caption(
            f"{fmt_getal(uitgesloten)} {n['meervoud']} met minder dan {fmt_getal(minimum)} fietsongevallen "
            "doen niet mee in deze ranglijst (te weinig data); verlaag het minimum om ze toch te zien."
        )
    elif (~genoeg).any():
        st.caption(
            f"Bij {fmt_getal(int((~genoeg).sum()))} {n['meervoud']} met minder dan {fmt_getal(minimum)} "
            "fietsongevallen staat 'te weinig data': de verhoudingen zijn daar te onzeker."
        )
    if kolom == "Bike_Rate" and len(lijst) > 1:
        eerste = lijst.iloc[0] if not laagste else lijst.iloc[-1]
        overlap = int((((lijst["Rate_High"] >= eerste["Rate_Low"]) & (lijst["Rate_Low"] <= eerste["Rate_High"])).sum()) - 1)
        if overlap:
            st.caption(
                f"De marge van {'nummer 1' if not laagste else 'de laagste'} ({eerste.name}) overlapt met die van "
                f"{fmt_getal(overlap)} andere {n['meervoud']} in deze lijst: de volgorde onder hen is niet zeker."
            )
        else:
            st.caption(f"De marge van {eerste.name} overlapt met geen enkele andere eenheid in deze lijst.")


def toon_vergelijking(gemeente_jaar) -> None:
    """Gewesten, provincies of gemeenten vergeleken: bevolking en fietsongevallen, en waar het
    verschil met de eenheid met de meeste fietsongevallen vandaan komt."""
    st.subheader("Vergelijken per gewest, provincie of gemeente")
    keuze = st.radio("Niveau", list(NIVEAUS), horizontal=True, key="vergelijk_niveau")
    n = NIVEAUS[keuze]
    toon_ranglijst(gemeente_jaar, keuze, n)
    top = n["top"]
    eenheden = pipeline.maak_niveauvergelijking(gemeente_jaar, n["kolom"], top)
    if len(eenheden) < 2:
        st.info(f"Kies in de zijbalk meer dan één {keuze.lower()} (of geen) om te vergelijken.")
        return
    wie = f"de {top} {n['meervoud']} met de meeste fietsongevallen" if top else f"alle {n['meervoud']}"
    hoogte = max(280, 60 + 28 * len(eenheden) * 2)

    # 1. Aandeel van de bevolking tegenover aandeel van de fietsongevallen
    aandelen = eenheden.reset_index(names="Eenheid").melt(
        id_vars="Eenheid",
        value_vars=["Population_Share", "Bike_Accidents_Share"],
        var_name="Maat", value_name="Aandeel",
    )
    aandelen["Maat"] = aandelen["Maat"].map(
        {"Population_Share": "Aandeel van de bevolking", "Bike_Accidents_Share": "Aandeel van de fietsongevallen"}
    )
    fig = px.bar(
        aandelen, x="Aandeel", y="Eenheid", color="Maat", barmode="group", orientation="h",
        category_orders={"Eenheid": list(eenheden.index)},
        color_discrete_map={"Aandeel van de bevolking": KLEUR_BEVOLKING, "Aandeel van de fietsongevallen": KLEUR_GRAAD},
        text=aandelen["Aandeel"].map(lambda x: fmt_getal(x, 1) + " %"),
    )
    fig.update_traces(hovertemplate="%{x:.1f} %<extra>%{fullData.name}</extra>", textposition="outside")
    fig.update_layout(
        title=f"{n['elk'] if not top else 'De ' + str(top) + ' ' + n['meervoud'] + ' met de meeste fietsongevallen'}: aandeel van de bevolking en van de fietsongevallen",
        xaxis={"title": None, "ticksuffix": " %", "range": [0, aandelen["Aandeel"].max() * 1.2]},
        yaxis={"title": None},  # px zet bij horizontale balken de eerste categorie al bovenaan
        legend_title_text=None, legend_orientation="h", legend_y=-0.15 if len(eenheden) < 6 else -0.08,
        margin={"t": 50, "b": 20, "l": 10, "r": 10}, height=hoogte, separators=",.",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"**Maat:** het aandeel van {n['dit']} in de bevolking (som van de inwoners over de gekozen "
        f"jaren) naast het aandeel in alle fietsongevallen, beide over alle {n['meervoud']} in de "
        f"selectie. Zijn de twee balken even lang, dan heeft {n['dit']} evenveel fietsongevallen als "
        "je op basis van het aantal inwoners zou verwachten. Is de oranje balk langer, dan zijn er "
        "meer fietsongevallen dan het aantal inwoners doet verwachten; is hij korter, dan zijn het er minder."
        + (f" Getoond: {wie}." if top else "")
    )

    # 2. De twee oorzaken in één beeld: aantal inwoners (x) en fietsongevallen per inwoner (y)
    referentie = eenheden["Bike_Accidents"].idxmax()
    jaren = gemeente_jaar["Year"].nunique()
    punten = eenheden.reset_index(names="Eenheid")
    punten["Inwoners"] = punten["Total"] / jaren
    punten["Rol"] = punten["Eenheid"].map(lambda e: referentie if e == referentie else "Andere")
    ref = punten[punten["Eenheid"] == referentie].iloc[0]
    fig = px.scatter(
        punten, x="Inwoners", y="Bike_Rate", size="Bike_Accidents", color="Rol", text="Eenheid",
        size_max=50, category_orders={"Rol": [referentie, "Andere"]},
        color_discrete_map={referentie: KLEUR_GRAAD, "Andere": KLEUR_BEVOLKING},
        custom_data=["Eenheid", "Bike_Accidents"],
    )
    fig.update_traces(
        textposition="top center",
        marker={"opacity": 0.75, "line": {"width": 1, "color": "white"}},
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>%{x:,.0f} inwoners (per jaar)<br>%{y:.1f} fietsongevallen "
            "per 100.000 inwoners<br>%{customdata[1]:,.0f} fietsongevallen<extra></extra>"
        ),
    )
    fig.add_vline(x=ref["Inwoners"], line_dash="dash", line_color="gray", opacity=0.6)
    fig.add_hline(y=ref["Bike_Rate"], line_dash="dash", line_color="gray", opacity=0.6)
    wie_titel = f"de {top} {n['meervoud']}" if top else f"alle {n['meervoud']}"
    fig.update_layout(
        title=f"Meer inwoners of meer ongevallen per inwoner? {wie_titel.capitalize()} naast {referentie}",
        xaxis={"title": "Inwoners (gemiddeld per jaar)", "rangemode": "tozero", "separatethousands": True},
        yaxis={"title": "Fietsongevallen per 100.000 inwoners (per jaar)", "rangemode": "tozero"},
        legend_title_text=None, legend_orientation="h", legend_y=-0.2,
        margin={"t": 50, "b": 20, "l": 10, "r": 10}, height=560, separators=",.",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"**Maat:** elke bol is {n['dit']}. Links-rechts: het gemiddeld aantal inwoners per jaar. "
        "Boven-onder: het aantal fietsongevallen per 100.000 inwoners per jaar. De grootte van de bol: "
        f"het totaal aantal fietsongevallen. De stippellijnen tonen {referentie}, het "
        f"{keuze.lower()} met de meeste fietsongevallen. Een bol rechts van de verticale lijn heeft meer "
        "inwoners, een bol boven de horizontale lijn meer fietsongevallen per inwoner. Een grote bol "
        "betekent veel inwoners, veel ongevallen per inwoner, of allebei. Er zijn geen gegevens over hoeveel "
        "er gefietst wordt: 'per inwoner' is niet 'per gefietste kilometer'."
    )


GRIJS = "#b8b8b8"


def tijd_aantalgrafiek(verdeling, labels: list[str], titel: str, as_titel: str):
    """Staafdiagram: aantal fietsongevallen per uur of maand."""
    fig = px.bar(x=labels, y=verdeling["Bike_Accidents"].to_list())
    fig.update_traces(marker_color=LIJNKLEUR, hovertemplate="%{x}: %{y:,.0f} fietsongevallen<extra></extra>")
    fig.update_layout(
        title=titel, xaxis={"title": as_titel, "type": "category"},
        yaxis={"title": None, "separatethousands": True, "rangemode": "tozero"},
        margin={"t": 50, "b": 20, "l": 10, "r": 10}, height=340, separators=",.",
    )
    return fig


def tijd_ernstgrafiek(verdeling, labels: list[str], titel: str, as_titel: str, gemiddeld: float | None):
    """Staafdiagram: aandeel ernstig per uur of maand. Staven met te weinig fietsongevallen zijn grijs."""
    genoeg = verdeling["Bike_Accidents"] >= pipeline.MIN_FIETSONGEVALLEN
    kleuren = [KLEUR_GRAAD if g else GRIJS for g in genoeg]
    fig = px.bar(x=labels, y=verdeling["Serious_Share"].to_list(), custom_data=[
        verdeling["Bike_Accidents"].to_list(), verdeling["Serious_Bike_Accidents"].to_list(),
    ])
    fig.update_traces(
        marker_color=kleuren,
        hovertemplate=(
            "%{x}: %{y:.1f} % ernstig<br>%{customdata[1]:,.0f} van %{customdata[0]:,.0f} "
            "fietsongevallen<extra></extra>"
        ),
    )
    if gemiddeld is not None:
        fig.add_hline(
            y=gemiddeld, line_dash="dash", line_color="gray",
            annotation_text=f"gemiddeld {fmt_getal(gemiddeld, 1)} %", annotation_position="top right",
        )
    fig.update_layout(
        title=titel, xaxis={"title": as_titel, "type": "category"},
        yaxis={"title": None, "ticksuffix": " %", "rangemode": "tozero"},
        margin={"t": 50, "b": 20, "l": 10, "r": 10}, height=340, separators=",.",
    )
    return fig


def toon_wanneer(gefilterd, tabellen) -> None:
    """Wanneer gebeuren fietsongevallen: per uur van de dag en per maand."""
    for kolom, titel, labels, as_titel in [
        ("Hour", "uur van de dag", [str(u) for u in range(24)], "Uur van de dag"),
        ("Month", "maand", MAANDEN, "Maand"),
    ]:
        verdeling, onbekend = pipeline.maak_tijdverdeling(gefilterd, tabellen, kolom)
        totaal = int(verdeling["Bike_Accidents"].sum())
        st.subheader(f"Per {titel}")
        if totaal == 0:
            st.info("Geen fietsongevallen voor deze selectie.")
            continue
        gemiddeld = verdeling["Serious_Bike_Accidents"].sum() / totaal * 100
        links, rechts = st.columns(2)
        with links:
            st.plotly_chart(
                tijd_aantalgrafiek(verdeling, labels, f"Fietsongevallen per {titel}", as_titel),
                width="stretch",
            )
        with rechts:
            st.plotly_chart(
                tijd_ernstgrafiek(verdeling, labels, f"Aandeel ernstig per {titel} (%)", as_titel, gemiddeld),
                width="stretch",
            )
        piek = verdeling["Bike_Accidents"].idxmax()
        piek_tekst = f"{piek} uur" if kolom == "Hour" else MAANDEN[piek - 1]
        rustig = verdeling["Bike_Accidents"].idxmin()
        rustig_tekst = f"{rustig} uur" if kolom == "Hour" else MAANDEN[rustig - 1]
        zwak = int((verdeling["Bike_Accidents"] < pipeline.MIN_FIETSONGEVALLEN).sum())
        st.caption(
            f"**Maat links:** aantal fietsongevallen (met doden of gewonden) per {titel}, over de gekozen jaren "
            f"samen. Het meeste: {piek_tekst} ({fmt_getal(verdeling['Bike_Accidents'].max())}); het minste: "
            f"{rustig_tekst} ({fmt_getal(verdeling['Bike_Accidents'].min())}). Het zegt niets over het risico "
            "per fietser: op drukke momenten fietsen er ook meer mensen. "
            f"**Maat rechts:** ernstige fietsongevallen als % van de fietsongevallen in dat {titel}. De stippellijn is "
            f"het gemiddelde ({fmt_getal(gemiddeld, 1)} %). "
            + (
                f"Grijze staven hebben minder dan {pipeline.MIN_FIETSONGEVALLEN} fietsongevallen; "
                "daar schommelt het percentage sterk door toeval. " if zwak else ""
            )
            + "Als je met de muis over een staaf gaat, zie je het aantal waarop het percentage steunt."
        )
        if onbekend:
            st.caption(f"{fmt_getal(onbekend)} fietsongevallen met onbekend uur staan niet in deze grafieken.")


# (tabtekst, filternaam, "Overige" onder dit %, zin over de categorieën)
OMSTANDIGHEDEN = [
    ("Licht", "Light Condition", None, "lichtomstandigheid"),
    ("Weer", "Weather", 1.0, "weersomstandigheid"),
    ("Wegdek", "Road Condition", 1.0, "toestand van het wegdek"),
    ("Kruispunt", "Crossway", None, "plaats (op of buiten een kruispunt)"),
    ("Wegtype", "Road Type", None, "wegtype"),
]


VAAK_VOORKOMEN = (
    "bij een omstandigheid die vaak voorkomt (zoals droog weer of daglicht) gebeuren ook de meeste ongevallen"
)


def toon_omstandigheid(
    gefilterd, tabellen, filternaam: str, overige_onder, woord: str,
    data=None, vaak_voorkomen: str = VAAK_VOORKOMEN, onbekend_betekent: str = "de omstandigheid niet is ingevuld",
) -> None:
    """Fietsongevallen per categorie (van een omstandigheid of van de tegenpartij): aantal, en aandeel ernstig."""
    if data is None:
        data = pipeline.maak_omstandigheid(gefilterd, tabellen, filternaam, overige_onder)
    if data.empty:
        st.info("Geen fietsongevallen voor deze selectie.")
        return
    totaal = int(data["Bike_Accidents"].sum())
    gemiddeld = data["Serious_Bike_Accidents"].sum() / totaal * 100
    volgorde = list(data.index)
    genoeg = data["Bike_Accidents"] >= pipeline.MIN_FIETSONGEVALLEN
    hoogte = max(260, 80 + 34 * len(data))

    links, rechts = st.columns(2)
    fig = px.bar(
        x=data["Bike_Accidents"].to_list(), y=volgorde, orientation="h",
        category_orders={"y": volgorde},
        text=[f"{fmt_getal(n)} ({fmt_pct(s)})" for n, s in zip(data["Bike_Accidents"], data["Share"])],
    )
    fig.update_traces(
        marker_color=LIJNKLEUR, textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:,.0f} fietsongevallen<extra></extra>",
    )
    fig.update_layout(
        title=f"Fietsongevallen per {woord}",
        xaxis={"title": None, "separatethousands": True, "range": [0, data["Bike_Accidents"].max() * 1.35]},
        yaxis={"title": None}, margin={"t": 50, "b": 20, "l": 10, "r": 10}, height=hoogte, separators=",.",
    )
    links.plotly_chart(fig, width="stretch")

    fig = px.bar(
        x=data["Serious_Share"].to_list(), y=volgorde, orientation="h",
        category_orders={"y": volgorde},
        custom_data=[data["Bike_Accidents"].to_list(), data["Serious_Bike_Accidents"].to_list()],
        text=[fmt_pct(s) for s in data["Serious_Share"]],
    )
    fig.update_traces(
        marker_color=[KLEUR_GRAAD if g else GRIJS for g in genoeg], textposition="outside", cliponaxis=False,
        hovertemplate=(
            "%{y}: %{x:.1f} % ernstig<br>%{customdata[1]:,.0f} van %{customdata[0]:,.0f} "
            "fietsongevallen<extra></extra>"
        ),
    )
    fig.add_vline(
        x=gemiddeld, line_dash="dash", line_color="gray",
        annotation_text=f"gemiddeld {fmt_getal(gemiddeld, 1)} %", annotation_position="top",
    )
    fig.update_layout(
        title=f"Aandeel ernstig per {woord} (%)",
        xaxis={"title": None, "ticksuffix": " %", "range": [0, max(data["Serious_Share"].max(), gemiddeld) * 1.3]},
        yaxis={"title": None}, margin={"t": 50, "b": 20, "l": 10, "r": 10}, height=hoogte, separators=",.",
    )
    rechts.plotly_chart(fig, width="stretch")

    uitleg = (
        f"**Maat links:** aantal fietsongevallen (en % van alle {fmt_getal(totaal)}) per {woord}. Dit zegt niets over "
        f"het risico per fietser: {vaak_voorkomen}. **Maat rechts:** ernstige fietsongevallen als % van de fietsongevallen in die "
        f"categorie; de stippellijn is het gemiddelde ({fmt_getal(gemiddeld, 1)} %). "
    )
    if not genoeg.all():
        uitleg += (
            f"Grijze staven hebben minder dan {pipeline.MIN_FIETSONGEVALLEN} fietsongevallen: daar schommelt het "
            "percentage sterk door toeval. "
        )
    uitleg += (
        "Het aandeel ernstig zegt niet waarom: de data bevat bijvoorbeeld geen snelheid of alcohol. "
        "Een hoger aandeel kan ook komen doordat er in die omstandigheid minder (lichte) ongevallen geregistreerd worden."
    )
    st.caption(uitleg)

    if overige_onder is not None and pipeline.OVERIGE_LABEL in data.index:
        zonder = pipeline.maak_omstandigheid(gefilterd, tabellen, filternaam, None)
        leden = [c for c in zonder.index if c not in data.index]
        st.caption(
            f"**Overige** bevat de {len(leden)} categorieën met minder dan {fmt_getal(overige_onder, 0)} % van de "
            f"fietsongevallen: {', '.join(leden)}."
        )
    if pipeline.ONBEKEND_LABEL in data.index and data.loc[pipeline.ONBEKEND_LABEL, "Bike_Accidents"] >= pipeline.MIN_FIETSONGEVALLEN:
        o = data.loc[pipeline.ONBEKEND_LABEL]
        verklaring = (
            " Een mogelijke verklaring is dat lichtere ongevallen minder volledig worden ingevuld; dat staat niet in de data."
            if o["Serious_Share"] < gemiddeld else ""
        )
        st.caption(
            f"**Onbekend** ({fmt_pct(o['Share'])} van de fietsongevallen) betekent dat {onbekend_betekent}; "
            f"het aandeel ernstig is daar {fmt_pct(o['Serious_Share'])}.{verklaring}"
        )
    if filternaam == "Road Type":
        st.caption(
            "De autosnelweg staat standaard uit (zie de melding bovenaan); selecteer ze in de zijbalk om ze mee te rekenen."
        )


def toon_tegenpartij(gefilterd, tabellen) -> None:
    """Met wie botst de fietser, en hoe vaak is het ernstig."""
    st.subheader("Met wie botst de fietser?")
    data = pipeline.maak_tegenpartij(gefilterd, tabellen)
    toon_omstandigheid(
        gefilterd, tabellen, "Tegenpartij", None, "tegenpartij", data=data,
        vaak_voorkomen="een tegenpartij die vaak voorkomt (zoals een personenauto) zit ook in de meeste ongevallen, "
        "omdat er veel meer personenauto's dan vrachtwagens rondrijden",
        onbekend_betekent="de tegenpartij niet is ingevuld",
    )
    st.caption(
        "**Tegenpartij** is de weggebruiker (1 of 2) die niet de fiets is. Zijn beide partijen een fiets, dan staat "
        f"het ongeval onder '{pipeline.FIETS_TEGEN_FIETS_LABEL}'. 'Eén bestuurder, geen hindernis' en 'Een "
        "weggebruiker tegen een hindernis' zijn ongevallen zonder andere weggebruiker (eenzijdig). Een ongeval telt "
        "één keer; het aandeel ernstig per tegenpartij zegt niet wie de schuld heeft en houdt geen rekening met "
        "snelheid of massa."
    )


def toon_omstandigheden(gefilterd, tabellen) -> None:
    sub = st.tabs([tekst for tekst, *_ in OMSTANDIGHEDEN])
    for tab, (_, filternaam, overige_onder, woord) in zip(sub, OMSTANDIGHEDEN):
        with tab:
            toon_omstandigheid(gefilterd, tabellen, filternaam, overige_onder, woord)


def toon_trend(gemeente_jaar, maandtelling) -> None:
    per_jaar = pipeline.maak_jaartrend(gemeente_jaar)
    links, midden, rechts = st.columns(3)
    with links:
        st.plotly_chart(
            lijngrafiek(per_jaar, "Bike_Rate", "Fietsongevallen per 100.000 inwoners", ""),
            width="stretch",
        )
        st.caption(MAAT_UITLEG["graad"])
    with midden:
        st.plotly_chart(
            lijngrafiek(per_jaar, "Bike_Share", "Aandeel fietsongevallen (%)", " %"),
            width="stretch",
        )
        st.caption(MAAT_UITLEG["aandeel"])
    with rechts:
        st.plotly_chart(
            lijngrafiek(per_jaar, "Serious_Share", "Aandeel ernstig (fiets, %)", " %"),
            width="stretch",
        )
        st.caption(MAAT_UITLEG["ernstig"])
    toon_maandgrafiek(maandtelling)
    with st.expander("Cijfers per jaar"):
        tabel = per_jaar[
            ["Year", "Bike_Accidents", "Serious_Bike_Accidents", "Bike_Rate", "Bike_Share", "Serious_Share"]
        ].rename(
            columns={
                "Year": "Jaar",
                "Bike_Accidents": "Fietsongevallen",
                "Serious_Bike_Accidents": "Ernstig",
                "Bike_Rate": "Per 100.000 inwoners",
                "Bike_Share": "Aandeel fietsongevallen (%)",
                "Serious_Share": "Aandeel ernstig (%)",
            }
        )
        tabel["Per 100.000 inwoners"] = tabel["Per 100.000 inwoners"].map(fmt_graad)
        for kolom in ("Aandeel fietsongevallen (%)", "Aandeel ernstig (%)"):
            tabel[kolom] = tabel[kolom].map(lambda x: fmt_getal(x, 1))
        st.dataframe(formatteer_tabel(tabel), hide_index=True)


def toon_datakwaliteit(tabellen, controles) -> None:
    """Controles op de volledige data; de filters gelden hier niet."""
    st.caption("Dit tabblad gaat over de volledige data en volgt de filters niet.")
    st.write(
        f"Ingelezen: {fmt_getal(controles['Ongevallen ingelezen'])} ongevallen; "
        f"waarvan {fmt_getal(pipeline.aantal_autosnelweg(tabellen))} op de autosnelweg "
        "(standaard niet getoond). Er gaan geen ongevallen verloren."
    )

    st.subheader("Bevolking: controle per jaar")
    st.caption("De som van de gemeenten moet gelijk zijn aan de rij 'België' van dat jaar.")
    st.dataframe(formatteer_tabel(controles["Controle bevolking"].reset_index()), hide_index=True)

    st.subheader("NIS-codes die maar in één bestand voorkomen")
    verschillen = controles["Datakwaliteit NIS"]
    if verschillen.empty:
        st.write("Alle NIS-codes komen in elk jaar in beide bestanden voor.")
    else:
        st.caption(
            "'Alleen in bevolking': de gemeente had dat jaar geen ongevallen (op geen enkel wegtype) "
            "en krijgt 0 ongevallen (niet 'ontbrekend'). 'Alleen in ongevallen': er is geen bevolking "
            "voor die code."
        )
        st.dataframe(formatteer_tabel(verschillen), hide_index=True)


(
    tab_trend, tab_kaart, tab_waar, tab_wanneer, tab_omstandigheden, tab_tegenpartij, tab_kwaliteit,
) = st.tabs(["Trend", "Kaart", "Waar", "Wanneer", "Omstandigheden", "Tegenpartij", "Datakwaliteit"])
with tab_kwaliteit:
    toon_datakwaliteit(tabellen, controles)

if not gefilterd.empty:
    gemeente_jaar = pipeline.maak_gemeente_jaar(gefilterd, tabellen, keuzes)
    with tab_trend:
        toon_trend(gemeente_jaar, pipeline.maak_maandtelling(gefilterd, tabellen))
    with tab_kaart:
        toon_kaart(gefilterd, tabellen)
    with tab_waar:
        toon_vergelijking(gemeente_jaar)
    with tab_wanneer:
        toon_wanneer(gefilterd, tabellen)
    with tab_omstandigheden:
        toon_omstandigheden(gefilterd, tabellen)
    with tab_tegenpartij:
        toon_tegenpartij(gefilterd, tabellen)
else:
    for tab_leeg in (tab_trend, tab_kaart, tab_waar, tab_wanneer, tab_omstandigheden, tab_tegenpartij):
        with tab_leeg:
            st.caption("Geen ongevallen om te tonen (zie de melding bovenaan).")
