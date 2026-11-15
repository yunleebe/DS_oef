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
- **Gewijzigd door beslissing 22:** de autosnelweg wordt niet meer uit de data gehaald. Ze staat
  standaard uit in het filter Wegtype en kan aangezet worden.

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
  Autosnelweg is uitgesloten. (Sinds beslissing 22 verwijderen we helemaal geen rijen meer.)
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

### 21. Opbouw van de app: kaarten en filters
- **Antwoord:** bovenaan de belangrijke cijfers als kaarten (card visuals). Filters in de zijbalk,
  meerkeuze, standaard alles, toegepast op alle visuals: Year; Region > Province > Municipality
  (trapsgewijs: Region beperkt Province, Province beperkt Municipality); Weather; Road Condition;
  Light Condition; Crossway; Road Type; Class Accidents; Obstacles; Road User Type (een ongeval telt
  mee als Road User Type1 OF Road User Type2 geselecteerd is). Taal: Nederlands. Getalnotatie:
  Belgisch (86.300; 13,0 %).
- **Reden:** geen reden opgegeven.
- **Uitvoering:** de filterlogica staat in `pipeline.py` (`filter_opties`, `filter_ongevallen`,
  `bereken_kerncijfers`, zonder Streamlit), de zijbalk en kaarten in `app.py`.
- **Controle:** de filters en kaarten zijn getest tegen onafhankelijke berekeningen met pandas
  (zonder filters, per jaar, per gewest/provincie/gemeente, weggebruiker TYPE1 OF TYPE2,
  combinaties van filters, lege selectie, trapsgewijs gedrag) en in de app zelf, waarbij de zijbalk
  bediend werd zoals een gebruiker. Alles klopte.

### 22. Autosnelweg in de data houden, standaard uit in het filter Wegtype
- **Antwoord:** optie A. De autosnelweg blijft in `Fact_Accidents` en het filter Wegtype heeft ze als
  optie, maar standaard uitgezet. Zo kan de gebruiker de kaarten met en zonder autosnelweg
  vergelijken. Het filter Wegtype is een uitzondering op "standaard = alles"; de standaard blijft
  zichtbaar ("Autosnelweg staat standaard uit"). `Gemeente_Jaar` wordt aangepast: als de autosnelweg
  uit het filter staat, toont `Gemeente_Jaar` de juiste data.
- **Reden:** de cijfers die de autosnelweg betreffen, veranderen enkel bij de kaarten waar het
  totaal aantal ongevallen in zit. Door het in de slicer te zetten ziet de gebruiker zelf het effect,
  in plaats van dat het verborgen zit in de pipeline.
- **Het effect op de kaarten (zonder filters), berekend uit de ruwe data:**

| Kaart | Zonder autosnelweg (standaard) | Met autosnelweg |
|---|---|---|
| Ongevallen | 267.672 | 289.532 |
| Fietsongevallen | 71.749 | 71.881 |
| Ernstige fietsongevallen | 7.829 | 7.852 |
| Aandeel fietsongevallen | 26,8 % | 24,8 % |
| Aandeel ernstig (fiets) | 10,9 % | 10,9 % |
| Fietsongevallen per 100.000 inwoners | 77,8 | 78,0 |

- **Uitvoering:** `sluit_autosnelweg_uit` is weg. `pipeline.py` heeft nu `STANDAARD_UIT`,
  `standaard_selectie` en `aantal_autosnelweg`, en `maak_gemeente_jaar` berekent `Gemeente_Jaar` per
  selectie. `Gemeente_Jaar` staat dus niet meer in de parquet. In de app toont een banner of de
  autosnelweg meegerekend is: een infoblok bij de standaard, een waarschuwing zodra ze meetelt.
  `CLAUDE.md` is aangepast. De parquet is herbouwd (Fact_Accidents: 289.532 rijen).
- **Controle:** de standaardselectie geeft exact dezelfde cijfers als voorheen. Met autosnelweg
  (lege keuze of alle vier geselecteerd) kloppen alle kaarten met de ruwe data. Voor `Gemeente_Jaar`
  klopt elke combinatie van gemeente en jaar met een onafhankelijke pandas-telling, met en zonder
  autosnelweg, per jaar en per gewest. In de app zelf kloppen de kaarten bij elke wijziging.
