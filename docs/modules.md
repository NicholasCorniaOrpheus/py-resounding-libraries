# Modules

## Koha

Koha scripts for processing MARC files and interacting with API.

### Oauth2 session

In order to interact with your Koha API you will need to create a Client ID and Secret Key for yuor Koha admin user.
Follow the [offical documentation](https://koha-community.org/manual/23.11/en/html/webservices.html#api-key-management-interface-for-patrons) in order to generate Client and Secret keys for your user.

### GET metadata from Koha

There are two main serialization for the MARC metadata of records and authorities that the Koha API provides: a detailed MARC in JSON dictionary serialization and a standard JSON serialization.

- [get_authority_marc][pyreslib.koha.get_authority_marc]
- [get_authority_json][pyreslib.koha.get_authority_json]
- [get_biblionumber_marc][pyreslib.koha.get_biblionumber_marc]
- [get_biblionumber_json][pyreslib.koha.get_biblionumber_json]

### PUT metadata to Koha

- [put_authority_marc][pyreslib.koha.put_authority_marc]
- [put_biblionumber_marc][pyreslib.koha.put_biblionumber_marc]


## Google Books

This module allows to harvest metadata information from Google Books API via ISBN of the book. Useful if you wish to populate your new record with basic metadata by only providing the ISBN code in field 020. A mapping between Google and Koha fields is available in `data/mappins/google`.

- [enhance_biblio_record_from_isbn](pyreslib.google_books.enhance_biblio_record_from_isbn)
- [get_metadata_from_google_api][pyreslib.google_books.get_metadata_from_google_api]

## Transkribus

This module allows the user to interact with the [Transkribus](https://www.transkribus.org/) API directly on Python. Transkribus is a state-of-the-art Handwritten Text Recognition platform for Digital Humanities scholars.

## BibTeX

This modules allows the export of bibliographicn records in BibTeX format, improving the built-in Koha export feature.

- [convert_biblio_to_bibtex](pyreslib.bibtex.convert_biblio_to_bibtex)

## Wikidata

Series of scripts to programmatically interact with Wikidata or another Wikibase instance. It is mostly based on [WikibaseIntegrator](wikibaseintegrator.readthedocs.io/en/stable/) and requires specific username-password or API keys credentials.

**TO BE CONTINUED**...


