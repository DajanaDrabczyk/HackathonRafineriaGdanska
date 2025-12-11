1. crude_assays

Zbiór podstawowych parametrów fizykochemicznych różnych gatunków ropy naftowej.
W realnych rafineriach dane te wpływają na wybór surowca oraz efektywność procesów.

Kolumny:

| kolumna       | typ  | opis                                                  |
| ------------- | ---- | ----------------------------------------------------- |
| `oil_type`    | TEXT | Nazwa gatunku ropy (np. Brent, WTI, Arab Light).      |
| `api_gravity` | REAL | Gęstość API – miara lekkości ropy (wyższa = lżejsza). |
| `sulfur_pct`  | REAL | Zawartość siarki w % (niższa = „słodsza” ropa).       |
| `origin`      | TEXT | Region/kraj pochodzenia.                              |

2. refinery_margins

Zestawienie dziennych marż rafineryjnych dla paliw – uproszczone dane syntetyczne.
Użyteczne do analizy trendów i testowania zapytań ekonomicznych.

Kolumny:

| kolumna            | typ  | opis                                                              |
| ------------------ | ---- | ----------------------------------------------------------------- |
| `date`             | TEXT | Data w formacie YYYY-MM-DD.                                       |
| `diesel_margin`    | REAL | Marża rafineryjna dla oleju napędowego.                           |
| `gasoline_margin`  | REAL | Marża rafineryjna dla benzyny.                                    |
| `crack_spread_321` | REAL | Crack spread 3:2:1 – uproszczony wskaźnik opłacalności rafinacji. |


3. imports

Dane o imporcie ropy do kraju lub zakładu – uproszczone liczby wolumenów.

Kolumny:

| kolumna         | typ     | opis                                |
| --------------- | ------- | ----------------------------------- |
| `year`          | INTEGER | Rok importu.                        |
| `country`       | TEXT    | Kraj pochodzenia ropy.              |
| `volume_tonnes` | REAL    | Wolumen sprowadzonej ropy w tonach. |


4. weather

Dane pogodowe – przydatne do analizy sezonowości (np. wpływ temperatur na popyt).

Kolumny:

| kolumna    | typ  | opis                                                |
| ---------- | ---- | --------------------------------------------------- |
| `date`     | TEXT | Data YYYY-MM-DD.                                    |
| `temp_avg` | REAL | Średnia temperatura dnia.                           |
| `season`   | TEXT | Pora roku (`winter`, `spring`, `summer`, `autumn`). |


5. Inne:

- Global Refinery Production Dataset (EIA lub Eurostat dane o produkcji paliw)

Możliwe pytania:

„Trend wykorzystania mocy rafinerii w UE od 2010 do 2024”

„Która rafineria ma najwyższy udział produkcji benzyny?”

„Porównaj diesel_output przed i po modernizacjach”

6. Przemysłowy dataset „Energy & Emissions Monitoring

| kolumna                  | typ  | opis                       |
| ------------------------ | ---- | -------------------------- |
| `date`                   | TEXT | Data YYYY-MM-DD            |
| `facility`               | TEXT | Nazwa instalacji           |
| `energy_used_mwh`        | REAL | Zużycie energii (MWh)      |
| `steam_generated_tonnes` | REAL | Wyprodukowana para (t)     |
| `gas_consumption_nm3`    | REAL | Zużycie gazu (Nm³)         |
| `co2_emissions_tonnes`   | REAL | Emisje CO₂ (t)             |
| `so2_emissions_kg`       | REAL | Emisje SO₂ (kg)            |
| `flaring_volume_nm3`     | REAL | Ilość gazu spalonego (Nm³) |

Instalacje:

Refinery_A

Refinery_B

Petrochemical_Unit

Hydrogen_Plant

