# Tutorials

## Reconciling authorities via OpenRefine and PyResLib

In this short tutorial, we are going to:

1. Extract from our Koha catalogue a list of authorities without Wikidata QID via Report.
2. Reconcile the authorities to Wikidata QIDs using OpenRefine via the authorities' main headings.
3. Ingest the Wikidata URIs back to the catalogue via PyResLib Koha API functions.

### Step 1

Create a new Koha Report with the following SQL code:
```sql
SELECT authid, concat(
ExtractValue(`marcxml`,'//datafield[@tag="100"]/subfield[@code="a"]'), -- PERSO_NAME
ExtractValue(`marcxml`,'//datafield[@tag="110"]/subfield[@code="a"]'), -- CORPO_NAME
ExtractValue(`marcxml`,'//datafield[@tag="111"]/subfield[@code="a"]'), -- MEETI_NAME
ExtractValue(`marcxml`,'//datafield[@tag="130"]/subfield[@code="a"]'), -- UNIF_TITLE
ExtractValue(`marcxml`,'//datafield[@tag="148"]/subfield[@code="a"]'), -- CHRON_TERM
ExtractValue(`marcxml`,'//datafield[@tag="150"]/subfield[@code="a"]'), -- TOPIC_TERM
ExtractValue(`marcxml`,'//datafield[@tag="151"]/subfield[@code="a"]'), -- GEOGR_NAME
ExtractValue(`marcxml`,'//datafield[@tag="155"]/subfield[@code="a"]')  -- GENRE/FORM
) AS main_heading,
ExtractValue(`marcxml`, '//datafield[@tag="024"]/subfield[@code="1"]') AS wd_uri,
ExtractValue(`marcxml`, '//datafield[@tag="942"]/subfield[@code="a"]') AS type
FROM `auth_header`
WHERE ExtractValue(`marcxml`, '//datafield[@tag="024"]/subfield[@code="1"]') IS NULL
OR ExtractValue(`marcxml`, '//datafield[@tag="024"]/subfield[@code="1"]') = '' 
AND ExtractValue(`marcxml`, '//datafield[@tag="942"]/subfield[@code="a"]') LIKE CONCAT ( '%', <<Authority Type code>>, '%' )
ORDER BY authid ASC

LIMIT 100 -- Adjust the limit value based on your needs and reconciliation time.
```

Select the authority type, such as `PERSO_NAME` or `GEOGR_TERM`. After running the report via the Staff Interface, save the result as CSV file.

### Step 2

Import your CSV file as new project in your [OpenRefine](https://openrefine.org/) application. We are using version 3.10.1 for this tutorial.

You can split the main_heading column based on a separator via `Edit Column/Split into separate columns...` command. Afterwards, you can recombine the splitted columns via `Edit Column/Join columns...`. This procedure is useful in order to turn Personal Names in the form `Surname, Name` into `Name Surname` for Wikidata matching.

![split_columns](./assets/split_columns_openrefine.png)

Once you have reconciled a reasonable number of authorities, you can create a new column via `Edit column/Add column based on this column...` that will parse the Wikidata Concept URI from the reconciliation service by using the GREL formula

```
'http://www.wikidata.org/entity/'+cell.recon.match.id
```

![reconcile](./assets/reconcile_openrefine.png)

### Step 3

Export the OpenRefine project as CSV (Comma separated values) and rename it as `add_qids_to_authorities.csv` in the `data/wikidata` default folder.

Create a Python script in your project folder called `ingest_QIDs_from_CSV.py`
```python
from pyreslib import wikidata, koha, utilities

### CREDENTIALS

credentials = utilities.json2dict("./data/credentials/credentials.json")

koha_base_url = credentials["koha"]["koha_api_url"]

# Generating OAuth2 credentials for Koha API
koha_session = koha.koha_session(
    client_id=credentials["koha"]["oauth_credentials"]["client_id"],
    client_secret=credentials["koha"]["oauth_credentials"]["client_secret"],
    user_agent=credentials["koha"]["oauth_credentials"]["user_agent"],
    base_url=koha_base_url,
)

print("Adding QIDs from CSV file")
wikidata.add_qids_to_authorities(koha_session=koha_session, koha_base_url=koha_base_url)

```

Then from terminal in the script's folder run the command

```bash
python3 ingest_QIDs_from_CSV.py
```

Your authorities should be automatically updated.

