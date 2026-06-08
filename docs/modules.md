# Modules

## Koha

Koha scripts for processing MARC files and interacting with API.

### Oauth2 session

In order to interact with your Koha API you will need to create a Client ID and Secret Key for your Koha admin user.
Follow the [offical documentation](https://koha-community.org/manual/23.11/en/html/webservices.html#api-key-management-interface-for-patrons) in order to generate Client and Secret keys for your user.

### GET metadata from Koha

There are two main serializations for the MARC metadata of records and authorities that the Koha API provides: a detailed MARC in JSON dictionary serialization and a standard JSON serialization.

- [Get authority record metadata from Koha API as MARC-in-JSON][pyreslib.koha.get_authority_marc]
- [Get authority record metadata from Koha API as JSON][pyreslib.koha.get_authority_json]
- [Get bibliographic record metadata from Koha API as MARC-in-JSON][pyreslib.koha.get_biblio_marc]
- [Get bibliographic record metadata from Koha API as JSON][pyreslib.koha.get_biblio_json]

### PUT metadata to Koha

- [Updates authority via Koha API][pyreslib.koha.update_authority_marc]
- [Updates bibliographic record via Koha API][pyreslib.koha.update_biblio_marc]


### Import bibliographic and authority catalogue

In order to import the whole catalogue, we provide two methods: 

1. Batch import from pre-downloaded MARC file from `Cataloging/Stage record for import`. See [import_koha_authorities_from_marc](pyreslib.koha.import_koha_authorities_from_marc) and [import_koha_biblios_from_marc](pyreslib.koha.import_koha_biblios_from_marc).
2. Batch import via API with parallel processing. See [import_koha_authorities_from_api](pyreslib.koha.import_koha_authorities_from_api) and [import_koha_biblios_from_api](pyreslib.koha.import_koha_biblios_from_api).

### Utilities

The module provides a series of functions that will extract specific fields from the MARC-in-JSON dictionary, such as 

- [item type][pyreslib.koha.get_biblio_type]
- [authority type][pyreslib.koha.get_authority_type]
- [Wikidata entities][pyreslib.koha.get_wikidata_entities_from_authority] associated to an authority
- [umbrella terms][pyreslib.koha.get_umbrella_terms_from_authority] associated to an authority
- [main heading][pyreslib.koha.get_main_heading_from_authority] associated to an authority
- [alternative headings][pyreslib.koha.get_alternative_headings_from_authority] (variant spelling and translations)
- [explicit_abbreviations_from_marc][pyreslib.koha.explicit_abbreviations_from_marc]: makes abbreviation codes explicit via mappings stored in `./data/mappings/abbreviations`.


## MARC

This module allows to process MARC files and records with the help of [pymarc](https://pymarc.readthedocs.io/en/latest/). It provides methods to convert MARC records to JSON dictionaries and vice versa, as well as to extract and modify specific information from MARC records.

- [Convert MARC file to MARC-in-JSON dictionary for Koha API][pyreslib.marc.generate_record_dict[]
- [Convert MARC file into plain text][pyreslib.marc.marc2txt]
- [Convert MARC file into CSV][pyreslib.marc.marc2csv]
- [Convert CSV file to MARC for ingestion][pyreslib.marc.csv2marc] based on template in `data/biblio_id/csv`.


## Google Books

This module allows to harvest metadata information from the Google Books API via ISBN of the book. This is useful if you wish to populate your new record with basic metadata by only providing the ISBN code in field 020. A mapping between Google and Koha fields is available in `data/mappins/google`.

- [Enhance record from ISBN code][pyreslib.google_books.enhance_biblio_record_from_isbn]
- [Get book metadata from Google API based on ISBN][pyreslib.google_books.get_metadata_from_google_api]

## Transkribus

This module allows the user to interact with the [Transkribus](https://www.transkribus.org/) API directly on Python. Transkribus is a state-of-the-art Handwritten Text Recognition platform for Digital Humanities scholars.

- [Transkribus API login][pyreslib.transkribus.get_documents_metadata] provinding username and password via `data/credentials/credentials.json`.
- [Extract document metadata][pyreslib.transkribus.get_documents_metadata]
- [Get PAGEXML transcription of page][pyreslib.transkribus.get_page_xml]
- [Get plain text transcription of page][pyreslib.transkribus.get_page_txt]
- [Upload transcription via local PAGEXML file][pyreslib.transkribus.post_page_xml]

## BibTeX

This modules allows the export of bibliographic records in BibTeX format, improving the built-in Koha export feature.

- [Convert bibliographic record into BibTeX][pyreslib.bibtex.convert_biblio_to_bibtex]

## Wikidata

This module provides a way to programmatically interact with Wikidata or another Wikibase instance. It is mostly based on [WikibaseIntegrator](wikibaseintegrator.readthedocs.io/en/stable/) and requires specific username-password or API keys credentials.

### Authentication

In order to avoid Too Many Requests errors from the API endpoint, we advise to create an account on Wikidata (or another Wikibase instance).

- [Authenticate to Wikidata or Wikibase instance via username and password][pyreslib.wikidata.wikibase_integrator_session_basic]
- [Authenticate via Oauth2 credentials][pyreslib.wikidata.wikibase_integrator_session_oauth2]. See [official documentation](https://www.wikidata.org/wiki/Wikidata:REST_API/Authentication) for more information.


### Enhancing Authorities

These scripts provide a controlled way to enrich your catalogue's authorities from Wikidata or another Wikibase instance.

- [Add metadata from authority's external URIs field][pyreslib.wikidata.external_sources_metadata_authorities], such as source name, entity label (Wikidata only) and id value. You can customize the external sources list via `data/mappings/lod/external_identifiers.json` mapping.
- [Enhance authorities via Wikidata properties][pyreslib.wikidata.enhance_authorities_via_wikidata] by establishing a mapping between properties and umbrella terms. The mapping CSV is available at `data/mappings/wikidata/wikidata-koha-properties.csv`.

The methods do not direct update the Koha catalogue. Instead, they generate `backup_auth` and `changed_auth` lists of dictionaries which are stored locally as JSON files. Once the user has manually checked the integrity of the data via sampling, the new records can be updated via [pyreslib.wikidata.update_enhanced_authorities][].

### Mapping Wikidata properties URIs

In order to specify a relation statement between two authorites in our Koha catalogue, we have found a solution by recording the property's URI (such as [country][http://wikidata.org/entity/P17]) via a new subfield `i`, not belonging to the standard [MARC21 framework for field 024](https://www.loc.gov/marc/authority/ad024.html).

To facilitate readibility of the URIs, we have created a new Authorized value group called `RELATION_PROPERTY`, associating each URI to the property name.


## RDF

This module provides a series of scripts in order to export Koha record to RDF data structures using the [RDFlib](https://rdflib.readthedocs.io/en/7.1.1/index.html) Python package.

- [Serialize authority record to RDF][pyreslib.rdf.auth_records_to_rdf]
- [Serialize bibliographical record to RDF][pyreslib.rdf.biblio_records_to_rdf]
