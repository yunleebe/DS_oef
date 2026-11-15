# Fietsongevallen in België (2017–2024) — Streamlit-app

Schoolopdracht (Syntra Data Scientist). Centrale vraag: waar in België zijn fietsongevallen het
talrijkst en het ernstigst (gemeente / provincie / gewest), en is dat veranderd sinds 2017?

## Afspraken

1. **Structuur**: `app.py` is enkel de interface. De datavoorbereiding staat in `pipeline.py`,
   met aparte, benoemde functies (één per stap) en **geen Streamlit-imports**.
2. **`requirements.txt`** bevat enkel wat de app importeert, met versienummers
   (nu: streamlit, pandas, openpyxl, pyproj, pyarrow).
3. **Nieuw package nodig?** Staat het niet in `syntra-ds`: vraag het EERST aan Yun, met reden en
   alternatief, en zet het niet in `requirements.txt`. Installeer niets zonder OK.
   Staat het wel in `syntra-ds` en heeft de app het nodig, dan mag het zonder vragen in
   `requirements.txt` (met versienummer).
4. **Data** staat in `data/`, **geheimen** in `.env`. `data/` (de Excel-brondata), `.env`,
   `__pycache__/` en `.venv/` staan in `.gitignore`, met één uitzondering: `data/parquet/` (het
   verwerkte datamodel) staat wél in git, omdat de publieke Streamlit-app het nodig heeft. Na een
   wijziging aan `pipeline.py` of de data herbouw je de parquet (`python pipeline.py`) en commit je
   die opnieuw.
5. **Omgeving**: de conda-omgeving `syntra-ds` is de standaard. Zolang de packages uit
   `requirements.txt` daarin staan, mag je ze gebruiken. Maak geen eigen `.venv`.
6. **Git**: de map is al een repo; geen `git init`. Yun doet de commits zelf, met een eigen
   boodschap. Commit nooit. Meld wanneer een stap werkt, zodat Yun kan committen.
7. **Windows** is het standaardbesturingssysteem (PowerShell, `C:\Users\<jij>\...`).
8. **Beslissingslogboek**: noteer elke beslissing van Yun in `beslissingslogboek.md`
   (vraag, antwoord, reden). Achtergrond bij beslissingen en aannames staat daar; lees het bij
   vragen over waarom iets zo gekozen is.

## Definities (ongevallendata)

- Een rij is een ongeval. De dataset bevat enkel ongevallen met minstens één dode of gewonde.
- **Fietsongeval**: `CD_ROAD_USR_TYPE1` of `CD_ROAD_USR_TYPE2` is `03` ("Fiets"). Elk ongeval
  telt één keer, ook als beide partijen een fiets zijn. Bromfiets (06) en motorfiets (07) tellen
  niet mee: ze hebben andere snelheden en wegen. De data maakt geen onderscheid tussen een gewone
  fiets en een e-bike.
- **Ernstig ongeval**: `CD_CLASS_ACCIDENTS` is "Met doden", "dodelijk gewonden" of
  "met zwaargewonden" (codes 1, 2, 3).
- **Fietsongevallengraad**: fietsongevallen per 100.000 inwoners, met de bevolking van
  hetzelfde jaar.
- **Aandeel fietsongevallen**: % fietsongevallen van alle ongevallen (standaard zonder
  autosnelweg, via het filter Wegtype).
- **Aandeel ernstig (fiets)**: % ernstige ongevallen van alle fietsongevallen.
- Er worden nooit rijen verwijderd. Onbekend wegtype (`CD_ROAD_TYPE` = 9) en de autosnelweg
  blijven in de data (`Fact_Accidents`).
- **Autosnelweg** (`CD_ROAD_TYPE` = 1) staat **standaard uit** in het filter Wegtype, omdat
  fietsers daar niet mogen rijden en ze het aandeel fietsongevallen zouden verlagen. De gebruiker
  kan ze aanzetten om met en zonder autosnelweg te vergelijken. De app toont bovenaan altijd of
  de autosnelweg wel of niet meegerekend is.

## Opschonen (ongevallendata)

- Brussel krijgt "Brussels Hoofdstedelijk Gewest" als provincie.
- Rijen zonder coördinaten blijven in de analyse.
- De 66 volledig identieke rijen blijven staan.
- Alle kolommen die met `CD_` beginnen zijn ID-kolommen en blijven tekst; `CD_NIS` ook
  (voorloopnullen blijven behouden).
- Alle kolommen die op `_FR` eindigen worden verwijderd.

## App

- De taal van de app is Nederlands, met Belgische getalnotatie (86.300; 13,0 %).
- Bovenaan staan de belangrijkste cijfers als kaarten.
- **Filters** staan in de zijbalk (meerkeuze) en gelden voor alle visuals. Geen keuze = alles.
  De filters zijn: Jaar; Gewest > Provincie > Gemeente; Weer; Wegdek; Licht; Kruispunt; Wegtype;
  Ernst; Hindernis; Weggebruiker. Enige uitzondering op "standaard = alles": bij Wegtype staat
  de autosnelweg standaard uit (de andere drie wegtypes zijn geselecteerd). Een lege keuze bij
  Wegtype betekent alle wegtypes, dus mét autosnelweg.
- **Trapsgewijs:** Gewest beperkt de keuzes bij Provincie, en Provincie beperkt de keuzes bij
  Gemeente. Wijzig je Gewest of Provincie, dan gaan de filters eronder terug op "Alles".
- **Weggebruiker:** een ongeval telt mee als Road User Type1 OF Road User Type2 geselecteerd is.
- Een filter toont enkel waarden die in `Fact_Accidents` voorkomen.
- De filterlogica en de berekeningen staan in `pipeline.py`, niet in `app.py`.

## Datamodel

