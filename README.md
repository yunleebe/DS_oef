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

## Wat de app toont

Bovenaan de belangrijkste cijfers en in de zijbalk twaalf filters (de autosnelweg staat standaard
uit). Daaronder zeven tabbladen:

| Tabblad | Inhoud |
|---|---|
| Trend | fietsongevallengraad, aandeel fietsongevallen en aandeel ernstig per jaar; aantal per maand |
| Kaart | concentratiekaart of afzonderlijke punten, voor fietsongevallen of alle ongevallen |
| Waar | ranglijst per gewest, provincie of gemeente (met 95 %-marge en trend) en bolgrafiek |
| Wanneer | per uur van de dag en per maand |
| Omstandigheden | licht, weer, wegdek, kruispunt, wegtype |
| Tegenpartij | met wie de fietser botst |
| Datakwaliteit | controles op de bevolking en de NIS-codes |

## Publiceren op Streamlit Community Cloud

De app draait op Cloud zonder de Excel-bestanden: ze leest `data/parquet/` (in git).

1. Zorg dat alle wijzigingen gecommit en gepusht zijn, ook `data/parquet/`.
2. Ga naar <https://share.streamlit.io>, log in met GitHub en kies **Create app** > *Deploy a public app from GitHub*.
3. Repository: `yunleebe/DS_oef`, branch `main`, main file path: `app.py`.
4. Open **Advanced settings** en kies **Python 3.13** (zoals de omgeving `syntra-ds`).
5. Klik **Deploy**. Het eerste starten duurt enkele minuten (packages installeren).

Na een wijziging aan `pipeline.py` of de data: bouw de parquet opnieuw (`python pipeline.py`) en
commit ze samen met de code. Cloud herstart de app na elke push automatisch.

## Status

De datavoorbereiding, het datamodel en alle visuals werken; de app is klaar om te publiceren.
Tests schreven we niet (zie het beslissingslogboek, beslissing 20).
