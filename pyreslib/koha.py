from pyreslib import utilities, marc
import requests
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import json
import os
from time import time

# Multiprocessing
from multiprocessing import Pool, cpu_count
from functools import partial
from typing import List, Dict, Any
import traceback


def koha_session(
    client_id: str, client_secret: str, user_agent: str, base_url: str, scope="all"
):
    """Returns an OAuth2 session, given client ID and secret key of your Koha account.

    Args:
        client_id (str): Client ID associated with your Koha Admin User.
        client_secret (str): Secret key provided by the Koha Administration.
        user_agent (str): User-Agent string. Default is None.
        base_url (str): Base URL for your Koha Staff interface

    Returns:
        session (oauth2): OAuth2 session

    Examples:
        >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")

    """
    token_url = f"{base_url}/oauth/token"  # This may be different for your endpoint

    oauth2client = OAuth2Client(
        token_endpoint=token_url, client_id=client_id, client_secret=client_secret
    )
    # Force the User-Agent before authorization
    if user_agent is not None:
        oauth2client.session.headers.update({"User-Agent": user_agent})
    auth = OAuth2ClientCredentialsAuth(oauth2client, scope=scope, resource=base_url)
    session = requests.Session()
    session.auth = auth
    # And also later, why not?
    if user_agent is not None:
        session.headers.update({"User-Agent": user_agent})
    return session


# API for Koha API v1


def get_authority_marc(session, auth_id: int, base_url: str) -> dict:
    """Get MARC in JSON data for authority from Koha API

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        auth_id (int): Authority ID for the requested record.
        base_url (str): Koha API url from credentials.

    Returns:
        response (dict): MARC in JSON serialization of the record.

    Examples:
        >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> marc_json_authority = pyreslib.koha.get_authority_marc(my_session,407,base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> marc_json_authority[0:145] # returns the first 145 characters of the JSON dictionary
        >>>{'leader': '00744nam a2200217Ia 4500', 'fields': [{'000': '00373cz  a2200157n  4500'}, {'001': '407'}, {'003': 'OI'}, {'005': '20260330105335.0'} ...


    """
    headers = {"Accept": "application/marc-in-json"}
    response = session.get(f"{base_url}/authorities/{str(auth_id)}", headers=headers)
    return response.json()


def get_authority_json(session, auth_id: int, base_url: str) -> dict:
    """Get JSON data for authority from Koha API. The amount of metadata is very limited compared to the MARC-in-JSON response.

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        auth_id (int): Authority ID for the requested record.
        base_url (str): Koha API url from credentials.

    Returns:
        response (dict): JSON serialization of the record.

    Examples:
        >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> json_authority = pyreslib.koha.get_authority_json(my_session,407,base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> {'authority_id': 11721, 'created_date': '2021-01-12', 'framework_id': 'PERSO_NAME', 'heading': 'Bach, Anna Magdalena 1701-1760', 'modified_date': '2026-03-30T09:54:31+02:00'}


    """
    headers = {"Accept": "application/json"}
    response = session.get(f"{base_url}/authorities/{str(auth_id)}", headers=headers)
    return response.json()


def get_biblio_marc(session, biblio_id: int, base_url: str) -> dict:
    """Get MARC in JSON data for biblio from Koha API. **Note**: this method does not return items metadata, use [pyreslib.koha.get_items_from_biblio_json][] in order to extract metadata at item's level.

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        biblio_id (int): Biblio ID for the requested record.
        base_url (str): Koha API url from credentials.

    Returns:
        response (dict): MARC in JSON serialization of the record.

    Examples:
        >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> marc_json_record = pyreslib.koha.get_biblio_marc(my_session,12,base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> {"leader": "01574acm a2200301   4500","fields": [{"001": "1"},{"005": "20251104114244.0"},{"008": "210318s1730       ||le| |||| 00| 0 fre d"},{"041": {"ind1": " ","ind2": " ","subfields": [{"a": "fre"}]}}, ...] }



    """
    headers = {"Accept": "application/marc-in-json"}
    response = session.get(f"{base_url}/biblios/{str(biblio_id)}", headers=headers)
    return response.json()


