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
- **Reden:** geen reden opgegeven.

### 12. Mag `openpyxl` in `requirements.txt`?
- **Antwoord:** ja. Alle packages die in `syntra-ds` staan, mag Claude toevoegen aan
  `requirements.txt` als ze nodig zijn. Staan ze niet in `syntra-ds`, dan mag het niet.
- **Reden:** `syntra-ds` is de standaardomgeving; wat daarin staat, is al goedgekeurd.
- **Uitvoering:** `openpyxl==3.1.5` toegevoegd (versie gecontroleerd in `syntra-ds`).
  Pandas heeft het nodig om `.xlsx` te lezen.
