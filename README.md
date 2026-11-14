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
| `data/` | de brondata, Excel (niet in git) |
| `data/parquet/` | het verwerkte datamodel (wel in git, zodat de app ook zonder Excel draait) |
| `beslissingslogboek.md` | welke keuzes gemaakt werden en waarom |
| `.env` | geheimen, indien nodig (niet in git) |

## Starten

```powershell
conda activate syntra-ds
streamlit run app.py
```

De app leest `data/parquet/`. Zijn de Excel-bestanden er en is de parquet verouderd, dan wordt
ze automatisch herbouwd (ongeveer 1,5 minuut). Zelf herbouwen kan met:

```powershell
python pipeline.py
```

## Status

De datavoorbereiding en het datamodel werken (dimensies, `Fact_Accidents`, `Fact_Population`,
koppeling per gemeente en jaar). De app toont voorlopig enkel de sectie Datakwaliteit; de
analyse en de kaart volgen.