def get_biblio_json(session, biblio_id: int, base_url: str) -> dict:
    """Get JSON data for biblio from Koha API. The amount of metadata is very limited compared to the MARC-in-JSON response.

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        biblio_id (int): Biblio ID for the requested record.
        base_url (str): Koha API url from credentials.

    Returns:
        response (dict): JSON serialization of the record.

    Examples:
        >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> json_record = pyreslib.koha.get_biblio_json(my_session,12,base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>>{'abstract': None, 'age_restriction': None, 'author': 'Playford, Henry', 'biblio_id': 1637, ... }


    """
    headers = {"Accept": "application/json"}
    response = session.get(f"{base_url}/biblios/{str(biblio_id)}", headers=headers)
    return response.json()


def get_items_from_biblio_json(session, biblio_id: int, base_url: str) -> dict:
    """Get JSON item data for biblio from Koha API.

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        biblio_id (int): Biblio ID for the requested record.
        base_url (str): Koha API url from credentials.

    Returns:
        response (dict): JSON serialization of the record's items.

    Examples:
        >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> json_items = pyreslib.koha.get_items_from_biblio_json(my_session,12)
        >>>



    """
    headers = {"Accept": "application/json"}
    response = session.get(
        f"{base_url}/biblios/{str(biblio_id)}/items", headers=headers
    )
    return response.json()


def query_biblio_marc(
    session, base_url: str, q: str, limit: int = 20, offset: int = 0
) -> list:
    """
    Returns a list of MARC-in-JSON biblio record matching a query according to Koha standards. This method exploits the [ListBiblio](https://api.koha-community.org/#tag/biblios/operation/listBiblio) operation.

    **Unfortunately the method does not yet work.**

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        base_url (str): Koha API url from credentials.
        q (str): Query string according to Koha standards. For example 'title:"Orlando furioso" AND author:"Ariosto"'


    Examples:


    """
    headers = {"Accept": "application/json"}
    params = {"limit": limit, "offset": offset, "q": q}

    try:
        response = session.get(
            f"{base_url}/biblios",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e.response.status_code} - {e.response.text}")
        raise


def get_framework_id_biblioitem(session, biblio_id: int, base_url: str) -> str:
    """Get the biblio record framework ID .

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        biblio_id (int): Biblio ID for the requested record.
        base_url (str): Koha API url from credentials.

    Returns:
        framework (str): Koha Framework ID for the record.

    Examples:
        >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , user_agent="{USER_AGENT}", base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> pyres;lib.koha.get_framework_id_biblioitem(my_session,12,base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> "1"

    """
    try:
        return get_biblio_json(session=session, biblio_id=biblio_id, base_url=base_url)[
            "framework_id"
        ]
    except KeyError:
        return ""


def get_framework_id_authority(session, auth_id: int, base_url: str) -> str:
    """Get the authority record framework ID .

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        auth_id (int): Authority ID for the requested record.
        base_url (str): Koha API url from credentials.

    Returns:
        framework (str): Koha Framework ID for the record.

    Examples:
        >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , user_agent="{USER_AGENT}", base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> pyres;lib.koha.get_framework_id_authority(my_session,1,base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> "1"

    """
    try:
        return get_authority_json(session=session, auth_id=auth_id, base_url=base_url)[
            "framework_id"
        ]
    except KeyError:
        return ""