- **Aannames van Claude:**
  - Een lege keuze bij Wegtype betekent alle wegtypes, dus mét autosnelweg. De banner waarschuwt dan.
    **Bevestigd door Yun:** de standaard is Gemeenteweg, Gewestweg en onbekend. De keuze mag leeg
    zijn als de gebruiker zelf alles uitvinkt.
  - `Dim_Road_Type` en `Dim_NIS` zijn onveranderd (alle 581 gemeenten, alle 4 wegtypes).
  - Datakwaliteit blijft over de volledige data gaan, nu inclusief de autosnelweg. Het aantal
    gemeente-jaren zonder ongevallen blijft 14, ook met de autosnelweg erbij.
  - `Gemeente_Jaar` toont enkel de gemeenten en jaren van de selectie (Jaar, Gewest, Provincie,
    Gemeente). Een gemeente zonder ongevallen in de selectie krijgt 0.

### 23. Labels in alle dimensies beginnen met een hoofdletter
- **Antwoord:** ja, alle labels in de dimensietabellen krijgen een hoofdletter (niet alleen
  Road User Type, zoals in beslissing 17).
- **Reden:** zo maken we de gold layer (de laag met schone, analyseklare tabellen).
- **Uitvoering:** `pipeline.py` zet de eerste letter van elk label om (`_met_hoofdletter`); de rest
  blijft zoals het is. Dat veranderde precies vijf labels: "Dodelijk gewonden", "Met zwaargewonden"
  en "Met lichtgewonden" bij Class Accidents, en "Onbekend" bij Crossway en bij Road Type. Alle
  andere labels begonnen al met een hoofdletter. ID's, `Fact_Accidents` en `Fact_Population` zijn
  onveranderd (vergeleken met de vorige parquet). De ernstklassen worden zonder rekening te houden
  met hoofdletters herkend, dus de kaarten veranderen niet (opnieuw getest).

### 24. Opbouw van de visuals (tabbladen, trend, kaart, ranglijsten)
- **Vraag:** hoe tonen we de centrale vraag (talrijkst, ernstigst, veranderd sinds 2017)?
- **Antwoord:** zes tabbladen: Trend, Kaart, Waar, Wanneer, Omstandigheden, Tegenpartij. Filters
  blijven in de zijbalk. Grafieken met `plotly==6.9.0` (staat in `syntra-ds`).
- **Trend (onderdeel 0):** twee aparte lijngrafieken (fietsongevallengraad en aandeel
  fietsongevallen), geen dubbele as. 2020–2021 is gearceerd als corona.
- **Trend per gemeente/provincie:** helling van de rechte lijn door de jaarlijkse
  fietsongevallengraad, uitgedrukt in % van het gemiddelde per jaar. Boven +2 % per jaar =
  stijgend, onder −2 % = dalend, ertussen stabiel; met sparkline. Reden: de eerdere vergelijking
  2017–19 met 2022–24 was te moeilijk uit te leggen.
- **Minimum 30 fietsongevallen** (over de gekozen jaren samen) voor rangschikkingen op een
  verhouding (graad, aandelen, trend). Een invoervak laat de gebruiker het aanpassen. Bij
  sorteren op aantal geldt geen drempel.
- **Weer:** categorieën onder 1 % worden "Overige"; "Onbekend" blijft apart.
- **Kaart:** standaard enkel fietsongevallen, met schakelaar naar alle ongevallen. Standaard een
  concentratiekaart; afzonderlijke punten zijn begrensd tot 20.000 (met melding). Geen
  gemeentegrenzenkaart (mogelijk later).
- **Heatmap:** enkel de top 20 gemeenten, volgens de sortering in "Waar".
- **Bij elke grafiek** staat één zin over de maat. De fietsongevallengraad is per inwoner; er zijn
  geen gegevens over hoeveel er gefietst wordt.
