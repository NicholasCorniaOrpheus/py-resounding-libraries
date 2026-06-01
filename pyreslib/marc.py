from pymarc import MARCReader, Record, Field, Subfield, Indicators
import os
from copy import deepcopy

from pyreslib import utilities


def generate_record_dict(marc_filepath: str, json_filepath: str, id_name: str) -> list:
    """
    Returns a list of dictionaries from a MARC record downloaded via Koha Cataloging batch import tool.

    Args:
    marc_filepath (str): Location of the MARC file to be processed. Default directory is `./data/koha_auth/marc` for authorities and `./data/koha_biblio/marc` for bibliographic records.
    json_filepath (str): Destination file. Default directory is `./data/koha_auth/json` for authorities and `./data/koha_biblio/json` for bibliographic records. Set to `None` if you wish not to save the JSON file locally.
    id_name (str): Field name of ID value. Use `biblio_id` for bibliographic records and `auth_id` for authorities.

    Returns:
    record_dict (list): List of dictionaries in MARC-in-JSON format.
    """
    n = 0
    success = 0
    f = open(records_filename, "rb")
    reader = MARCReader(f)
    record_dict = []
    for record in reader:
        n += 1
        record_as_dict = record.as_dict()
        try:
            record_id = list(
                filter(lambda x: "001" in x.keys(), record_as_dict["fields"])
            )[0]["001"]
            record_dict.append(
                {
                    id_name: record_id,
                    "record": record_as_dict,
                }
            )
            success += 1
        except KeyError:
            pass

    print(f"{success} records out of {n} have been successfully extracted.")

    # Saving dictionary to JSON
    if json_filepath is not None:
        utilities.dict2json(record_dict, json_filepath)

    return record_dict
