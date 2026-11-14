# Beslissingslogboek

Per beslissing: de vraag, het antwoord en de reden. Redenen die Yun niet zelf gaf, staan als
"geen reden opgegeven" zodat er niets bijverzonnen wordt.

## 2026-11-14: Ongevallen (`OPENDATA_MAP_2017-2024.xlsx`)

Context: één blad met alle jaren. Enkel ongevallen met minstens één dode of gewonde (ongevallen
zonder slachtoffers zitten niet in de dataset). Extra bron: `data/Variabelenlijst.pdf`.

### 1. Wat is een rij, en wat is "ernstig"?
- **Antwoord:** een rij is een ongeval. Ernstig = `CD_CLASS_ACCIDENTS` is "Met doden",
  "dodelijk gewonden" of "met zwaargewonden" (codes 1, 2, 3).
- **Reden:** de definities staan in de tabel hieronder en in `Variabelenlijst.pdf`.

| Begrip | Definitie |
|---|---|
| Fietsongeval | Road User Type1 of Road User Type2 is "Fiets" |
| Ernstig ongeval | Class Accidents is "Met doden", "dodelijk gewonden" of "met zwaargewonden" |
| Fietsongevallengraad | Fietsongevallen per 100.000 inwoners (bevolking van hetzelfde jaar) |
| Aandeel fietsongevallen | % fietsongevallen van alle ongevallen (zonder autosnelweg) |
| Aandeel ernstig (fiets) | % ernstige ongevallen van alle fietsongevallen |

### 2. Hoe definiëren we een fietsongeval, en wat sluiten we uit?
- **Antwoord:** een fietsongeval heeft "Fiets" bij `ROAD_USR_TYPE1` of `ROAD_USR_TYPE2`. Elk
  ongeval telt één keer, ook als beide partijen een fiets zijn. `Autosnelweg` (road type 1)
  wordt uitgesloten voor de hele analyse. Dit wordt bovenaan in de app vermeld.
- **Reden:** fietsers mogen niet op de autosnelweg. Die ongevallen zouden het aandeel
  fietsongevallen in gemeenten met een autosnelweg verlagen.

### 3. Hoe gaan we om met Brussel, dat geen provincie heeft?
- **Antwoord:** vul "Brussels Hoofdstedelijk Gewest" in als provincie voor Brussel.
- **Reden:** geen reden opgegeven.

### 4. Rijen zonder coördinaten, en hoe tonen we de kaart?
- **Antwoord:** rijen met ontbrekende coördinaten blijven in de analyse.
  - Kaart: toon eerst waar de ongevallen geconcentreerd zijn (donkerder = meer ongevallen),
    met een optie om de afzonderlijke ongevallen als punten te tonen.
  - Onder de kaart, voor de gekozen jaren, een zin zoals: "Deze kaart toont 86.300 van de
    100.000 ongevallen; 12.900 (13,0 %) hebben geen coördinaten en worden niet getoond op
    deze kaart."
  - Een kleine tabel met het % ongevallen zonder coördinaten per jaar en per provincie
    (provincies als rijen, jaren als kolommen, plus een totaalrij en totaalkolom), berekend
    uit de data en aangepast aan de filters in de zijbalk.
- **Reden:** het gaat om heel veel ongevallen, dus eerst de concentratie tonen. Het is ook
  duidelijk hoeveel ongevallen niet op de kaart staan. Voor de telling van ongevallen per
  gemeente, provincie en gewest zijn de coördinaten niet nodig.

### 5. De 66 volledig identieke rijen
- **Antwoord:** houden, geen wijziging.
- **Reden:** geen reden opgegeven.

### 6. Datatypes van `CD_`-kolommen en NIS
- **Antwoord:** alle kolommen die met `CD_` beginnen zijn ID-kolommen en blijven tekst
  (`str`). `CD_NIS` blijft ook tekst, want codes kunnen met een nul beginnen (bv. "09").
- **Reden:** het zijn codes, geen hoeveelheden. Rekenen ermee heeft geen zin en voorloopnullen
  mogen niet verdwijnen.