- **Maandgrafiek (Trend):** fietsongevallen per maand, één lijn per jaar (`maak_maandtelling`).
  Yun vergeleek twee versies: een eigen palet van acht kleuren (met symbolen) en blauwtinten.
  Ze koos de **blauwtinten**, omdat die goed tonen dat er in recente jaren meer fietsongevallen
  zijn. Het oudste jaar is het lichtst, het recentste het donkerst. De legende staat omgekeerd
  (recentste jaar bovenaan), zodat jaar en lijn beter te koppelen zijn. De validator keurde het
  eigen palet niet volledig goed (grijzige kleuren, twee kleuren die voor rood-groen-
  kleurenblinden lijken op elkaar). Dat speelde mee, al koos Yun om de duidelijkheid.
- **Kaart gebouwd (stap 2):** twee keuzes boven de kaart: *Fietsongevallen | Alle ongevallen*
  (standaard fiets) en *Concentratie | Afzonderlijke punten* (standaard concentratie). De
  concentratiekaart telt ongevallen samen per vakje van ± 1 km (`maak_kaartdata`); de punten zijn
  een vaste steekproef van maximaal 20.000 (`maak_kaartpunten`), met melding. De zin onder de kaart
  zegt hoeveel van de ongevallen op de kaart staan. Een uitklapbare tabel toont het % zonder
  coördinaten per provincie en jaar, en een waarschuwing verschijnt als de gekozen jaren over 2022
  lopen (vanaf 2022 ontbreken veel minder coördinaten: totaal 14,7 % in 2017, 4,1 % in 2022).
- **Gewesten vergeleken (tabblad Waar, eerste deel):** Yun merkte dat Wallonië minder
  fietsongevallen heeft maar ook minder inwoners, en wilde weten hoeveel van het verschil daardoor
  komt. Twee grafieken: (1) aandeel van de bevolking naast aandeel van de fietsongevallen per
  gewest; (2) het verschil met het gewest met de meeste fietsongevallen (vast, geen keuzelijst),
  opgesplitst in "door minder inwoners" en "door minder ongevallen per inwoner"
  (`ontleed_verschil`), als balken die samen 100 % zijn. Yun vond de eerste versie (gestapelde
  aantallen, een keuzelijst en bijna gelijke zinnen per gewest) onduidelijk; nu staat er één
  voorbeeldzin in de maatzin en een tabel met de cijfers.
  Methode: gemiddelde van beide volgordes, zodat de uitkomst niet afhangt van het vertrekpunt; de
  twee delen tellen exact op tot het verschil. Resultaat (standaard): Wallonië heeft 53.907
  fietsongevallen minder dan Vlaanderen, waarvan 29 % door het kleinere aantal inwoners en 71 %
  door minder ongevallen per inwoner; bij Brussel is dat 73 % bevolking en 27 % graad.
- **Niveau-keuze in het tabblad Waar:** boven beide visuals staat een keuze *Gewest | Provincie |
  Gemeente*. Titels en maatzinnen veranderen mee. Bij Gemeente blijven enkel de 20 gemeenten met de
  meeste fietsongevallen over (anders is de grafiek veel te lang); de aandelen worden wel berekend
  over alle 581 gemeenten, en de tweede grafiek vergelijkt de andere 19 met de gemeente met de
  meeste fietsongevallen (Antwerpen). Eerst kregen eenheden waar de twee oorzaken in
  tegengestelde richting werken geen balk (bij de top 20 gemeenten 6 van de 19). Yun merkte dat
  Provincie Oost-Vlaanderen daardoor ontbrak, terwijl die de tweede is op aantal. Oost-Vlaanderen
  heeft minder inwoners dan Antwerpen (155 % van het verschil) maar méér fietsongevallen per
  inwoner (134,9 tegenover 125,5; −55 %). Nu staan alle eenheden in de grafiek: bij tegengestelde
  richting loopt het ene deel naar links van nul (negatief) en is het andere groter dan 100 %.
  Onder de grafiek staat een uitleg met een voorbeeld. De percentages blijven bescheiden (bij de
  top 20 gemeenten tussen −22 % en 122 %).
