# Fietsongevallen in België, 2017–2024

Streamlit-app voor een schoolopdracht (Syntra, Data Scientist).

**Centrale vraag:** waar in België zijn fietsongevallen het talrijkst en het ernstigst
(gemeente / provincie / gewest), en is dat veranderd sinds 2017?

## Structuur

| Bestand | Rol |
|---|---|
| `app.py` | de Streamlit-interface |
| `pipeline.py` | de datavoorbereiding, één functie per stap (geen Streamlit) |
| `requirements.txt` | enkel de packages die de app importeert |
| `data/` | de brondata (niet in git) |
| `.env` | geheimen, indien nodig (niet in git) |

## Starten

```powershell
conda activate syntra-ds
streamlit run app.py
```

## Status

Skelet: de functies in `pipeline.py` zijn nog leeg.