def update_authority_marc(
    session, auth_id: int, marc_json: dict, base_url: str
) -> dict:
    """Update authority record given a MARC-in-JSON payload via Koha API.

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        auth_id (int): Authority ID for the requested record.
        marc_json (dict): JSON dictionary serialization of the record.

    Returns:
        `None`

    Examples:
        >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> marc_json_authority = {'leader': '00744nam a2200217Ia 4500', 'fields': [{'000': '00373cz  a2200157n  4500'}, {'001': '407'}, {'003': 'OI'}, {'005': '20260330105335.0'} ...
        >>> update_authority_marc(my_session,407,marc_json_authority)


    """
    framework_id = get_framework_id_authority(
        session=session, auth_id=auth_id, base_url=base_url
    )
    if str(framework_id) != "":
        headers = {
            "Accept": "application/json",
            "Content-type": "application/marc-in-json",
            "x-authority-type": str(framework_id),
        }
    else:  # default framework
        headers = {
            "Accept": "application/json",
            "Content-type": "application/marc-in-json",
        }
    response = session.put(
        f"{base_url}/authorities/{str(auth_id)}",
        headers=headers,
        data=json.dumps(
            marc_json
        ),  # dumps serializes the Python dictionary into JSON string
    )

    return None


def update_biblio_marc(session, biblio_id: int, marc_json: dict, base_url: str) -> dict:
    """Update biblio record given a MARC-in-JSON payload via Koha API.

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        biblio_id (int): Biblio ID for the requested record.
        marc_json (dict): JSON dictionary serialization of the record.
        base_url (str): Koha API url from credentials.

    Returns:
        `None`

    Examples:
        >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
        >>> marc_json_record = {'leader': '00744nam a2200217Ia 4500', 'fields': [{'000': '00373cz  a2200157n  4500'}, {'001': '12'}, {'003': 'OI'}, {'005': '20260330105335.0'} ...
        >>> update_biblio_marc(my_session,12,marc_json_record)


    """
    framework_id = get_framework_id_biblioitem(
        session=session, biblio_id=biblio_id, base_url=base_url
    )
    if str(framework_id) != "":
        headers = {
            "Accept": "application/json",
            "Content-type": "application/marc-in-json",
            "x-framework-id": str(framework_id),
        }
    else:  # dafault framework
        headers = {
            "Accept": "application/json",
            "Content-type": "application/marc-in-json",
        }
    response = session.put(
        f"{base_url}/biblios/{str(biblio_id)}",
        headers=headers,
        data=json.dumps(
            marc_json
        ),  # dumps serializes the Python dictionary into JSON string
    )
    return None


# Full catalogue import methods using parallel processing


def get_auth_list_from_csv_report(
    auth_id_csv_filepath: str = "./data/mappings/koha/authority_list.csv",
    auth_id_field="authid",
) -> list:
    """
    Returns a list of all authorities in the catalogue.

    Args:
        auth_id_csv_filepath (str): File path of the csv file coming from report. By default is `data/mappings/authority_list.csv`
        auth_id_field (str): Koha report field name for authority ID. Default is `authid`.

    Returns:
        authority_list (list): List of authority IDs.

    """

    # import csv file and return list
    csv_list = utilities.csv2dict(auth_id_csv_filepath)

    print(csv_list[:4])
    return [int(auth[auth_id_field]) for auth in csv_list]


def get_biblio_list_from_csv_report(
    biblio_id_csv_filepath: str = "./data/mappings/koha/biblio_list.csv",
    biblio_id_field="biblionumber",
) -> list:
    """
    Returns a list of all bibliographic records in the catalogue.

    Args:
        biblio_id_csv_filepath (str): File path of the csv file coming from report. By default is `data/mappings/biblio_list.csv`
        biblio_id_field (str): Koha report field name for biblio ID. Default is `biblionumber`.

    Returns:
        biblio_list (list): List of biblio IDs.

    """

    # import csv file and return list
    return [
        int(biblio[biblio_id_field])
        for biblio in utilities.csv2dict(biblio_id_csv_filepath)
    ]


