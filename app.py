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


def toon_vergelijking(gemeente_jaar) -> None:
    """Gewesten, provincies of gemeenten vergeleken: bevolking en fietsongevallen, en waar het
    verschil met de eenheid met de meeste fietsongevallen vandaan komt."""
    st.subheader("Vergelijken per gewest, provincie of gemeente")
    keuze = st.radio("Niveau", list(NIVEAUS), horizontal=True, key="vergelijk_niveau")
    n = NIVEAUS[keuze]
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
        yaxis={"title": None, "autorange": "reversed"},
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

    # 2. Waar komt het verschil met de eenheid met de meeste fietsongevallen vandaan?
    referentie = eenheden["Bike_Accidents"].idxmax()
    rijen = []
    for ander in eenheden.index:
        if ander != referentie:
            rijen.append({"Eenheid": ander, **pipeline.ontleed_verschil(eenheden, referentie, ander)})
    ontleding = pd.DataFrame(rijen)
    zelfde_richting = ontleding["Bevolking"] * ontleding["Graad"] >= 0
    getoond = ontleding[zelfde_richting].copy()
    getoond["Door minder inwoners"] = getoond["Bevolking"] / getoond["Verschil"] * 100
    getoond["Door minder ongevallen per inwoner"] = 100 - getoond["Door minder inwoners"]
    if not getoond.empty:
        lang = getoond.melt(
            id_vars="Eenheid",
            value_vars=["Door minder inwoners", "Door minder ongevallen per inwoner"],
            var_name="Oorzaak", value_name="Deel",
        )
        fig = px.bar(
            lang, x="Deel", y="Eenheid", color="Oorzaak", barmode="stack", orientation="h",
            category_orders={"Eenheid": [e for e in eenheden.index if e in set(getoond["Eenheid"])]},
            color_discrete_map={
                "Door minder inwoners": KLEUR_BEVOLKING,
                "Door minder ongevallen per inwoner": KLEUR_GRAAD,
            },
            text=lang["Deel"].map(lambda x: fmt_getal(x) + " %"),
        )
        fig.update_traces(hovertemplate="%{x:.1f} %<extra>%{fullData.name}</extra>", textposition="inside")
        fig.update_layout(
            title=f"Waarom hebben de andere {n['meervoud']} minder fietsongevallen dan {referentie}?",
            xaxis={"title": "100 % = het hele verschil in aantal fietsongevallen", "range": [0, 100], "ticksuffix": " %"},
            yaxis={"title": None, "autorange": "reversed"},
            legend_title_text=None, legend_orientation="h", legend_y=-0.35 if len(getoond) < 6 else -0.15,
            margin={"t": 50, "b": 20, "l": 10, "r": 10},
            height=max(300, 90 + 28 * len(getoond)), separators=",.",
        )
        st.plotly_chart(fig, width="stretch")
    voorbeeld = ontleding.loc[ontleding["Verschil"].abs().idxmax()]
    uitleg = (
        f"**Maat:** het verschil in aantal fietsongevallen met {referentie} ({n['dit']} met de meeste), "
        f"opgesplitst in twee oorzaken: (1) {n['dat']} heeft minder inwoners, (2) per inwoner zijn er "
        "minder fietsongevallen. De twee delen tellen op tot 100 %. Voorbeeld: "
    )
    if voorbeeld["Bevolking"] * voorbeeld["Graad"] >= 0:
        deel = voorbeeld["Bevolking"] / voorbeeld["Verschil"] * 100
        uitleg += (
            f"{voorbeeld['Eenheid']} heeft {fmt_getal(abs(voorbeeld['Verschil']))} fietsongevallen minder dan "
            f"{referentie}. {fmt_getal(deel)} % daarvan komt doordat er minder inwoners zijn, "
            f"{fmt_getal(100 - deel)} % doordat er per inwoner minder fietsongevallen zijn. "
        )
    else:
        uitleg += "zie de tabel met cijfers hieronder. "
    uitleg += (
        "De delen zijn berekend met het gemiddelde van beide eenheden, zodat het resultaat niet "
        "afhangt van welke als vertrekpunt dient. Er zijn geen gegevens over hoeveel er gefietst "
        "wordt: 'per inwoner' is niet 'per gefietste kilometer'."
    )
    st.caption(uitleg)
    if not zelfde_richting.all():
        st.caption(
            f"Niet getoond ({int((~zelfde_richting).sum())}): "
            + ", ".join(ontleding.loc[~zelfde_richting, "Eenheid"])
            + ". Daar werken de twee oorzaken in tegengestelde richting (bijvoorbeeld meer inwoners "
            "maar toch minder fietsongevallen), zodat percentages niet zinvol zijn."
        )
    with st.expander(f"Cijfers per {keuze.lower()}"):
        tabel = eenheden.reset_index(names=keuze)[[keuze, "Total", "Bike_Accidents", "Bike_Rate"]].rename(
            columns={
                "Total": "Inwoners (som over de gekozen jaren)",
                "Bike_Accidents": "Fietsongevallen",
                "Bike_Rate": "Per 100.000 inwoners",
            }
        )
        tabel["Per 100.000 inwoners"] = tabel["Per 100.000 inwoners"].map(fmt_graad)
        st.dataframe(formatteer_tabel(tabel), hide_index=True)


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


if not gefilterd.empty:
    gemeente_jaar = pipeline.maak_gemeente_jaar(gefilterd, tabellen, keuzes)
    tab_trend, tab_kaart, tab_waar, tab_wanneer, tab_omstandigheden, tab_tegenpartij = st.tabs(
        ["Trend", "Kaart", "Waar", "Wanneer", "Omstandigheden", "Tegenpartij"]
    )
    with tab_trend:
        toon_trend(gemeente_jaar, pipeline.maak_maandtelling(gefilterd, tabellen))
    with tab_kaart:
        toon_kaart(gefilterd, tabellen)
    with tab_waar:
        toon_vergelijking(gemeente_jaar)
    for tab_nog_niet in ( tab_wanneer, tab_omstandigheden, tab_tegenpartij):
        with tab_nog_niet:
            st.caption("Dit onderdeel komt in een volgende stap.")

st.header("Datakwaliteit")
st.caption("Deze sectie gaat over de volledige data en volgt de filters niet.")
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
