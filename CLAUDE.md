# Fietsongevallen in België (2017–2024) — Streamlit-app

Schoolopdracht (Syntra Data Scientist). Centrale vraag: waar in België zijn fietsongevallen het
talrijkst en het ernstigst (gemeente / provincie / gewest), en is dat veranderd sinds 2017?

## Afspraken

1. **Structuur**: `app.py` is enkel de interface. De datavoorbereiding staat in `pipeline.py`,
   met aparte, benoemde functies (één per stap) en **geen Streamlit-imports**.
2. **`requirements.txt`** bevat enkel wat de app importeert, met versienummers
   (nu: streamlit, pandas).
3. **Nieuw package nodig?** Vraag het EERST aan Yun, met reden en alternatief.
   Installeer niets zonder OK.
4. **Data** staat in `data/`, **geheimen** in `.env`. `data/`, `.env`, `__pycache__/` en `.venv/`
   staan in `.gitignore`.
5. **Omgeving**: de conda-omgeving `syntra-ds` is de standaard. Zolang de packages uit
   `requirements.txt` daarin staan, mag je ze gebruiken. Maak geen eigen `.venv`.
6. **Git**: de map is al een repo; geen `git init`. Yun doet de commits zelf, met een eigen
   boodschap. Commit nooit. Meld wanneer een stap werkt, zodat Yun kan committen.
7. **Windows** is het standaardbesturingssysteem (PowerShell, `C:\Users\<jij>\...`).