def import_koha_authorities_from_marc(
    marc_filepath: str, output_directory: str = "./data/koha_auth/json"
) -> list:
    """
    Returns a MARC-in-JSON dictionaries from a MARC import of the authority catalogue.

    Args:
        marc_filepath (str): Location of the MARC file to be processed. Default directory is `./data/koha_auth/marc`.
        output_directory (str): Output directory for the generated JSON. The default filename is "auth_dict-{yyyy-mm-dd}.json". Default is `data/koha_auth/json`. Set to `None` if you wisj not to save the list as JSON.

    Retruns:
        auth_dict (list): List of authority dictionaries with auth_id, wd_id, and record

    """
    # extract all records as dictionaries.
    record_dict = marc.generate_record_dict(
        marc_filepath=marc_filepath, json_filepath=None, id_name="auth_id"
    )

    auth_dict = []
    for record in record_dict:
        # extract wikidata_qids
        wd_id = []
        wd_id = extract_wikidata_id(record["record"])
        auth_dict.append(
            {"auth_id": record["auth_id"], "wd_id": wd_id, "record": record["record"]}
        )

    # Save results to JSON file
    output_filepath = os.path.join(
        output_directory, f"auth_dict-{utilities.get_current_date()}.json"
    )
    if output_directory is not None:
        utilities.dict2json(auth_dict, output_filepath)

    return auth_dict


def import_koha_biblios_from_marc(
    marc_filepath: str, output_directory: str = "./data/koha_biblio/json"
) -> list:
    """
    Returns a MARC-in-JSON dictionaries from a MARC import of the bibliographic catalogue.

    Args:
        marc_filepath (str): Location of the MARC file to be processed. Default directory is `./data/koha_biblio/marc`.
        output_directory (str): Output directory for the generated JSON. The default filename is "biblo_dict-{yyyy-mm-dd}.json". Default directory is `./data/koha_biblio/json`. Set to `None` if you wisj not to save the list as JSON.

    Retruns:
        biblio_dict (list): List of bibliopgraphic record dictionaries with biblio_id and record

    """
    # extract all records as dictionaries.
    record_dict = marc.generate_record_dict(
        marc_filepath=marc_filepath, json_filepath=None, id_name="biblio_id"
    )

    biblio_dict = []
    for record in record_dict:
        biblio_dict.append({"biblio_id": record["auth_id"], "record": record["record"]})

    # Save results to JSON file
    output_filepath = os.path.join(
        output_directory, f"biblio_dict-{utilities.get_current_date()}.json"
    )
    if output_directory is not None:
        utilities.dict2json(biblio_dict, output_filepath)

    return biblio_dict


def fetch_and_process_authority(auth_id: int, session, base_url: str) -> Dict[str, Any]:
    """
    Fetch a single authority from API and extract metadata.
    This function runs in parallel worker processes.

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        auth_id (int): Authority ID for the requested record.
        base_url (str): Koha API url from credentials.

    Returns:
        result (dict): Dictionary containing authority ID, Wikidata ID and MARC-in-JSON record.

    """
    try:
        record = get_authority_marc(session, auth_id, base_url)

        # Extract Wikidata ID
        wd_id = extract_wikidata_id(record)

        return {"auth_id": auth_id, "wd_id": wd_id, "record": record}
    except Exception as e:
        return {"auth_id": auth_id, "wd_id": [], "record": None}


def fetch_and_process_biblio(biblio_id: int, session, base_url: str) -> Dict[str, Any]:
    """
    Fetch a single bibliographic record from API and extract metadata.
    This function runs in parallel worker processes.

    Args:
    session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
    biblio_id (int): Biblio ID for the requested record.
    base_url (str): Koha API url from credentials.

    Returns:
    result (dict): Dictionary containing biblio ID, and MARC-in-JSON record.

    """
    try:
        record = get_biblio_marc(session, biblio_id, base_url)

        return {
            "biblio_id": biblio_id,
            "record": record,
        }
    except Exception as e:
        return {"biblio_id": biblio_id, "wd_id": [], "record": None}