### 7. Welke kolommen verwijderen we?
- **Antwoord:** alle kolommen die op `_FR` eindigen gaan weg. De NL-kolommen blijven.
- **Reden:** geen reden opgegeven.

## 2026-11-14: Bevolking (`Bevolking_per_gemeente_2017-2024.xlsx`)

### 8. Hoe lezen we de bladen in?
- **Antwoord:** één blad per jaar ("Bevolking in 2017" … "Bevolking in 2024"); het jaar komt uit
  de bladnaam. De lege rijen 2 en 3 vallen weg. De kolommen Mannen en Vrouwen vallen weg.
  NIS blijft tekst. Behouden en hernoemen naar tabel `Fact_Population`:
  `NIS code` → `NIS`, `Woonplaats` → `Municipality`, `Totaal` → `Total`, bladnaam → `Year`.
- **Reden:** geen reden opgegeven.

### 9. De bladen mengen alle niveaus. Wat doen we?
- **Antwoord:** verwijder per blad "België", "Vlaams Gewest", "Waals Gewest",
  "Brussels Hoofdstedelijk Gewest" en elke rij die "Provincie" of "Arrondissement" bevat.
  Controle per jaar: de som van `Total` van de overblijvende rijen moet gelijk zijn aan `Total`
  van de rij "België". Toon de controle per jaar; stop en meld het als ze mislukt. Voeg daarna
  alle jaren samen in één tabel `Fact_Population`.
- **Reden:** anders tel je een inwoner meerdere keren mee (gemeente, arrondissement, provincie,
  gewest, land).

### 10. Hoe lossen we de NIS-codes van 2017 en 2018 op?
- **Antwoord:** NIS moet tekst zijn in beide bronnen (kan met 0 beginnen). Voor 2017 en 2018
  koppelen we oude codes aan nieuwe via de lijst van Yun: 7 fusies (15 → 7 gemeenten in
  Vlaanderen) en 11 Waalse gemeenten die enkel een nieuwe code kregen. Bij een fusie worden de
  inwoners opgeteld.
- **Reden:** de gemeentefusies van 1 januari 2019. De ongevallendata gebruikt overal de nieuwe
  codes, de bevolkingsbladen van 2017 en 2018 de oude.
- **Controle:** zie de resultaten van deze stap in de sessie: alle controles slagen, 581
  gemeenten per jaar, geen enkele code ontbreekt in 2017 en 2018.
- **Aanname van Claude:** de naam van een gefuseerde gemeente komt uit 2019, de naam bij de
  nieuwe code. De naam hoort bij de code en niet bij de oude gemeenten.

### 11. Wat doen we met `CD_ROAD_TYPE` 9 (onbekend, 1.502 rijen)?
- **Antwoord:** onbekend wegtype blijft in de data. We verwijderen geen rijen. Enkel
  Autosnelweg is uitgesloten.
- **Reden:** 1.502 rijen zijn veel, en er zitten ongevallen met een fiets of voetganger bij. Er is
  geen reden om ze uit te sluiten.
- **Controle door Claude:** de 1.502 ongevallen zijn 0,56% van `Fact_Accidents`. Daarvan hebben er
  301 een fiets (0,42% van alle fietsongevallen), 123 een voetganger en 402 een fiets of een
  voetganger. Per jaar: 379, 337, 159, 141, 106, 125, 126 en 129 (2017 tot 2024); 2017 en 2018
  liggen dus duidelijk hoger dan de latere jaren.

### 12. Mag `openpyxl` in `requirements.txt`?
- **Antwoord:** ja. Alle packages die in `syntra-ds` staan, mag Claude toevoegen aan
  `requirements.txt` als ze nodig zijn. Staan ze niet in `syntra-ds`, dan mag het niet.
- **Reden:** `syntra-ds` is de standaardomgeving; wat daarin staat, is al goedgekeurd.
- **Uitvoering:** `openpyxl==3.1.5` toegevoegd (versie gecontroleerd in `syntra-ds`).
  Pandas heeft het nodig om `.xlsx` te lezen.

## 2026-11-14: Datamodel (dimensies, feiten en koppeling)

