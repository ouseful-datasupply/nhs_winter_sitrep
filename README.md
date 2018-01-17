# Winter sitrep cli

Simple CLI to download time series data from [NHS Winter Daily SitRep 2017-18 Data](https://www.england.nhs.uk/statistics/statistical-work-areas/winter-daily-sitreps/winter-daily-sitrep-2017-18-data/) and pop it into a `SQLite3` database.

By default, the database is created as `nhs_sitrepdb.db` with tables:

- `sitrep` for *Winter Sitrep: Acute Time series* data
- `nhs111` for *Winter SitRep: NHS111 Time series* data

The data tables are simple long form and unnormalised.

An easy way of querying the database via a browser is to use [*Franchise*](https://blog.ouseful.info/2017/09/25/asking-questions-of-csv-data-in-the-browser-with-franchise/).

## Installation

`pip install --upgrade --no-deps git+https://github.com/ouseful-datasupply/nhs_winter_sitrep.git`

## Usage

- `nhs_winter_sitrep collect`
- `nhs_winter_sitrep [OPTIONS] collect`

### Options:

- `--dbname`, *default='nhs_sitrepdb.db'*, SQLite database name
- `--sitrepurl`, *default=None*, Winter sitrep URL
- `--sitreptable`, *default='sitrep'*, Winter sitrep db table name
- `--sitrep111url`, *default=None*, NHS111 Winter sitrep URL
- `--sitrep111table`, *default='nhs111'*, Winter sitrep db table name