def import_koha_authorities_from_api(
    session,
    base_url: str,
    output_directory: str = "./data/koha_auth/json",
    num_workers: int = None,
) -> List[Dict[str, Any]]:
    """
    Generate authority dictionary using parallel processing.

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        base_url (str): Koha API url from credentials.
        output_directory (str): Output directory for the generated JSON. The default filename is "auth_dict-{yyyy-mm-dd}.json". Default is `data/koha_auth/json`. Set to `None` if you don't want to save the JSON result.
        num_workers: Number of parallel workers (default: CPU count)

    Returns:
        auth_dict (list): List of authority dictionaries with auth_id, wd_id, and record
    """

    start_time = time()

    # get authority_list
    authority_list = get_auth_list_from_csv_report()

    # Set number of workers (default: number of CPU cores)
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)  # Leave one core free

    print(f"Using {num_workers} parallel workers")

    # Use Pool for parallel processing
    with Pool(num_workers) as pool:
        # Map function across all authority IDs
        # using partial to fix other parameters, such as session and base_url
        fetch_auth = partial(
            fetch_and_process_authority, session=session, base_url=base_url
        )
        results = pool.map(fetch_auth, authority_list)

    # Filter successful results
    auth_dict = [result for result in results if result["record"] is not None]

    print(
        f"Successfully imported {len(auth_dict)} authorities out of {len(authority_list)} in {float(time()-start_time)/60} minutes."
    )

    # Save results to JSON file
    output_filepath = os.path.join(
        output_directory, f"auth_dict-{utilities.get_current_date()}.json"
    )
    if output_filepath is not None:
        utilities.dict2json(auth_dict, output_filepath)

    return auth_dict


def import_koha_biblios_from_api(
    session,
    base_url: str,
    output_directory: str = "./data/koha_biblio/json",
    num_workers: int = None,
) -> List[Dict[str, Any]]:
    """
    Generate authority dictionary using parallel processing.

    Args:
        session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        base_url (str): Koha API url from credentials.
        output_directory (str): Output directory for the generated JSON. The default filename is "biblio_dict-{yyyy-mm-dd}.json". Default is `data/koha_biblio/json`.
        num_workers: Number of parallel workers (default: CPU count)

    Returns:
        List of bibliographic record dictionaries with biblio_id and record
    """

    start_time = time()

    # get authority_list
    biblio_list = get_biblio_list_from_csv_report()

    # Set number of workers (default: number of CPU cores)
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)  # Leave one core free

    print(f"Using {num_workers} parallel workers")

    # Use Pool for parallel processing
    with Pool(num_workers) as pool:
        # Map function across all authority IDs
        # using partial to fix other parameters, such as session and base_url
        fetch_biblio = partial(
            fetch_and_process_biblio, session=session, base_url=base_url
        )
        results = pool.map(fetch_biblio, biblio_list)

    # Filter successful results
    biblio_dict = [result for result in results if result["record"] is not None]

    print(
        f"Successfully imported {len(biblio_dict)} biblios out of {len(biblio_list)} in {float(time()-start_time)/60} minutes."
    )

    # Save results to JSON file
    output_filepath = os.path.join(
        output_directory, f"biblio_dict-{utilities.get_current_date()}.json"
    )

    utilities.dict2json(biblio_dict, output_filepath)

    return biblio_dict


# Getting authority and biblio records information via CSV reports from Koha