- **Tweede visual vervangen door een bolgrafiek:** Yun vond de balken met negatieve en
  100+ %-delen onduidelijk ("zo een grafiek heb ik nergens gezien"). Nu is elke eenheid een bol:
  links-rechts het gemiddeld aantal inwoners per jaar, boven-onder de fietsongevallen per 100.000
  inwoners, grootte = aantal fietsongevallen; stippellijnen tonen de eenheid met de meeste
  fietsongevallen. De opsplitsing in "door inwoners" en "door graad" stond eerst als tabel in een
  uitklapbaar blok, naast een blok "Cijfers per gewest/provincie/gemeente". Yun vond beide
  overbodig ("weinig inzicht"): de cijfers staan al in de ranglijst en de bolgrafiek. Beide blokken
  en de functie `ontleed_verschil` zijn verwijderd.
- **Is Knokke-Heist de gevaarlijkste gemeente? (vraag van Yun):** Knokke-Heist heeft de hoogste
  graad (232,9 per 100.000 inwoners; 614 fietsongevallen; Belgisch gemiddelde 77,8), maar "gevaarlijkst"
  volgt daar niet uit: (1) over de jaren wisselt de nummer 1 (Knokke-Heist alleen in 2024; rang 2–7 in
  de meeste jaren, 16 in 2023); (2) de 95 %-marge (214–251) overlapt met die van Eeklo (199–244);
  (3) de noemer is inwoners, geen fietsers of kilometers; (4) toeristen tellen mee in de ongevallen
  maar niet in de inwoners; (5) het aandeel ernstig (10,9 %) is gemiddeld, in Eeklo 15,0 %; (6) de
  registratie (enkel ongevallen met gewonden, verandering rond 2022, geen onderscheid e-bike).
- **Ranglijst in het tabblad Waar (`maak_ranglijst`):** volgt de keuze Gewest | Provincie | Gemeente.
  "Sorteer op": aantal fietsongevallen (standaard), aantal ernstige, graad per 100.000, aandeel
  fietsongevallen, aandeel ernstig, trend; hoogste of laagste eerst. Gemeente toont standaard 20
  (instelbaar). Het minimum van 30 fietsongevallen (aanpasbaar) geldt enkel bij sorteren op een
  verhouding; eenheden eronder doen dan niet mee (hoeveel staat onder de tabel), en bij sorteren op een
  aantal staat bij hen "te weinig data" in de verhoudingskolommen. De graad heeft een ruwe
  95 %-marge (aantal ± 1,96 × wortel van het aantal) en een melding wanneer de marge van nummer 1
  overlapt met andere in de lijst (nu: Knokke-Heist met 5 andere gemeenten). Trend = helling van de
  rechte lijn door de jaarlijkse graad in % van het gemiddelde (±2 % per jaar), met kolom
  "Graad per jaar" (sparkline); "–" bij minder dan 4 jaren. Gecontroleerd: 326 van 581 gemeenten
  halen 30, provincies 7 stijgend en 4 stabiel, top 20 gemeenten 6 stijgend, 13 stabiel, 1 dalend.
- **"Sorteer op" alleen bij Gemeente (keuze A van Yun):** Yun vroeg wat het voordeel was, want de
  maten staan al als kolom in de tabel. Antwoord: bij 581 gemeenten bepaalt de keuze *welke* 20 je
  ziet (top 20 op aantal is deels een andere lijst dan top 20 op graad) en of het minimum geldt;
  een klik op een kolomkop ordent alleen de getoonde rijen (en sorteert de tekstgetallen als tekst).
  Daarom blijft de keuze enkel bij Gemeente, met de naam "Toon de top 20 gemeenten volgens"
  (samen met volgorde, aantal en minimum). Bij Gewest en Provincie staat alles in de tabel, op
  aantal fietsongevallen, zonder keuzes.
