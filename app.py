"""Streamlit-interface: fietsongevallen in België, 2017-2024.

Start met: streamlit run app.py
De datavoorbereiding zit in pipeline.py.
"""

import streamlit as st

import pipeline  # noqa: F401  (wordt gebruikt zodra de stappen ingevuld zijn)

st.set_page_config(page_title="Fietsongevallen in België", layout="wide")

st.title("Fietsongevallen in België, 2017–2024")
st.write(
    "Waar zijn fietsongevallen het talrijkst en het ernstigst "
    "(gemeente, provincie, gewest), en is dat veranderd sinds 2017?"
)

st.info("Skelet: de dataverwerking en de grafieken komen in de volgende stappen.")