- Het datamodel bestaat uit `Dim_*`-tabellen, `Fact_Accidents` en `Fact_Population`.
  Tabel- en kolomnamen volgen de lijst in `beslissingslogboek.md` (beslissing 13 tot 15).
- Labels in de dimensietabellen beginnen met een hoofdletter (gold layer: schone, analyseklare
  tabellen). Enkel de eerste letter verandert.
- **Coördinaten**: lege waarden en punten buiten België tellen als "geen coördinaten". Die rijen
  blijven in de analyse. De bron-coördinaten zijn Belgisch Lambert 72 (EPSG:31370) en worden
  met `pyproj` omgezet naar WGS84 (Latitude en Longitude).
- **Nulwaarden**: een gemeente zonder ongevallen in een jaar krijgt 0 ongevallen, niet
  "ontbrekend".
- **`Gemeente_Jaar`** (bevolking en tellingen per gemeente en jaar) wordt niet opgeslagen, maar per
  selectie berekend (`maak_gemeente_jaar`), zodat de tellingen alle filters volgen, ook Wegtype.
- **Gemeentenamen** in de app komen uit `Dim_NIS` (ongevallenbestand).
- De app heeft een eigen tabblad **"Datakwaliteit"** (het laatste tabblad, geen sectie onder de
  andere tabbladen) met de controle van de bevolking per jaar en de NIS-codes (per jaar) die maar
  in één van de twee bestanden voorkomen. Het gaat over de volledige data en volgt de filters niet.

## Visuals

- Grafieken met `plotly`, onder tabbladen: Trend, Kaart, Waar, Wanneer, Omstandigheden,
  Tegenpartij. De filters blijven in de zijbalk. Geen dubbele as: één maat per grafiek.
- Onder elke grafiek of tabel staat één zin over de maat. De fietsongevallengraad is per inwoner
  en niet per gefietste kilometer (daar zijn geen gegevens over); een ongeval is geen slachtoffer.
- **Trend per gemeente/provincie**: helling van de rechte lijn door de jaarlijkse
  fietsongevallengraad, in % van het gemiddelde per jaar. Boven +2 % per jaar = stijgend, onder
  −2 % = dalend, ertussen stabiel; met sparkline. Bij minder dan 4 gekozen jaren: "–".
- **Minimum 30 fietsongevallen** (over de gekozen jaren samen) voor rangschikkingen op een
  verhouding (graad, aandelen, trend). De gebruiker kan het minimum aanpassen. Bij sorteren op
  aantal geldt geen drempel. Gemeenten eronder staan er wel, gemarkeerd "te weinig data".
- **Weer**: categorieën onder 1 % worden "Overige"; "Onbekend" blijft apart.
- **Kaart**: standaard enkel fietsongevallen, met schakelaar naar alle ongevallen. Standaard een
  concentratiekaart; afzonderlijke punten zijn begrensd tot 20.000, met melding. Geen
  gemeentegrenzenkaart.
- **Heatmap**: enkel de top 20 gemeenten, volgens de sortering in "Waar".
- Bij 2020–2021 staat in tijdreeksen een arcering "corona".
- **Wat een zin of titel mag beweren:** een fietsongeval is geen slachtoffer. De graad is per
  inwoner en zegt niets over "gevaarlijker", want er zijn geen gegevens over gefietste kilometers.
  Een stijging of daling nooit als "gevaarlijker/veiliger" duiden zonder dat voorbehoud.
- **Tijdreeks per jaar:** drie aparte grafieken (graad, aandeel fietsongevallen, aandeel ernstig),
  nooit samen op één as.
- **Aantal per maand:** één lijn per jaar in blauwtinten (oudste jaar het lichtst); de legende
  staat omgekeerd (recentste jaar bovenaan). Een geordende reeks krijgt één kleur in oplopende
  tint, geen acht verschillende kleuren.
- **Kleuren:** categorische kleuren worden gecontroleerd met de validator van de dataviz-skill.
  Slaagt die niet, dan komt er een tweede aanduiding bij (symbool, label of tabel).
- **Kaart:** de maatzin zegt hoeveel % van de ongevallen op de kaart staat; een tabel toont het %
  zonder coördinaten per provincie en jaar; een waarschuwing verschijnt als de gekozen jaren over
  2022 lopen.
- **Vergelijking per niveau (tabblad Waar):** keuze Gewest, Provincie of Gemeente; titels en
  maatzinnen volgen de keuze. Bovenaan staat de ranglijst. "Toon de top N gemeenten volgens" (met
  volgorde, aantal en minimum) bestaat enkel bij Gemeente; bij Gewest en Provincie staat alles in de
  tabel, op aantal fietsongevallen. Daaronder: het aandeel van de bevolking tegenover het aandeel
  van de fietsongevallen, en een bolgrafiek (x = inwoners, y = fietsongevallen per 100.000 inwoners,
  grootte = fietsongevallen) met de eenheid met de meeste fietsongevallen als referentie. Bij
  Gemeente enkel de top 20 op aantal fietsongevallen, met aandelen berekend over alle gemeenten.
- **Ranglijst:** de graad heeft een ruwe 95 %-marge, en onder de tabel staat een melding als de marge
  van nummer 1 overlapt met andere in de lijst. Het minimum van 30 fietsongevallen geldt enkel bij
  een verhouding (graad, aandelen, trend); bij sorteren op een aantal staat bij kleine eenheden
  "te weinig data" in de verhoudingskolommen. Geen losse tabellen met "cijfers" of "opsplitsing"
  naast de grafieken: die gaven geen extra inzicht.
- **Maatzinnen:** concreet en eenvoudig, met één voorbeeld met echte cijfers; geen herhaalde,
  bijna gelijke zinnen per eenheid.
