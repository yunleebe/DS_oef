"""Streamlit-interface: fietsongevallen in België, 2017-2024.

Start met: streamlit run app.py
De datavoorbereiding zit in pipeline.py.
"""

import streamlit as st

import pipeline

st.set_page_config(page_title="Fietsongevallen in België", layout="wide")


@st.cache_data(show_spinner="Data wordt geladen...")
def laad_datamodel():
    return pipeline.laad_of_bouw_datamodel()


st.title("Fietsongevallen in België, 2017–2024")
st.write(
    "Waar zijn fietsongevallen het talrijkst en het ernstigst "
    "(gemeente, provincie, gewest), en is dat veranderd sinds 2017?"
)
st.warning(
    "Ongevallen op de **autosnelweg** zijn uitgesloten uit de hele analyse: "
    "fietsers mogen daar niet rijden en ze zouden het aandeel fietsongevallen "
    "in gemeenten met een autosnelweg verlagen."
)

tabellen, controles = laad_datamodel()

st.header("Datakwaliteit")
st.write(
    f"Ingelezen: {controles['Ongevallen ingelezen']:,} ongevallen; "
    f"{controles['Autosnelweg uitgesloten']:,} op de autosnelweg uitgesloten; "
    f"{len(tabellen['Fact_Accidents']):,} blijven over.".replace(",", ".")
)

st.subheader("Bevolking: controle per jaar")
st.caption("De som van de gemeenten moet gelijk zijn aan de rij 'België' van dat jaar.")
st.dataframe(controles["Controle bevolking"])

st.subheader("NIS-codes die maar in één bestand voorkomen")
verschillen = controles["Datakwaliteit NIS"]
if verschillen.empty:
    st.write("Alle NIS-codes komen in elk jaar in beide bestanden voor.")
else:
    st.caption(
        "'Alleen in bevolking': de gemeente had dat jaar geen ongevallen en krijgt "
        "0 ongevallen (niet 'ontbrekend'). 'Alleen in ongevallen': er is geen bevolking "
        "voor die code."
    )
    st.dataframe(verschillen, hide_index=True)
