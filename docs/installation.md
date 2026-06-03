# Installation

Lorem ipsum.

## Package installation

### Using [pip](https://pip.pypa.io/en/stable/getting-started/)

Generate the virtual enviroment on your project folder:

```bash
# Generate local python binaries in folder
python3 -m venv pyreslib-env
```

Activate virtual enviroment in order to invoke the package:

```bash
# activate the enviroment for this terminal
source pyreslib-env/bin/activate
```

```bash
pip install pyreslib
```

### Using [uv](https://docs.astral.sh/uv)

Do not forget to include the `pyproject.toml` file in your project directory. You can find a copy of the file in our [GitHub repository](https://github.com/NicholasCorniaOrpheus/py-resounding-libraries/blob/main/pyproject.toml).

Generate the virtual enviroment on your project folder:

```bash
# Generate local python binaries in folder
uv venv pyreslib-env
```

Activate virtual enviroment in order to invoke the package:

```bash
# activate the enviroment for this terminal
source pyreslib-env/bin/activate
```

```bash
uv add pyreslib
```

### Python for Windows and Mac users

Have a look at this detailed [documentation](https://realpython.com/installing-python/).


## Data structure


## MARC and JSON records

The package suppose a specific folder structure for credentials, mappings files and data paths. You can easily clone our [GitHub repository](https://github.com/NicholasCorniaOrpheus/py-resounding-libraries) and copy the relevant directories to your projec folder.

```bash
git clone https://github.com/NicholasCorniaOrpheus/py-resounding-libraries.git
```

Create a `data` folder with subfolders `koha_auth` and `koha_biblio`. For both authorities and biblionumbers, make subdirectories `marc` and `json`.

```project
your_project
├── data
│   ├── credentials
│   │   └── credentials.json
│   ├── koha_auth
│   │   ├── json
│   │   └── marc
│   ├── koha_biblio
│   │   ├── json
│   │   └── marc
│   └── mappings
│       ├── abbreviations
│       │   ├── item_types.json
│       │   ├── languages.json
│       │   ├── music_instruments.json
│       │   └── relationships.json
│       ├── bibtex
│       │   ├── country_codes.csv
│       │   ├── koha_entry_types.json
│       │   └── role_codes.csv
│       ├── external_sources
│       │   └── external_sources.json
│       ├── google
│       │   └── google_books-koha_mapping.csv
│       ├── koha
│       │   └── authority_list.csv
│       ├── omekas
│       │   ├── biblionumber_barcode.csv
│       │   ├── koha-omekas_mapping - auth.csv
│       │   ├── koha-omekas_mapping - biblio.csv
│       │   ├── koha-omekas_mapping - locations.csv
│       │   ├── koha-omekas_mapping - media.csv
│       │   ├── koha-omekas_mapping - projects.csv
│       │   ├── koha-omekas_mapping - researchers.csv
│       │   └── koha-omekas_mapping - research_groups.csv
│       └── wikidata
│           ├── authority_wd_list.csv
│           └── wikidata-koha-properties.csv


```

### Credentials

In your `data` folder you should create a `credentials` directory to store all your sensible data. All credentials are stored in `credentials.json` file. Copy the [credential template](https://github.com/NicholasCorniaOrpheus/py-resounding-libraries/blob/main/credentials/credentials.json) from our GitHub repository.


## Mappings

Create a `data/mappings` folder in order to store all mappings between your Koha instance and other external services, such as Wikidata, Google Books, Omeka S and Resource Space. You can copy the [mappings template]() from our GitHub repository and modify them accordingly.


## Koha Setup

- Generate Client ID and Secret Key for your Koha admin user.
- Generate public reports for calculating maximal id for authorities and biblionumbers.
- Allow API preferences from Koha Administration. 