def get_wd_authority_list(
    report_csv_file=os.path.join(
        "data", "mappings", "wikidata", "wd_authoritu_list.csv"
    ),
    separator="|",
) -> list:
    """
    This method returns a list of authority IDs and their corresponding Wikidata entities from a CSV report exported from Koha.

    Args:
        report_csv_file (str): File path to the CSV report exported from Koha. See [Reports](reports) page for the SQL query.
        separator (str): Separator for multiple values. Pipe is default.

    Returns:
        authority_wd_list (list): A list of dictionaries, each containing an authority ID and its corresponding Wikidata entities.

    Examples:
        >>> authority_wd_list = pyreslib.koha.get_authority_wd_list(report_csv_file="path/to/authorities_wd_list.csv")
        >>> [{"auth_id": 1, "type": "GEOGR_NAME", "main_heading": "Venice", "qid": ["Q641"], "wd_uri": ["http://www.wikidata.org/entity/Q641"]", "wd_label": ["Venice","Venezia"]}, ...]


    """
    authority_wd_list = []
    with open(report_csv_file, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            authority_wd_list.append(
                {
                    "auth_id": int(row["authid"]),
                    "type": row["authtypecode"],
                    "main_heading": row("main_heading"),
                    "qid": row["qid"].split(separator),
                    "wd_uri": row["wd_uri"].split(separator),
                    "wd_label": row["wd_label"].split(separator),
                }
            )

    return authority_wd_list


# Filtering methods for MARC-in-JSON authority records


def extract_wikidata_id(record: dict, wd_field=["024", "1"]):
    query = list(filter(lambda x: wd_field[0] in x.keys(), record["fields"]))
    wd_id = []
    if len(query) > 0:
        for result in query:
            uri_subfield = list(
                filter(
                    lambda x: wd_field[1] in x.keys(), result[wd_field[0]]["subfields"]
                )
            )
            if len(uri_subfield) > 0:
                if "wikidata" in uri_subfield[0][wd_field[1]]:
                    try:
                        wd_id.append(
                            int(
                                uri_subfield[0][wd_field[1]]
                                .split("/")[-1]
                                .replace("Q", "")
                            )
                        )
                    except Exception:
                        pass

    return wd_id


def get_biblio_type(record: dict, biblio_type_field=["942", "c"]) -> str:
    """
    This function returns the biblio type code of a given record.

    Args:
        record (dict): MARC-in-JSON record of the biblio, conform with Koha API.
        biblio_type_field (list): MARC field holding the biblio type code. Default is 942$c.


    Returns:
        biblio_type (str): Biblio type code.

    Examples:
        >>> pyreslib.koha.get_biblio_type(record=marc_json_biblio)
        >>> "BOO"
    """
    try:
        # get biblio type
        query_field = list(
            filter(lambda x: biblio_type_field[0] in x.keys(), record["fields"])
        )
        # the field should be unique
        biblio_type = list(
            filter(
                lambda x: biblio_type_field[1] in x.keys(),
                query_field[0][biblio_type_field[0]]["subfields"],
            )
        )[0][biblio_type_field[1]]

        return biblio_type

    except Exception:
        return None


def get_authority_type(record: dict, auth_type_field=["942", "a"]) -> str:
    """
    This function returns the authority type code of a given record.

    Args:
        record (dict): MARC-in-JSON record of the authority, conform with Koha API.
        auth_type_field (list): MARC field holding the authority type code. Default is 942$a.


    Returns:
        auth_type (str): Authority type code.

    Examples:
        >>> pyreslib.koha.get_authority_type(record=marc_json_authority)
        >>> "PERSO_NAME"
    """
    try:
        # get authority type
        query_field = list(
            filter(lambda x: auth_type_field[0] in x.keys(), record["fields"])
        )
        # the field should be unique
        auth_type = list(
            filter(
                lambda x: auth_type_field[1] in x.keys(),
                query_field[0][auth_type_field[0]]["subfields"],
            )
        )[0]["a"]

        return auth_type

    except Exception:
        return None


def get_wikidata_entities_from_authority(
    record: dict, wikidata_field="024", wikidata_subfields={"uri": "1", "label": "9"}
) -> list:
    """
    This function returns a list of wikidata entities linked with a given record.

    Args:
        record (dict): MARC-in-JSON record of the authority, conform with Koha API.
        wikidata_field (str): Default is "024", according to MARC21 guidelines.
        wikidata_subfields (str): label and authority id for each umbrella term. Default is {"label": "a","id": "9"}.


    Returns:
        wikidata_entities (list): List of Wikidata entities.

    Examples:
        >>> pyreslib.koha.get_wikidata_entities_from_authority(record=marc_json_authority)
        >>> [{"uri": "http://www.wikidata.org/entity/Q42", "label": "Douglas Adams"}, {"uri": "http://www.wikidata.org/entity/Q12345", "label": "Example Entity"}]

    """
    # get wikidata entities
    wd_entities = []
    try:
        query_field = list(
            filter(lambda x: wikidata_field in x.keys(), record["fields"])
        )
        for statement in query_field:
            wikidata_entity = {}
            for wikidata_key in wikidata_subfields.keys():
                metadata = list(
                    filter(
                        lambda x: wikidata_subfields[wikidata_key] in x.keys(),
                        statement[wikidata_field]["subfields"],
                    )
                )
                if len(metadata) > 0:
                    subfield = wikidata_subfields[wikidata_key]
                    wikidata_entity[wikidata_key] = metadata[0][subfield]
                else:
                    metadata = None

            wd_entities.append(wikidata_entity)

        return wd_entities

    except Exception:
        return None


def get_umbrella_terms_from_authority(
    record: dict,
    umbrella_fields={
        "PERSO_NAME": "500",
        "CORPO_NAME": "510",
        "CHRON_TERM": "548",
        "TOPIC_TERM": "550",
        "GEOGR_NAME": "551",
    },
    umbrella_subfields={"label": "a", "id": "9"},
) -> list:
    """
    This function returns a list of umbrella terms of a given record.

    Args:
        record (dict): MARC-in-JSON record of the authority, conform with Koha API.
        umbrella_fields (dict): Dictionary of umbrella fields for the authority type, according to MARC21 guidelines.
        umbrella_subfields (str): label and authority id for each umbrella term. Default is {"label": "a","id": "9"}.


    Returns:
        umbrella_terms (list): List of umbrella terms.

    Examples:
        >>> pyreslib.koha.get_umbrella_terms_from_authority(record=marc_json_authority)
        >>> [{"type": "PERSO_NAME", "label": "Example Person", "id": "434"},{...}]
    """
    # get umbrella terms
    umbrella_terms = []
    try:
        for auth_type in umbrella_fields.keys():
            query_field = list(
                filter(
                    lambda x: umbrella_fields[auth_type] in x.keys(), record["fields"]
                )
            )
            for statement in query_field:
                umbrella_term = {"type": auth_type}
                for umbrella_key in umbrella_subfields.keys():
                    metadata = list(
                        filter(
                            lambda x: umbrella_subfields[umbrella_key] in x.keys(),
                            statement[umbrella_fields[auth_type]]["subfields"],
                        )
                    )
                    if len(metadata) > 0:
                        umbrella_term[umbrella_key] = metadata[0][
                            umbrella_subfields[umbrella_key]
                        ]
                    else:
                        metadata = None

                umbrella_terms.append(umbrella_term)

        return umbrella_terms

    except Exception:
        return None


def get_main_heading_from_authority(
    record: dict,
    headings={
        "PERSO_NAME": "100",
        "CORPO_NAME": "110",
        "CHRON_TERM": "148",
        "TOPIC_TERM": "150",
        "GEOGR_NAME": "151",
        "KOOPM_KEYW": "150",
    },
    heading_subfield="a",
) -> str:
    """
    This function returns the authority main heading of a given record.

    Args:
        record (dict): MARC-in-JSON record of the authority, conform with Koha API.
        headings (dict): Dictionary of main heading fields according to authorty type. Default is {"PERSO_NAME": "100","CORPO_NAME": "110","CHRON_TERM": "148","TOPIC_TERM": "150","GEOGR_NAME": "151"}
        heading_subfield (str): Subfield of the main heading. Default is "a".


    Returns:
        main_heading (str): Main heading string.

    Examples:
        >>> pyreslib.koha.get_main_heading_from_authority(record=marc_json_authority)
        >>> "Example Person"
    """
    # get authority type
    auth_type = get_authority_type(record)
    heading_field = headings[auth_type]

    # get main heading
    try:
        query_field = list(
            filter(lambda x: heading_field in x.keys(), record["fields"])
        )
        # the field should be unique
        main_heading = list(
            filter(
                lambda x: heading_subfield in x.keys(),
                query_field[0][heading_field]["subfields"],
            )
        )[0][heading_subfield]

        return main_heading

    except Exception:
        return None


def get_alternative_headings_from_authority(
    record: dict,
    headings={
        "PERSO_NAME": "400",
        "CORPO_NAME": "410",
        "CHRON_TERM": "448",
        "TOPIC_TERM": "450",
        "GEOGR_NAME": "451",
        "KOOPM_KEYW": "450",
    },
    heading_subfield="a",
) -> list:
    """
    This function returns a list of alternative headings (equivalent terms, pseudonyms,...) of a given record.

    Args:
        record (dict): MARC-in-JSON record of the authority, conform with Koha API.
        headings (dict): Dictionary of main heading fields according to authorty type. Default is {"PERSO_NAME": "100","CORPO_NAME": "110","CHRON_TERM": "148","TOPIC_TERM": "150","GEOGR_NAME": "151"}
        heading_subfield (str): Subfield of the main heading. Default is "a".


    Returns:
        alternative_headings (list): List of alternative headings.

    Examples:
        >>> pyreslib.koha.get_alternative_headings_from_authority(record=marc_json_authority)
        >>> ["Example Person", "Example Pseudonym", "Example Equivalent Term"]
    """
    # get authority type
    auth_type = get_authority_type(record)
    heading_field = headings[auth_type]

    # get alternative headings
    alternative_headings = []
    try:
        query_field = list(
            filter(lambda x: heading_field in x.keys(), record["fields"])
        )
        for statement in query_field:
            alt_heading = list(
                filter(
                    lambda x: heading_subfield in x.keys(),
                    statement[heading_field]["subfields"],
                )
            )[0][heading_subfield]
            alternative_headings.append(alt_heading)

        return alternative_headings

    except Exception:
        return None


# Explicit abbreviations codes from MARC records


def explicit_abbreviations_from_marc(
    record: dict,
    abbreviations_dir=os.path.join("data", "mappings", "abbreviations"),
    abbreviation_codes={
        "relationships": {"fields": ["100$4", "700$4"]},
        "languages": {"fields": ["041$a"]},
        "item_type": {"fields": ["942$c"]},
        "voices_and_musical_instruments": {"fields": ["059$a"]},
    },
) -> dict:
    """
    The method returns a MARC-in-JSON record where MARC abbreviation codes are made explicit.

    Args:
        record (dict): MARC-in-JSON record from Koha API.
        abbreviations_dir (str): Directory path (in data/mappings) containing a series of JSON mappings for standard MARC abbreviation codes.
    Returns:
        explicit_record (dict): MARC-in-JSON record with explicit abbreviations.

    Examples:

    """
    # load abbreviation jsons
    for f in os.scandir(abbreviations):
        if f.endswith(".json"):
            with open(f.path) as json_file:
                abbreviation = json.load(json_file)
                abbreviation_name = f.name.split(".")[0]
                abbreviation_codes[abbreviation_name]["values"] = abbreviation

    # explicit abbreviations according to abbreviation_codes

    for key in abbreviation_codes.keys():
        for tag in abbreviation_codes[key]["fields"]:
            field = tag.split("$")[0]
            subfield = tag.split("$")[1]
            # retrieve field and subfield in record
            query_field = list(lambda x: field in x.keys(), record["fields"])
            print(query_field)
            if len(query_field) > 0:
                for statement in query_field:
                    query_subfield = list(
                        lambda x: subfield in x.keys(), statement["subfields"]
                    )
                    print(query_subfield)
                    if len(query_subfield) > 0:
                        for sub_statement in query_subfield:
                            # retrive abbreviation code
                            retrieved_code = list(
                                lambda x: x["code"] == sub_statement[subfield],
                                abbreviation_codes[key]["values"],
                            )
                            print(retrieved_code)
                            if len(retrieved_code) > 0:
                                # explicit subfield value
                                sub_statement[subfield] = retrieved_code[0]["label"]

                            else:
                                # code not found, ignore
                                pass

    print(f"Explicit MARC-in-JSON record: {record}")
