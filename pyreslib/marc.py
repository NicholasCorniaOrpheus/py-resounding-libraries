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
    f = open(marc_filepath, "rb")
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


def marc2txt(marc_filepath):  # MARC2TXT operations and split
    f = open(marc_filepath, "rb")
    reader = MARCReader(f)
    # Take out the file extension
    out = open(marc_filepath.replace(".mrc", ".txt"), "w+")
    for record in reader:
        out.write(str(record) + "\n")

    f.close()
    out.close()


def marc2csv(marc_filepath: str, csv_filepath: str, separator: str = "|"):
    """
    Converts a MARC record into CSV.

    Args:
        marc_filepath (str): Filepath for the MARC file serialized using pymarc.
        csv_filepath (str): Filepath for the output CSV file. See template in `data/koha_biblio/csv` and `data/koha_auth/csv`.
        separator (str): CSV file separator for multiple values. Default is pipe.
    Returns:
        `None`

    Examples:
        >>> csv_filepath = "./data/koha_biblio/csv/records-yyyy-mm-dd.csv"
        >>> marc_filepath = "./data/koha_biblio/marc/records-yyyy-mm-dd.marc"
        >>> marc2csv(marc_filepath,csv_filepath)
    """
    # import MARC file via pymarc as dictionary
    f = open(marc_filepath, "rb")
    reader = MARCReader(f)
    record_dict = []
    for record in reader:
        record_dict.append(record.as_dict())

    # initiate csv dictionary
    csv_dict = []
    # add fields and subfields values
    for record in record_dict:
        # initialize new record

        # continue adding fields and subfields
        for field in record["fields"]:
            print(f"Current field: {field}")
            field_tag = list(field.keys())[0]
            # print(field_tag)
            if field_tag == "001":  # eclude 001 id field
                csv_dict.append(
                    {
                        "leader": record["leader"],
                        "ind1": " ",
                        "ind2": " ",
                        "field": "001",
                        "subfields": "",
                        "values": record["fields"][0]["001"],
                    }
                )
            else:
                try:
                    ind1 = field[field_tag]["ind1"]
                except Exception:
                    ind1 = ""
                try:
                    ind2 = field[field_tag]["ind2"]
                except Exception:
                    ind2 = ""

                try:
                    subfield_tags = separator.join(
                        [
                            list(subfield.keys())[0]
                            for subfield in field[field_tag]["subfields"]
                        ]
                    )
                    subfield_values = separator.join(
                        [
                            item.get(list(item.keys())[0])
                            for item in field[field_tag]["subfields"]
                        ]
                    )

                except TypeError:
                    # the field statement has no subfields
                    subfield_values = field.get(field_tag)
                    subfield_tags = ""
                csv_dict.append(
                    {
                        "leader": "",
                        "ind1": ind1,
                        "ind2": ind2,
                        "field": field_tag,
                        "subfields": subfield_tags,
                        "values": subfield_values,
                    }
                )
            # print(csv_dict)
            # input()

    # save csv_dict as CSV file
    utilities.dict2csv(csv_dict, csv_filepath)


def csv2marc(csv_filepath: str, marc_filepath: str, separator: str = "|") -> dict:
    """
    Converts a record CSV into MARC as dictionary file.

    Args:
        csv_filepath (str): Filepath for the input CSV file. See template in `data/koha_biblio/csv` and `data/koha_auth/csv`.
        marc_filepath (str): Filepath for the MARC file serialized using pymarc.
        separator (str): CSV file separator for multiple values. Default is pipe.

    Returns:
        marc_as_dict (dict): MARC record as dictionary for Koha API.

    Examples:
        >>> csv_filepath = "./data/koha_biblio/csv/records-yyyy-mm-dd.csv"
        >>> marc_filepath = "./data/koha_biblio/marc/records-yyyy-mm-dd.marc"
        >>> csv2marc(csv_filepath,marc_filepath)
        >>> {"leader": ... "fields": [{"001": ... }, ...]}

    """
    # import CSV file as dictionary
    csv_dict = utilities.csv2dict(csv_filepath)

    # generate MARC records file via pymarc
    # new record (overwrite!)
    record_dict = []
    f = open(marc_filepath, "wb")
    record = None
    for row in csv_dict:
        if row["leader"] != "":
            # initate new record
            if record is None:
                # new record
                record = Record()
            else:
                # write previous record
                f.write(record.as_marc())
                record_dict.append(record.as_dict())
                # new record
                record = Record()
            # add leader

            record.leader = str(row["leader"])
            # add 001 field
            record.add_field(Field(tag=row["field"], data=row["values"]))

        else:  # other fields
            # split tags and values based on separator
            field_tag = row["field"]
            list_subfields = row["subfields"].split(separator)
            list_values = row["values"].split(separator)
            if list_subfields == [""]:  # no subfields, only field tag
                record.add_field(Field(tag=field_tag, data=row["values"]))
            else:
                record.add_field(
                    Field(
                        tag=field_tag,
                        indicators=Indicators(row["ind1"], row["ind2"]),
                        subfields=[
                            Subfield(code=list_subfields[i], value=list_values[i])
                            for i in range(len(list_subfields))
                        ],
                    )
                )

    # save MARC file to marc_filepath
    f.write(record.as_marc())
    record_dict.append(record.as_dict())
    f.close()

    return record_dict
