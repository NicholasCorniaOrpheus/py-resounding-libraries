import requests
import os
import csv
from pyreslib import koha 
import re
from datetime import datetime

def get_metadata_from_google_api(isbn:str, google_api_key:str) -> dict:
    """
    Get book metadata from Google Books API.
    Args:
    isbn (str): The ISBN number of the book as string.
    google_api_key (str): Your Google API key for accessing the Books API from credentials.

    Returns:
    response (dict): JSON dictionary of the Google API metadata

    Examples:
    >>> get_metadata_from_google_api(isbn="9780674970472",goole_api_key=credentals["google"]["api_key"])
    >>> {'kind': 'books#volumes', 'totalItems': 1, 'items': [{'kind': 'books#volume', 'id': 'IXV-EAAAQBAJ', 'etag': 'J8cdkA9cXTg', 'selfLink': 'https://www.googleapis.com/books/v1/volumes/IXV-EAAAQBAJ', 'volumeInfo': {'title': 'In Praise of Failure', 'subtitle': 'Four Lessons in Humility', 'authors': ['Costica Bradatan'], 'publisher': 'Harvard University Press' ...}

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
                    "format_format": row["format"]
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



def transform_value(value: Any, format_type: str) -> Any:
    """
    Apply format transformations to values based on the format field.
    
    Args:
        value: The value to transform
        format_type: The format type from the mapping (e.g., 'ymd_date2year', 'name_surname2surname,_name')
    
    Returns:
        Transformed value
    """
    if value is None or value == "":
        return None
    
    if format_type == "ymd_date2year":
        # Extract year from YYYY-MM-DD format
        try:
            return str(value)[:4]
        except Exception:
            return None
    
    elif format_type == "page_number2page_number_pages":
        # Convert page count to MARC format (e.g., "289" -> "289 pages")
        try:
            return f"{int(value)} pages"
        except Exception:
            return None
    
    elif format_type == "name_surname2surname,_name":
        # Transform "John Doe" to "Doe, John"
        try:
            parts = str(value).strip().split()
            if len(parts) == 1:
                return parts[0]
            else:
                surname = parts[-1]
                name = " ".join(parts[:-1])
                return f"{surname}, {name}"
        except Exception:
            return None
    
    return value


def create_marc_field(tag: str,subfields: list, ind1: str = " ", ind2: str = " ", 
                      ) -> dict:
    """
    Create a MARC field in Koha API format.
    
    Args:
        tag: The MARC field tag
        ind1: First indicator
        ind2: Second indicator
        subfields: List of dictionaries with subfield code and value.
    
    Returns:
        MARC field dictionary
    """
    
    return {
            "tag": tag : {
                "ind1": ind1,
                "ind2": ind2,
                "subfields": subfields
                }
            }
       


def enhance_biblio_record_from_isbn(
    biblio_id: int,
    koha_session,
    base_url: str,
    google_api_key: str
) -> bool:
    """
    Enhance a Koha biblio record with metadata from Google Books API using the ISBN number.
    
    Args:
        biblio_id (int): The biblio_id of the book in Koha.
        koha_session: An authenticated Koha session object.
        base_url (str): The base URL of the Koha API.
        google_api_key (str): Your Google API key for accessing the Books API.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get ISBN from biblio record
        isbn = get_isbn_from_biblio_id(
            biblio_id=biblio_id,
            koha_session=koha_session,
            base_url=base_url
        )
        
        if isbn is None:
            print(f"ISBN is missing for biblio ID {biblio_id}")
            return False
        
        # Get Google Books metadata
        try:
            google_response = get_metadata_from_google_api(
                isbn=isbn,
                google_api_key=google_api_key
            )
            
            if "items" not in google_response or len(google_response["items"]) == 0:
                print(f"No results found for ISBN {isbn} (biblio ID {biblio_id})")
                return False
            
            google_metadata = google_response["items"][0]["volumeInfo"]
        except (KeyError, IndexError) as e:
            print(f"Error parsing Google API response for ISBN {isbn}: {e}")
            return False
        
        # Load mappings
        mappings = get_google_api_koha_mapping()
        
        # Prepare fields to update
        fields_to_add = []
        
        # Process each mapping
        for mapping in mappings:
            json_key = mapping["json_key"]
            field_tag = mapping["field"]
            subfield_code = mapping["subfield"]
            format_type = mapping["format"]
            field_type = mapping["type"]
            
            # Get value from Google metadata
            google_value = google_metadata.get(json_key)
            
            if google_value is None:
                continue
            
            # Apply transformations
            if format_type:
                if field_type == "list":
                    # For list types, apply transformation to each element
                    google_value = [
                        transform_value(item, format_type)
                        for item in google_value
                    ]
                    google_value = [v for v in google_value if v]  # Remove None values
                else:
                    google_value = transform_value(google_value, format_type)
            
            if not google_value:
                continue
            
            # Prepare regular fields
            if field_type == "list":
                # For lists, create multiple fields
                for item in google_value:
                    fields_to_add.append(create_marc_field(tag=field_tag,subfields=[{subfield_code: item}]))
            else:
                # Single value
                fields_to_add.append(create_marc_field(tag=field_tag,subfields=[{subfield_code: google_value}]))
        
        print(f"New fields to be added: {fields_to_add}")

        # Get current biblionumber from API
        biblio = get_biblio_marc(session=koha_session,biblio_id=biblio_id,base_url=base_url)
        print(f"Old biblio: {biblio}")

        # append new fields to biblio in order!

        for new_field in fields_to_add:
            new_tag = int(list(new_field.keys())[0])
            # search right position in biblio record
            for old_field in biblio["fields"]:
                old_tag = int(list(new_field.keys())[0])
                if old_tag < new_tag:
                    continue 
                else:
                    # append new field hier
                    biblio.insert(biblio.index(old_field)+1,new_field)
                    break

        print(f'New biblio: {biblio}')            

    
    except Exception as e:
        print(f"Error enhancing biblio ID {biblio_id}: {e}")
        return False



def enhance_biblio_record_from_isbn(biblio_id: int, koha_session,  base_url: str, google_api_key: str, authority_list: list):
    """
    Enhance a Koha biblio record with metadata from Google Books API using the ISBN number.
    Args:
    biblio_id (int): The biblio_id of the book in Koha.
    koha_session: An authenticated Koha session object.
    base_url (str): The base URL of the Koha API.
    google_api_key (str): Your Google API key for accessing the Books API from credentials.
    authorities_list (list): List of authorities including minimal metadata.

    Returns:
    None
    """
    isbn = get_isbn_from_biblio_id(biblio_id=biblio_id,koha_session=koha_session,base_url=base_url)
    if isbn is not None:
        # get only first result from API
        try:
            google_metadata = get_metadata_from_google_api(isbn=isbn, google_api_key=google_api_key)["items"][0]["volumeInfo"]
            mappings = get_google_api_koha_mapping()

            for mapping in mappings:
                if mapping["is_authority"] is False:
                    # import the new value as text according to output format
                    if mapping["format"] != "":
                        # apply transformations
                        if mappings["format"] == "name_surname2surname,_name":
                            # split surname and name based on space
                            # too complicated ...


                else:
                    # search for the right authority in the
        except IndexError:
             print(f"ISBN {isbn} problem for {biblio_id}")

        
    else: 
        print(f"ISBN is missing for biblio ID {biblio_id}")