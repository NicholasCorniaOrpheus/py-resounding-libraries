import requests
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import json
import os


def oauth2_session(
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


def get_authority_marc(session, auth_id: int) -> dict:
    """Get MARC in JSON data for authority from Koha API

    Args:
                    session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
                    auth_id (int): Authority ID for the requested record.

    Returns:
                    response (dict): MARC in JSON serialization of the record.

    Examples:
                    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
                    >>> marc_json_authority = pyreslib.koha.get_authority_marc(my_session,407)
                    >>> marc_json_authority[0:145] # returns the first 145 characters of the JSON dictionary
                    {'leader': '00744nam a2200217Ia 4500', 'fields': [{'000': '00373cz  a2200157n  4500'}, {'001': '407'}, {'003': 'OI'}, {'005': '20260330105335.0'} ...


    """
    headers = {"Accept": "application/marc-in-json"}
    response = session.get(f"{base_url}/authorities/{str(auth_id)}", headers=headers)
    return response.json()


def get_authority_json(session, auth_id: int) -> dict:
    """Get JSON data for authority from Koha API

    Args:
                    session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
                    auth_id (int): Authority ID for the requested record.

    Returns:
                    response (dict): JSON serialization of the record.

    Examples:
                    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
                    >>> json_authority = pyreslib.koha.get_authority_json(my_session,407)


    """
    headers = {"Accept": "application/json"}
    response = session.get(f"{base_url}/authorities/{str(auth_id)}", headers=headers)
    return response.json()


def get_biblionumber_marc(session, biblio_id: int) -> dict:
    """Get MARC in JSON data for biblionumber from Koha API

    Args:
                    session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
                    biblio_id (int): Biblio ID for the requested record.

    Returns:
                    response (dict): MARC in JSON serialization of the record.

    Examples:
                    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
                    >>> marc_json_record = pyreslib.koha.get_biblionumber_marc(my_session,12)



    """
    headers = {"Accept": "application/marc-in-json"}
    response = session.get(f"{base_url}/biblios/{str(biblio_id)}", headers=headers)
    return response.json()


def get_biblionumber_json(session, biblio_id: int) -> dict:
    """Get JSON data for biblionumber from Koha API. **Note**: this method does not return items metadata, use [pyreslib.koha.get_items_from_biblio_json][] in order to extract metadata at item's level.

    Args:
                    session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
                    biblio_id (int): Biblio ID for the requested record.

    Returns:
                    response (dict): JSON serialization of the record.

    Examples:
                    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
                    >>> json_record = pyreslib.koha.get_biblionumber_json(my_session,12)


    """
    headers = {"Accept": "application/json"}
    response = session.get(f"{base_url}/biblios/{str(biblio_id)}", headers=headers)
    return response.json()


def get_items_from_biblio_json(session, biblio_id: int, base_url: str) -> dict:
    """Get JSON item data for biblionumber from Koha API.

    Args:
                    session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
                    biblio_id (int): Biblio ID for the requested record.

    Returns:
                    response (dict): JSON serialization of the record's items.

    Examples:
                    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
                    >>> json_items = pyreslib.koha.get_items_from_biblio_json(my_session,12)



    """
    headers = {"Accept": "application/json"}
    response = session.get(
        f"{base_url}/biblios/{str(biblio_id)}/items", headers=headers
    )
    return response.json()


def get_framework_id_biblioitem(biblio_id: int) -> str:
    """Get the framework ID of the biblionumber."""
    try:
        return get_biblionumber_json(biblio_id)["framework_id"]
    except KeyError:
        return ""


def get_framework_id_authority(auth_id: int) -> str:
    """Get the framework ID of the authority."""
    try:
        return get_authority_json(auth_id)["framework_id"]
    except KeyError:
        return ""


def put_authority_marc(session, auth_id: int, marc_json: dict) -> dict:
    """Put MARC in JSON data of authority via Koha API

    Args:
                    session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
                    auth_id (int): Authority ID for the requested record.
                    marc_json (dict): JSON dictionary serialization of the record.

    Returns:
                    response (dict): MARC in JSON response

    Examples:
                    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
                    >>> marc_json_authority = {'leader': '00744nam a2200217Ia 4500', 'fields': [{'000': '00373cz  a2200157n  4500'}, {'001': '407'}, {'003': 'OI'}, {'005': '20260330105335.0'} ...
                    >>> put_authority_marc(my_session,407,marc_json_authority)


    """
    framework_id = get_framework_id_authority(auth_id)
    if str(framework_id) != "":
        headers = {
            "Accept": "application/json",
            "Content-type": "application/marc-in-json",
            "x-authority-type": str(framework_id),
        }
    else:  # dafault framework
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

    return response.json()


def put_biblionumber_marc(session, biblio_id: int, marc_json: dict) -> dict:
    """Put MARC in JSON data of biblioumber via Koha API

    Args:
                    session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
                    biblio_id (int): Biblio ID for the requested record.
                    marc_json (dict): JSON dictionary serialization of the record.

    Returns:
                    response (dict): MARC in JSON response

    Examples:
                    >>> my_session = pyreslib.koha.oauth2_session(client_id="{CLIENT_ID}"", client_secret="{SECRET_KEY}" , base_url="https://{KOHA_STAFF_URL}/api/v1")
                    >>> marc_json_record = {'leader': '00744nam a2200217Ia 4500', 'fields': [{'000': '00373cz  a2200157n  4500'}, {'001': '12'}, {'003': 'OI'}, {'005': '20260330105335.0'} ...
                    >>> put_biblionumber_marc(my_session,12,marc_json_record)


    """
    framework_id = get_framework_id_biblioitem(biblio_id)
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
    return response.json()
