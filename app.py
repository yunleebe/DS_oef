"""Streamlit-interface: fietsongevallen in België, 2017-2024.

Start met: streamlit run app.py
De datavoorbereiding en de filterlogica zitten in pipeline.py.
"""

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


def toon_trend(gemeente_jaar) -> None:
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
        toon_trend(gemeente_jaar)
    for tab_nog_niet in (tab_kaart, tab_waar, tab_wanneer, tab_omstandigheden, tab_tegenpartij):
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
