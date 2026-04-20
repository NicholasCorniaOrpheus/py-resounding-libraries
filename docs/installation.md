# Installation

Lorem ipsum.

## Package installation

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
pip install py-resounding-libraries
```

### Python for Windows and Mac users

Have a look at this detailed [documentation](https://realpython.com/installing-python/).


## Data structure


## MARC and JSON records

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
│       │   ├── author_relations.json
│       │   ├── item_types.json
│       │   ├── languages.json
│       │   └── musical_instruments.json
│       ├── mapping_abbreviation_codes.json
│       ├── mapping_external_sources.json
│       ├── mapping_reports.json
│       └── wikidata-koha-properties.csv

```

### Credentials

In your `data` folder you should create a `credentials` directory to store all your sensible data. All credentials are stored in `credentials.json` file. Copy the [credential template](https://github.com/NicholasCorniaOrpheus/py-resounding-libraries/blob/main/credentials/credentials.json) from our GitHub repository.



## Mappings

Create a `data/mappings` folder in order to store all mappings between your Koha instance and other external services, such as Wikidata, Google Books, Omeka S and Resource Space. You can copy the [mappings template]() from our GitHub repository and modify them accordingly.




## Koha Setup

- Generate Client ID and Secret Key for your Koha admin user.
- Generate public reports for calculating maximal id for authorities and biblionumbers.
- Allow API preferences from Koha Administration (?). 