- **Tabblad Wanneer (`maak_tijdverdeling`):** de data heeft enkel jaar, maand en uur (geen weekdag),
  dus het tabblad toont twee blokken: per uur van de dag en per maand. Telkens links het aantal
  fietsongevallen en rechts het aandeel ernstig, met het gemiddelde als stippellijn. Staven met minder
  dan 30 fietsongevallen zijn grijs, en de tooltip toont het aantal waarop het percentage steunt (zo
  zie je het 's nachts: 18–22 % ernstig, maar op 245–479 ongevallen per uur). Uur 99 (onbekend)
  komt bij fietsongevallen niet voor; de code vangt het toch op en meldt het. Gecontroleerd: de
  som over uren en maanden is 71.749 (ernstig 7.829); drukste uur 16 u (7.401), drukste maand juni
  (8.104). De maandgrafiek in Trend toont dezelfde maanden, maar per jaar.
- **Datakwaliteit als zevende tabblad:** de sectie stond onder de tabbladen en was dus op elk
  tabblad zichtbaar, terwijl ze over de volledige data gaat en de filters niet volgt. Yun vond dat
  verwarrend. Nu is het een eigen tabblad rechts van Tegenpartij, met dezelfde inhoud (ingelezen
  ongevallen, controle bevolking per jaar, NIS-codes in één bestand). Het tabblad blijft ook bij een
  lege selectie beschikbaar. `CLAUDE.md` is aangepast.
- **Volgorde van de balken:** van hoog naar laag op aantal fietsongevallen (grootste bovenaan).
  Een eerste versie stond omgekeerd, omdat plotly bij horizontale balken de eerste categorie al
  bovenaan zet en ik dat nog eens omkeerde.
- **Tabblad Omstandigheden (`maak_omstandigheid`):** vijf sub-tabbladen: Licht, Weer, Wegdek,
  Kruispunt, Wegtype. Elk heeft links het aantal fietsongevallen (met %) per categorie en rechts het
  aandeel ernstig met het gemiddelde (10,9 %) als stippellijn; staven met minder dan 30 fietsongevallen
  zijn grijs en de tooltip toont het aantal. Weer én Wegdek: categorieën onder 1 % worden
  "Overige" (de leden staan onder de grafiek); Wegdek erbij omdat het net als Weer veel gecombineerde
  categorieën heeft ("Droog+Proper"). Licht krijgt geen "Overige": "Nacht, geen openbare verlichting"
  is 0,98 % maar heeft 16,1 % ernstige ongevallen. "Onbekend" blijft overal apart. Opmerking: bij
  Weer (9,2 %), Wegdek (8,6 %) en Licht (2,9 %) is het aandeel ernstig bij "Onbekend" laag (6,2 %,
  5,7 % en 5,4 %); een mogelijke verklaring is dat lichtere ongevallen minder volledig ingevuld
  worden (niet in de data bevestigd). Kruispunt: 43,4 % op een kruispunt, 9,7 % ernstig; buiten een
  kruispunt 11,8 %. Gecontroleerd: alle vijf tellen op tot 71.749 (ernstig 7.829).
- **Tabblad Tegenpartij (`maak_tegenpartij`):** dezelfde twee grafieken als bij Omstandigheden
  (links aantal fietsongevallen met %, rechts aandeel ernstig met het gemiddelde als stippellijn, grijs
  onder 30). Regel: is Road User Type1 de fiets, dan is Type2 de tegenpartij, en omgekeerd; zijn beide
  een fiets, dan staat het ongeval onder "Fiets (twee fietsen)". "Eén bestuurder, geen hindernis" en
  "Een weggebruiker tegen een hindernis" zijn ongevallen zonder andere weggebruiker (eenzijdig); die
  labels komen uit Dim_Road_User. Standaard (71.749 fietsongevallen): personenauto 40.419 (56,3 %; 8,3 %
  ernstig), fiets 6.785 (9,5 %; 13,3 %), één bestuurder 6.270 (18,3 % ernstig), lichte vrachtauto
  4.223, hindernis 3.797 (17,1 %), voetganger 3.616 (10,6 %), bromfiets 2.406 (6,7 %), vrachtwagen
  1.358 (28,4 %). Onafhankelijk nagerekend voor fiets + personenauto. Het aandeel ernstig zegt niet
  wie de schuld heeft en houdt geen rekening met snelheid of massa. `toon_omstandigheid` wordt
  hergebruikt, met eigen zinnen voor de tegenpartij.
- **Zin over personenauto's geschrapt (Tegenpartij):** Yun liet de zin "een tegenpartij die vaak voorkomt
  (zoals een personenauto) zit ook in de meeste ongevallen, omdat er veel meer personenauto's dan
  vrachtwagens rondrijden" verwijderen. Reden: de data bevat geen verkeersintensiteit, dus de
  "omdat"-uitleg kan de app niet staven, en de vaste tekst volgde de filters niet.
- **Filter Jaar aflopend:** Yun wil in de zijbalk eerst de recente jaren zien (2024 bovenaan). Reden:
  de recentste jaren zijn meestal het meest relevant. Enkel de volgorde van de keuzelijst verandert
  (`filter_opties`); de gekozen jaren worden alleen met `isin` gebruikt, dus de cijfers blijven gelijk.
- **Maatzinnen groter (optie 1):** Yun vond de tekst onder de grafieken te klein. `st.caption` is
  standaard ± 14 px en lichtgrijs. Eén CSS-regel in `app.py` maakt alle captions 16 px, met de
  tekstkleur van het thema en 85 % dekking (leesbaarder, maar nog steeds duidelijk secundair). Dat
  geldt ook voor de caption in de zijbalk. Gekozen boven een aparte `maatzin()`-helper (enkel de
  maatzinnen), omdat alle uitleg onder de visuals even belangrijk is.
- **Tabel "zonder coördinaten" standaard open (tabblad Kaart):** Yun wil de tabel direct zien, zonder
  eerst op de uitklapper te klikken (`expanded=True`). Reden: het percentage zonder coördinaten bepaalt
  hoe voorzichtig je de kaart leest.
- **Tabbladen groter en met ruimte ertussen:** Yun wilde grotere tabbladnamen, meer ruimte ertussen
  en een leuker design. Via CSS in `app.py`: tekst 1,15 rem (vet), 0,5 rem ruimte ertussen, de
  onderstreping van Streamlit verborgen en een hoverstand. Een eerste versie met volledig ronde
  "pillen" was Yun te ovaal; op basis van een voorbeeld-screenshot zijn het nu rechthoekige tabbladen
  met enkel de bovenhoeken afgerond (10 px) en het gekozen tabblad donkerblauw (`#156082`, kleur uit
  het voorbeeld) met witte tekst. Daarna wilde Yun de knoppen 15 % korter, zonder ruimte ertussen en
  met schuine zijkanten (20 graden): nu parallelogrammen die tegen elkaar sluiten (`clip-path` op
  `::before`, zodat de tekst recht blijft). Gemeten: de zeven tabbladen samen zijn 743 px breed tegenover
  883 px voordien (-16 %). Aanname: "20 %" gelezen als een hoek van 20 graden, en beide zijkanten
  leunen dezelfde kant op (zo sluiten ze zonder tussenruimte aan). Yun vond de tekst daarna te krap
  tegen de schuine rand en wilde afgeronde bovenhoeken: de vorm is nu een `skewX(-20deg)` met
  `border-radius: 10px 10px 0 0` (in plaats van `clip-path`, dat niet kan afronden), en de zijruimte
  is groter (1,35 rem). Gemeten: de zeven tabbladen zijn samen 834 px breed (883 px in de rechthoekige
  versie), dus de eerdere verkorting van 15 % is met opzet grotendeels teruggedraaid. Sub-tabbladen (Omstandigheden) zijn iets kleiner (1 rem). Technisch:
  in Streamlit 1.64 is een tabblad een `div` met `data-testid="stTab"`, geen `button`; gecontroleerd
  in een echte browser (Edge, DevTools).
  **Definitieve vorm (voorbeeld van Yun, map `screenshot button`):** de kleur `#156082` blijft, het
  design volgt het voorbeeld: trapeziumvormige tabbladen die licht overlappen, met sterk afgeronde
  bovenhoeken (vorm als `clip-path: polygon(...)`, berekend met een Bezier-curve), het gekozen tabblad
  donkerblauw met witte tekst, de andere wit met grijze hoofdletters en een zachte schaduw, en een
  lijn in `#156082` eronder (eerst 4 px; Yun wilde eerst 70 % en daarna 50 % van de
  oorspronkelijke dikte: nu 2 px, bij de sub-tabbladen 1,5 px). De lichtblauwe balk achter de tabbladen heeft Yun laten
  schrappen (screenshot in de map `achtergrond kleur`): de achtergrond van de rij is nu transparant. Dit vervangt de parallelogramvorm
  hierboven. Aanname: hoofdletters en wit voor de niet-gekozen tabbladen komen uit het voorbeeld;
  niet gecontroleerd in dark mode. De zeven tabbladen zijn samen 944 px breed (was 834).
- **Tegenpartij "Onbekend" blijft Onbekend:** Yun vroeg of de 530 fietsongevallen waarbij de andere
  partij code 99 "Onbekend" heeft (242 met Type1 onbekend + Type2 fiets, 288 omgekeerd; 0,7 % van de
  71.881 fietsongevallen) als eenzijdig ongeval moesten tellen. Antwoord: nee. De data zegt niet of
  het een eenzijdig ongeval is, een niet-geïdentificeerde tegenpartij (bijvoorbeeld vluchtmisdrijf) of
  een invulfout. Reden: 7,2 % van deze ongevallen is ernstig tegenover 17-18 % bij eenzijdige
  ongevallen, en het aantal groeit van 7 (2017) naar 159 (2024), wat op een andere registratie wijst.
  De zin onder de grafiek legt dit nu uit. Bij fietsongevallen is geen enkel Type1 of Type2 leeg.
- **Heatmap geschrapt en klaarzetten voor Streamlit Cloud:** Yun vond de heatmap niet meer nodig
  ("het is al voldoende om te kunnen analyseren en presenteren"); de ranglijst met trend en de
  sparkline volstaan. Voor de publieke URL: repo `yunleebe/DS_oef` (app.py in de hoofdmap), Python 3.13
  op Cloud, `requirements.txt` met dezelfde versies als `syntra-ds` (streamlit 1.64.0, pandas 3.0.6,
  openpyxl 3.1.5, pyproj 3.7.2, pyarrow 24.0.0, plotly 6.9.0). Gesimuleerd zonder Excel (enkel
  `app.py`, `pipeline.py` en de 14 parquet-bestanden): de app start in 4,6 seconden zonder fouten.
  De README bevat de stappen om te publiceren.
- **Stap 1 gebouwd:** tabbladen en de trendgrafieken (`maak_jaartrend` in `pipeline.py`),
  gecontroleerd met een onafhankelijke pandas-telling.
- **Derde trendgrafiek (aandeel ernstig):** Yun vroeg of de piek in 2022 (graad 88,5 per 100.000
  tegenover 70,5 in 2017 en 77,9 in 2024) betekent dat fietsen gevaarlijker werd. Antwoord: dat
  kan de data niet zeggen, om drie redenen. (1) Een rij is een ongeval, geen slachtoffer. (2) De
  graad is per inwoner, niet per gefietste kilometer: er kan meer gefietst zijn. (3) De
  registratie veranderde rond 2022 (veel minder ontbrekende coördinaten), wat ook het aantal
  geregistreerde ongevallen kan beïnvloeden; dat is niet onderzocht. Het aandeel ernstig is
  stabiel of licht gedaald (11,0 % in 2017 en 2022, 9,8 % in 2024), dus niets wijst op zwaardere
  ongevallen. Daarom staat er een derde grafiek met het aandeel ernstig per jaar.
- **Maatzinnen aangepast na feedback van Yun:** de zin onder de graadgrafiek zegt nu dat het om
  fietsongevallen gaat en niet om slachtoffers, en dat het niet het risico per gefietste kilometer
  is. De zin "dan komt het gewest precies overeen met zijn bevolking" was onduidelijk; nu staat er
  "evenveel fietsongevallen als je op basis van zijn aantal inwoners zou verwachten", met uitleg
  wat een langere of kortere oranje balk betekent. Yun las de uitkomst als "29 % door meer
  inwoners en 71 % door meer ongevallen"; precies is dat "meer ongevallen per inwoner".
- **Wat de kaart toont (opmerking van Yun):** de concentratiekaart is goed leesbaar. Wallonië
  heeft duidelijk minder fietsongevallen, maar er wonen ook minder mensen. Per inwoner blijft er
  een groot verschil (19,4 in Wallonië, 111,9 in Vlaanderen en 67,0 in Brussel per 100.000);
  daarom komt er naast de kaart (aantallen) ook een vergelijking per inwoner. De kaart overdrijft
  het verschil licht, omdat in Wallonië meer coördinaten ontbreken (Luik en Henegouwen tot ruim
  30 % in sommige jaren).

### Aannames van Claude bij stap 21 (nog niet bevestigd door Yun)
- **Welke kaarten:** zes, afgeleid van de definities in `CLAUDE.md`: Ongevallen, Fietsongevallen,
  Ernstige fietsongevallen, Aandeel fietsongevallen, Aandeel ernstig (fiets) en Fietsongevallen per
  100.000 inwoners. Zonder filters: 267.672, 71.749, 7.829, 26,8 %, 10,9 % en 77,8.
- **"Standaard = alles"** is een lege keuze met de tekst "Alles", geen volledig aangevinkte lijst.
  Anders staan er 581 gemeenten als labels in één filter. Geen keuze betekent geen beperking (zoals
  een slicer in Power BI).
- **Trapsgewijs:** wijzig je Gewest of Provincie, dan gaan de filters eronder terug op "Alles". De
  andere filters blijven staan.
- **Aandelen met filters:** teller én noemer volgen de filters. Filter je op Weggebruiker = Fiets,
  dan is het aandeel fietsongevallen dus 100 %.
- **Fietsongevallengraad met filters:** fietsongevallen / bevolking × 100.000, gemiddeld per jaar.
  De bevolking is de som over de gekozen jaren en gemeenten (alle gemeente-jaarcombinaties). Enkel
  Jaar, Gewest, Provincie en Gemeente beïnvloeden de noemer. Een filter als Weer verandert dus
  enkel de teller.
- **Opties:** een filter toont enkel waarden die in `Fact_Accidents` voorkomen. (Bij Wegtype staat
  sinds beslissing 22 ook "Autosnelweg".)
- **Labels:** de filternamen heb ik vertaald (Weer, Wegdek, Licht, Kruispunt, Wegtype, Ernst van het
  ongeval, Hindernis, Weggebruiker). De waarden in de filters zijn de labels uit de data, zoals
  "met zwaargewonden" (kleine letter) en "onbekend".
- **Datakwaliteit** volgt de filters niet: ze gaat over de volledige data.
- **Parquet herbouwd** na de wijziging in `pipeline.py`; de inhoud is niet veranderd.
- **Niet visueel gecontroleerd:** de logica en de cijfers zijn getest, maar ik heb de app niet in een
  browser bekeken (kaartgrootte, afkapping van tekst).

### Aannames van Claude bij het datamodel (nog niet bevestigd door Yun)
- **Autosnelweg:** *vervangen door beslissing 22.* Eerst verdwenen de 21.860 rijen uit
  `Fact_Accidents`; nu blijven ze erin en staan ze standaard uit in het filter Wegtype.
- **Codes blijven tekst zoals in de bron.** De weggebruikerscodes zijn `'01'` … `'09'`, `'10'`,
  `'11'`, `'99'` (voorloopnul). (Fiets: zie beslissing 17.)
- **`Gemeente_Jaar`:** één extra tabel (bevolking + tellingen) met Municipality, Province en Region
  uit `Dim_NIS`, Total, Accidents, Bike_Accidents en Serious_Bike_Accidents. De drie tellingen
  volgen uit de definities in `CLAUDE.md`. **Bevestigd door Yun:** de tabel toont duidelijk wat
  nodig is en blijft. De ongebruikte stubs `voeg_regio_toe` en `tel_per_regio` zijn weg.
- **`Hour` = 99** (3 rijen) blijft staan, want we verwijderen geen rijen.
- **De 138 punten > 50 km van hun eigen gemeente** (op basis van de coördinaten) blijven staan en
  tellen mee op de kaart. Ze liggen wel binnen België.