### 13. Welke dimensietabellen maken we?
- **Antwoord:** unieke rijen (ID + label, hernoemd) voor `Dim_NIS` (NIS, Region, Province,
  Municipality), `Dim_Crossway`, `Dim_Weather`, `Dim_Road_Condition`, `Dim_Light_Condition`,
  `Dim_Road_Type`, `Dim_Class_Accidents` en `Dim_Obstacles`. `Dim_Road_User` is één gedeelde
  dimensie voor `CD_ROAD_USR_TYPE1` en `TYPE2` samen. Controleer dat elke code in beide kolommen
  hetzelfde label heeft en meld elk conflict.
- **Reden:** geen reden opgegeven.
- **Resultaat:** geen enkel conflict. Alle dimensies hebben één label per ID. `Dim_Road_User` heeft
  12 rijen; codes 10 en 11 komen enkel in `TYPE2` voor en zijn geen weggebruikers ("één
  bestuurder, geen hindernis" en "een weggebruiker tegen een hindernis").

### 14. Hoe ziet `Fact_Accidents` eruit?
- **Antwoord:** 15 kolommen: Year, Month, Hour, NIS, Latitude, Longitude, Weather ID,
  Road Condition ID, Light Condition ID, Crossway ID, Road Type ID, Class Accidents ID,
  Obstacle ID, Road User Type1 ID en Road User Type2 ID, met verwijzingen naar de dimensies.
- **Reden:** geen reden opgegeven.
- **Resultaat:** elk ID in de fact bestaat in zijn dimensie (0 ontbrekende verwijzingen).

### 15. Coördinaten
- **Antwoord:** zet `MS_X_COORD` en `MS_Y_COORD` om naar Latitude en Longitude. Lege waarden en
  punten buiten België tellen als "geen coördinaten".
- **Reden:** de kaart heeft lat/lon nodig.
- **Aanname van Claude:** het stelsel van de bron is Belgisch Lambert 72 (EPSG:31370). Dat staat
  niet in `Variabelenlijst.pdf`. Ik controleerde het: Antwerpen, Genk, Luik en Aarlen landen op de
  juiste plek. "Binnen België" = omhullende rechthoek lat 49,49 tot 51,51 en lon 2,54 tot 6,41; dat
  is geen exacte landsgrens.
- **Resultaat:** 2 rijen hadden onmogelijke waarden (~10^16) en tellen als "geen coördinaten".
  `pyproj` is nodig voor de omzetting.
- **Bevestigd door Yun:** die 2 rijen vallen onder "geen coördinaten". Ze blijven in de analyse.

### 16. Hoe koppelen we bevolking en ongevallen?
- **Antwoord:** koppel op NIS + Year. Meld NIS-codes (per jaar) die in één bestand voorkomen en niet
  in het andere, in een sectie "Datakwaliteit". Een gemeente met nul ongevallen in een jaar krijgt 0
  (niet "ontbrekend"). Gebruik in de app de gemeentenamen uit `Dim_NIS`.
- **Reden:** geen reden opgegeven.
- **Resultaat:** 0 codes alleen in de ongevallen. 14 combinaties van gemeente en jaar staan enkel
  in de bevolking (bv. Herstappe, Mesen): die gemeenten hadden dat jaar geen ongevallen.

### 17. Wat telt als "fiets", en hoe schrijven we de labels van Dim_Road_User?
- **Antwoord:** enkel Road User Type ID `03` ("Fiets") telt als fiets. Labels in `Dim_Road_User`
  beginnen met een hoofdletter (bv. "personenauto" wordt "Personenauto").
- **Reden:** de data maakt geen onderscheid tussen een gewone fiets en een e-bike. Bromfiets en
  motorfiets hebben andere snelheden en andere wegen en zouden de resultaten over fietsveiligheid
  vertekenen.
- **Uitvoering:** `pipeline.py` gebruikt nu ID `03` (niet langer het label) en gooit een fout als dat
  ID niet "Fiets" heet. Alleen de eerste letter wordt een hoofdletter; de rest blijft zoals het is.
  Het aantal fietsongevallen is ongewijzigd: 71.749 (7.829 ernstig).
- **Vervangt** de aanname hieronder dat "Fiets" via het label gezocht wordt.

### 18. Fietsers op de autosnelweg: 132 ongevallen
- **Antwoord:** akkoord dat deze ongevallen uitgesloten blijven. Het lijken fouten in de registratie.
- **Reden:** fietsers mogen niet op de autosnelweg. In 27 van de 132 ongevallen zijn beide partijen
  "Fiets", wat daar onmogelijk is.
- **Controle door Claude:** 132 ongevallen op de autosnelweg hebben minstens één fiets: 55 enkel
  bij TYPE1, 50 enkel bij TYPE2 en 27 bij beide. De 27 bestaan uit 1 "dodelijk gewonden",
  3 "met zwaargewonden" en 23 "met lichtgewonden". Per jaar: 13, 11, 17, 10, 9, 27, 19 en 26
  (2017 tot 2024). Totaal fietsongevallen over alle wegtypes: 71.881; zonder autosnelweg: 71.749.

### 19. Parquet voor snel laden, en in git
- **Antwoord:** het verwerkte datamodel wordt als parquet opgeslagen en mag in git en op GitHub
  staan.
- **Reden:** de opdracht vraagt een GitHub-repo en een werkende, publieke Streamlit-URL, dus de app
  draait op Streamlit Community Cloud. Daar zijn de Excel-bestanden (58 MB, `data/` staat in
  `.gitignore`) er niet. De brondata is open data.
- **Uitvoering:** de parquet staat in `data/parquet/` (15 bestanden, samen 5,2 MB). `.gitignore` houdt
  de rest van `data/` buiten git (`data/*`, behalve `!data/parquet/`). `pyarrow==24.0.0` toegevoegd
  (staat in `syntra-ds`; Streamlit heeft het zelf ook nodig). Alle pins bestaan ook op PyPI,
  nodig voor Cloud. `pipeline.py` heeft nu `schrijf_parquet`, `lees_parquet`, `parquet_is_actueel`
  en `laad_of_bouw_datamodel`; `python pipeline.py` herbouwt de parquet.
- **Controle:** de tabellen en controles uit parquet zijn identiek aan die uit Excel (waarden en
  types). Inladen duurt 0,2 s in plaats van ongeveer 94 s. Een kopie van de app zonder Excel draait
  zonder fouten met dezelfde cijfers.
- **Aanname van Claude:** is de parquet ouder dan de Excel-bestanden of `pipeline.py`, dan herbouwt
  de app ze automatisch (alleen als de Excel-bestanden er zijn). Zo werk je nooit met verouderde
  data na een aanpassing. Na zo'n herbouw moet je de gewijzigde parquet opnieuw committen.

### 20. Tests voor de opdracht
- **Antwoord:** tests worden overgeslagen. 
- **Reden:** Yun heeft tests niet geleerd in de opleiding. De opdracht noemt tests wel bij de
  GitHub-repo; dat verschil blijft dus bestaan.

### Aannames van Claude bij deze stap (nog niet bevestigd door Yun)
- **Autosnelweg:** de rijen verdwijnen in `Fact_Accidents` (21.860 van 289.532). De dimensies
  worden gebouwd vóór die uitsluiting, dus `Dim_Road_Type` bevat nog "Autosnelweg" en `Dim_NIS`
  heeft alle 581 gemeenten.
- **Codes blijven tekst zoals in de bron.** De weggebruikerscodes zijn `'01'` … `'09'`, `'10'`,
  `'11'`, `'99'` (voorloopnul). (Fiets: zie beslissing 17.)
- **`Gemeente_Jaar`:** één extra tabel (bevolking + tellingen) met Municipality, Province en Region
  uit `Dim_NIS`, Total, Accidents, Bike_Accidents en Serious_Bike_Accidents. De drie tellingen
  volgen uit de definities in `CLAUDE.md`. **Bevestigd door Yun:** de tabel toont duidelijk wat
  nodig is en blijft. De ongebruikte stubs `voeg_regio_toe` en `tel_per_regio` zijn weg.
- **`Hour` = 99** (3 rijen) blijft staan, want we verwijderen geen rijen.
- **De 138 punten > 50 km van hun eigen gemeente** (op basis van de coördinaten) blijven staan en
  tellen mee op de kaart. Ze liggen wel binnen België.
