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
8. **Beslissingslogboek**: noteer elke beslissing van Yun in `beslissingslogboek.md`
   (vraag, antwoord, reden).

## Definities (ongevallendata)

- Een rij is een ongeval. De dataset bevat enkel ongevallen met minstens één dode of gewonde.
- **Fietsongeval**: `CD_ROAD_USR_TYPE1` of `CD_ROAD_USR_TYPE2` is "Fiets" (code 3). Elk ongeval
  telt één keer, ook als beide partijen een fiets zijn.
- **Ernstig ongeval**: `CD_CLASS_ACCIDENTS` is "Met doden", "dodelijk gewonden" of
  "met zwaargewonden" (codes 1, 2, 3).
- **Fietsongevallengraad**: fietsongevallen per 100.000 inwoners, met de bevolking van
  hetzelfde jaar.
- **Aandeel fietsongevallen**: % fietsongevallen van alle ongevallen (zonder autosnelweg).
- **Aandeel ernstig (fiets)**: % ernstige ongevallen van alle fietsongevallen.
- **Autosnelweg** (`CD_ROAD_TYPE` = 1) is uitgesloten voor de hele analyse, omdat fietsers daar
  niet mogen rijden. Dit staat altijd zichtbaar bovenaan in de app.

## Opschonen (ongevallendata)

- Brussel krijgt "Brussels Hoofdstedelijk Gewest" als provincie.
- Rijen zonder coördinaten blijven in de analyse.
- De 66 volledig identieke rijen blijven staan.
- Alle kolommen die met `CD_` beginnen zijn ID-kolommen en blijven tekst; `CD_NIS` ook
  (voorloopnullen blijven behouden).
- Alle kolommen die op `_FR` eindigen worden verwijderd.
