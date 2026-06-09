# Koha Reports

The Koha database can be queried via [SQL reports](https://koha-community.org/manual/latest/en/html/reports.html#report-from-sql). Reports can be either public or private (only for library staff), and provide an efficient way to retrieve information from the catalogue.

This section provides a list of SQL reports that have been intergrated in the workflow of the package. 

## Koha Records

## Authorities

This report returns a list of authority IDs from catalogue:

```sql
SELECT authid
FROM `auth_header`
ORDER BY authid
LIMIT 50000
```


Used by [pyreslib.koha.get_auth_list_from_csv_report][].


A more advanced report returns a list of authorities with the following fields:

- ``auth_id``: unique identifier for authority.
- ``type``:
- ``main_heading``: the main heading of the authority record according to Authority type.
- ``alt_heading``: list of alternative headings, such as pseudonyms or translations in secondary languages. Pipe separated
- ``uri``: external uri idenfier for the authority, stored in field 024$1. Pipe separated.


```sql
SELECT 
  authid, 
  authtypecode, 
  concat(
    ExtractValue(`marcxml`,'//datafield[@tag="100"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="110"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="111"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="130"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="148"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="150"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="151"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="155"]/*')
  ) main_heading, -- get main heading according to Authority type
    CONCAT_WS('|',
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="400"][1]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="400"][2]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="400"][3]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="400"][4]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="400"][5]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="400"][6]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="400"][7]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="400"][8]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="400"][9]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="400"][10]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="410"][1]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="410"][2]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="410"][3]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="410"][4]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="410"][5]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="410"][6]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="410"][7]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="410"][8]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="410"][9]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="410"][10]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="448"][1]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="448"][2]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="448"][3]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="448"][4]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="448"][5]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="448"][6]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="448"][7]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="448"][8]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="448"][9]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="448"][10]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="450"][1]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="450"][2]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="450"][3]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="450"][4]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="450"][5]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="450"][6]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="450"][7]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="450"][8]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="450"][9]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="450"][10]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="451"][1]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="451"][2]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="451"][3]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="451"][4]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="451"][5]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="451"][6]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="451"][7]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="451"][8]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="451"][9]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="451"][10]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="430"][1]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="430"][2]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="430"][3]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="430"][4]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="430"][5]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="430"][6]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="430"][7]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="430"][8]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="430"][9]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="430"][10]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="455"][1]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="455"][2]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="455"][3]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="455"][4]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="455"][5]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="455"][6]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="455"][7]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="455"][8]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="455"][9]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="455"][10]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="411"][1]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="411"][2]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="411"][3]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="411"][4]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="411"][5]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="411"][6]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="411"][7]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="411"][8]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="411"][9]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="411"][10]/subfield[@code="a"]'), '')
  ) as alt_heading, -- concatenate (first ten) variant spellings and translations of the main heading.
  CONCAT_WS('|',
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][1]/subfield[@code="1"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][2]/subfield[@code="1"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][3]/subfield[@code="1"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][4]/subfield[@code="1"]'), '')
  ) as uri -- concatenate (first four) external URI values
FROM `auth_header`  
ORDER BY authid
LIMIT 50000
```

### Bibliographic Records

The following report returns a list of biblionumbers from your catalogue.

```sql
SELECT  biblio.biblionumber FROM biblio ORDER BY biblio.biblionumber
LIMIT 50000
```

This report is used in order to batch import bibliographic records via Koha API. Used by [pyreslib.koha.get_biblio_list_from_csv_report][].

An alternative version of this report includes all barcodes of items associated with a given biblionumber:

```sql
SELECT  items.biblionumber,items.barcode FROM items ORDER BY items.biblionumber
LIMIT 50000
```


### Wikidata Report

This report assumes that each authority type has on field 024 metadata concerning external URI identifiers. It returns a list of authority records with the following fields:

- `authid`: unique identifier for authority.
- `authtypecode`: MARC code for authority type.
- ``main_heading``: the main heading of the authority record according to Authority type.
- ``qid``: the Wikidata QID associated with the authority record, stored in field 024$a.
- `wd_uri`: Concept URI for Wikidata entity, stored in field 024$1.
- `wd_label`: label associated with Wikidata entity, stored in field 024$9.


```sql
SELECT 
  authid, 
  authtypecode, 
  concat(
    ExtractValue(`marcxml`,'//datafield[@tag="100"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="110"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="111"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="130"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="148"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="150"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="151"]/*'),
    ExtractValue(`marcxml`,'//datafield[@tag="155"]/*')
  ) main_heading, -- get main heading according to Authority type
  CONCAT_WS('|',
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][1]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][2]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][3]/subfield[@code="a"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][4]/subfield[@code="a"]'), '')
  ) as qid, -- concatenate (first four) Wikdiata QIDs values by pipe separator
  CONCAT_WS('|',
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][1]/subfield[@code="1"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][2]/subfield[@code="1"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][3]/subfield[@code="1"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][4]/subfield[@code="1"]'), '')
  ) as wd_uri, -- concatenate (first four) Wikdiata Concept URIs values by pipe separator
  CONCAT_WS('|',
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][1]/subfield[@code="9"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][2]/subfield[@code="9"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][3]/subfield[@code="9"]'), ''),
    NULLIF(ExtractValue(`marcxml`,'//datafield[@tag="024"][4]/subfield[@code="9"]'), '')
  ) as wd_label -- concatenate (first four) Wikdiata Labels values by pipe separator
FROM `auth_header`
WHERE ExtractValue(`marcxml`, '//datafield[@tag="024"][1]/subfield[@code="1"]') LIKE '%wikidata.org%'
   OR ExtractValue(`marcxml`, '//datafield[@tag="024"][2]/subfield[@code="1"]') LIKE '%wikidata.org%'
   OR ExtractValue(`marcxml`, '//datafield[@tag="024"][3]/subfield[@code="1"]') LIKE '%wikidata.org%'
   OR ExtractValue(`marcxml`, '//datafield[@tag="024"][4]/subfield[@code="1"]') LIKE '%wikidata.org%'
ORDER BY authid
LIMIT 50000
```

Export the result of the report as CSV file in `data/mappins/authority_wd_list.csv` and use the method [pyreslib.koha.get_wd_authority_list][].