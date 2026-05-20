import requests
import os
import csv
from pyreslib import koha 

def get_metadata_from_google_api(isbn:str, google_api_key:str) -> dict:
    """
    Get book metadata from Google Books API.
    Args:
    isbn (str): The ISBN number of the book as string.
    google_api_key (str): Your Google API key for accessing the Books API from credentials.

    Returns:
    response (dict): JSON dictionary of the Google API metadata

    """
    GB_API_URL = "https://www.googleapis.com/books/v1/volumes"
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "google-books-metadata/1.0 (+https://example.org)"}
    )
    params = {"q": f"isbn:{isbn}", "key": google_api_key}
    response = session.get(GB_API_URL, params=params, timeout=10)
    """# Debugging
    print("REQUEST URL:", response.request.url)
    print("REQUEST HEADERS:", response.request.headers)
    print("REQUEST BODY (bytes):", response.request.body)
    print("STATUS:", response.status_code)
    print("RESPONSE HEADERS:", response.headers)
    print("RESPONSE TEXT:", (response.text or ""))
    """

    return response.json()

def get_google_api_koha_mapping(google_koha_mapping_filepath=os.path.join("data","mappings","google","google_books-koha_mapping.csv")) -> list:
    """
    Get the mapping between Google Books API metadata fields and Koha metadata fields from a CSV file.
    Args:
    google_koha_mapping_filepath (str): The file path to the CSV file containing the mapping.

    Returns:
    mapping (list): A list of dictionaries of the mappins.
    """
    mapping = []
    with open(google_koha_mapping_filepath, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            mapping.append(
                {
                    "google_field": row['json_key'],
                    "type": row['type'],
                    "koha_field": f"{row["field"]}${row["subfield"]}",
                    "is_authority": bool(row['is_authority']),
                    "input_format": row["input_format"],
                    "output_format": row["output_format"]

                })

    return mapping


def get_isbn_from_biblio_id(biblio_id: int, koha_session, base_url: str) -> str:
    """
    Get the ISBN number from a Koha biblio_id.
    Args:
    biblio_id (int): The biblio_id of the book in Koha.
    koha_session: An authenticated Koha session object.
    base_url (str): The base URL of the Koha API.

    Returns:
    isbn (str): The ISBN number of the book as string.
    """
    biblio_metadata = koha.get_biblio_marc(session=koha_session,biblio_id=biblio_id,base_url=base_url)
    isbn = None
    for field in biblio_metadata['fields']:
        if "020" in field.keys():
            isbn = field['subfields'][0]['a']
            break
    return isbn


def enhance_biblio_record_from_isbn(biblio_id: int, koha_session,  base_url: str, google_api_key: str):
    """
    Enhance a Koha biblio record with metadata from Google Books API using the ISBN number.
    Args:
    biblio_id (int): The biblio_id of the book in Koha.
    koha_session: An authenticated Koha session object.
    base_url (str): The base URL of the Koha API.

    Returns:
    None
    """
    isbn = get_isbn_from_biblio_id(biblio_id=biblio_id,koha_session=koha_session,base_url=base_url)
    if isbn is not None:
        google_metadata = get_metadata_from_google_api(isbn=isbn, google_api_key=google_api_key)
        mappings = get_google_api_koha_mapping()

        for mapping in mappings:
            if mapping["is_authority"] is False:
                # import the new value as text


            else:
                # search for the right authority in the 

        
    else: 
        print(f"ISBN is missing for biblio ID {biblio_id}")