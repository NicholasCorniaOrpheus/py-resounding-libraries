from omeka_s_tools.api import OmekaAPIClient
import requests
from pyreslib import koha, utilities
import os
import pandas as pd
import json, csv
from pathlib import Path


### TO-DO
"""
1. Filter records with digitization and create new items and associated media in Omeka S via API.
2. Update record information via biblio_id and auth_id fields between Koha and Omeka S.
"""


def omekas_session(api_url: str, key_identity: str, key_credential: str):
    """
    Args:
        api_url (str): API URL for your Omeka S instance.
        key_identity (str): Omeka S key identity for the user.
        key_credential (str): Omeka S key credential for the user.

    Returns:
        omekas_session: `omeka_s_tools` session
    """
    omekas_session = OmekaAPIClient(
        api_url=api_url,
        key_identity=key_identity,
        key_credential=key_credential,
    )
    return omekas_session


def generate_omekas_koha_mapping(
    mappings_directory: str | Path = "./data/mappings/omekas/resource_templates",
) -> dict:
    """
    Generates a dictionary from a series of CSV files (auth,biblio,media...).
    Args:
        mappings_directory (str): Path of csv mapping files.
    Returns:
        A dictionary of mappings.
    """
    omekas_mapping = {}

    mappings_directory = Path(mappings_directory)

    for file in Path.glob(mappings_directory, "*.csv"):
        print(f"Loading mapping file: {file}")
        df = pd.read_csv(file, 
            encoding="utf-8-sig",
            dtype={"field": "str", "subfield": "str", "retrieve_label_subfield": "str", 
            "is_authority": "bool","is_biblionumber": "bool","is_code": "bool"})
        df = df.fillna("")
        d = df.to_dict(orient="records")
        omekas_mapping[file.stem] = d

    return omekas_mapping


def import_koha_authorities_to_omekas_from_report(
    koha_report_id: int,
    koha_public_report_url: str,
    omekas_session: OmekaAPIClient,
    koha_session,
    koha_api_base_url: str,
    koha_base_url: str,
    omekas_mapping: dict,
    resource_template_id: int,
    authority_path_url: str = "cgi-bin/koha/authorities/detail.pl?authid=",
    biblio_path_url: str = "cgi-bin/koha/authorities/detail.pl?authid=",
):
    """
    Imports Koha authorities based on an existing public report as Omeka S items of the same resource template type.

    Args:
        koha_report_id (int): Koha public report ID.
        koha_public_report_url (str): Koha public report URL.
        omekas_session (OmekaAPIClient): Omeka S session.
        omekas_mapping (dict): Omeka S mapping dictionary.
        resource_template_name (str): Omeka S resource template name.

    """

    resource_mapping = omekas_mapping[str(resource_template_id)]

    print("Loading resource mapping based on template ID...")
    #print(resource_mapping)
    #input()

    # Get Koha report data, as raw list of list of the form [ [value], [value2] ...]
    response = koha_session.get(f"{koha_public_report_url}{str(koha_report_id)}")

    koha_authorities = [i[0] for i in response.json()]

    print("Retrieving authority IDs from Koha Public Report...")
    #print(koha_authorities)
    #input()

    for auth in koha_authorities:
        # extract metadata from Koha API
        auth_metadata = koha.get_authority_marc(
            session=koha_session, auth_id=int(auth), base_url=koha_api_base_url
        )
        print("Getting record metadata from Koha API...")
        #print(auth_metadata)
        #input()
        # Lookup for existing Omeka S item using koha_authority_base_url+auth_id
        search_results = omekas_session.filter_items_by_property(
            filter_property="dcterms:indentifier",
            filter_value=f"{koha_base_url}{authority_path_url}{str(auth)}",
            filter_type="eq",
        )
        if search_results["total_results"] > 0:
            print(f"Authority {auth} already exists in Omeka S, skipping...")
            print(search_results["results"])
            input()
            continue
        else:
            print(
                f"Authority {auth} is missing. Creating new item according to resource_template"
            )
            # generate payload
            payload = generate_omekas_payload_from_marc_in_json(
                        marc_json=auth_metadata, 
                        record_id=int(auth), 
                        omekas_mapping=omekas_mapping, 
                        resource_template_id=resource_template_id,
                        koha_api_base_url=koha_api_base_url,
                        koha_base_url=koha_base_url)
            print(payload)
            input()
            prep_payload = omekas_session.prepare_item_payload_using_template(
                payload, template_id=resource_template_id
            )
            print(prep_payload)
            input()

            # create new item using resource template
            print("Adding item to OmekaS... press Enter to continue...")
            omekas_session.add_item(prep_payload, template_id=resource_template_id)
            input()



def generate_omekas_payload_from_marc_in_json(
    marc_json: dict, 
    record_id: int, 
    omekas_mapping: dict, 
    resource_template_id: int,
    koha_api_base_url: str,
    koha_base_url: str,
    item_identifier: str = None,
    item_identifier_field: str = "external_id",
    authority_path_url: str = "cgi-bin/koha/authorities/detail.pl?authid=",
    biblio_path_url: str = "cgi-bin/koha/authorities/detail.pl?authid=",
):
    """
    Given a dictionary in MARC in JSON format (from Koha API) returns a payload dictionary for Omekas based on a specific omekas_mapping resource template.
    
    Args:
        marc_json(dict): MARC-in-JSON dictionary from Koha API
        record_id(int): Integer value identifying either a bibliographical or authority record.
        omekas_mapping(dict): Mapping generated by [pyreslib.omekas.generate_omekas_koha_mapping][]
        resource_template_id(int): OmekaS internal resource template for payload parsing.
        koha_api_base_url(str): Base URL for Koha API.
        koha_base_url(str): Base URL for Koha instance, for example [https://cat.orpheusinstituut.be/](https://cat.orpheusinstituut.be/) defined in credentials as `koha_staff_url` or `koha_opac_url`
        item_identifier(str): Unique string indentifying a Koha item belonging to a record. Usually a barcode or a callnumber.
        item_identifier_field(str): JSON field from Koha Item API defining the item_identifier. By default is `external_id`.

    """

    payload = {"o:resource_template": {"o:id": resource_template_id}}

    resource_mapping = omekas_mapping[str(resource_template_id)]

    if item_identifier is not None:
        # retrieve items dictionary
        items = koha.get_items_from_biblio_json(session=koha_session, biblio_id=record_id, base_url=koha_api_base_url)
        # filter only relevant item using item_identifier
        try:
            item = list(filter(lambda x: x[item_identifier_field] == item_identifier, items))[0]

        except IndexError:
            print(f"Error: we could not find item with identifier {item_identifier} in record {record_id}")
            input()
            item = None  

    for prop in resource_mapping:
        if prop["is_item"] is False:
            # filter field value using lambda filter
            fields = list(filter(lambda x: prop["field"] in x.keys(), marc_json["fields"]))
            if len(fields) > 0:
                for field in fields:
                    if prop["subfield"] != "": # extract value at subfield level
                        # check subfields
                        subfields = list(filter(lambda x: prop["subfield"] in x.keys(), field[prop["field"]]["subfields"]))
                        if len(subfields) > 0:
                            for subfield in subfields:
                                # define label, default is value itself
                                try:
                                    label = list(filter(lambda x: prop["retrieve_label_subfield"] in x.keys(), field[prop["field"]]["subfields"]))[0][prop["retrieve_label_subfield"]]
                                except Exception:
                                    label = subfield[prop["subfield"]]

                                if prop["is_biblionumber"]:
                                    # add biblionumber_URI to value
                                    values = [{"value": f"{koha_base_url}{biblio_path_url}{subfield[prop["subfield"]]}", "o:label": label }]
                                elif prop["is_authority"]:
                                    # add authority_URI to value
                                    values = [{"value": f"{koha_base_url}{biblio_path_url}{subfield[prop["subfield"]]}", "o:label": label}]
                                elif prop["is_code"]:
                                    # explicit codes via Wikidata or OmekaS mappings
                                    values = explicit_marc_abbreviation(code=subfield[prop["subfield"]], abbreviation_mapping_name=prop["code_type"])
                                else:
                                    # Literals
                                    if prop["retrieve_label_subfield"] != "":
                                        values = [{"value": subfield[prop["subfield"]], "o:label": label }]
                                    else:
                                        if prop["data_type"] == "Timestamp": # convert Koha / to -
                                            values = [{"value": subfield[prop["subfield"]].replace("/","-")}]
                                        elif prop["data_type"] == "Number": # convert years, cleaning up c. and other elements from the string
                                            values = [{"value": utilities.extract_year(subfield[prop["subfield"]])}]
                                        else:
                                            values = [{"value": subfield[prop["subfield"]]}]

                            # add values to payload according to property
                            if prop["property"] in payload.keys():
                                # append values to existing list
                                payload[prop["property"]].extend(values)
                            else:
                                payload[prop["property"]] = values    

                    else: # extract value directly at the field level
                        if prop["is_biblionumber"]:
                            # add biblionumber_URI to value
                            values = [{"value": f"{koha_base_url}{biblio_path_url}{field[prop["field"]]}", "o:label": field[prop["field"]]}]
                        elif prop["is_authority"]:
                            # add authority_URI to value
                            values = [{"value": f"{koha_base_url}{biblio_path_url}{field[prop["field"]]}", "o:label": field[prop["field"]]}]
                        elif prop["is_code"]:
                            # explicit codes via Wikidata or OmekaS mappings
                            values = explicit_marc_abbreviation(code=field[prop["field"]], abbreviation_mapping_name=prop["code_type"])
                        else:
                            # Literals
                            values = [{"value": field[prop["field"]]}]

                        # add values to payload according to property
                        if prop["property"] in payload.keys():
                            # append values to existing list
                            payload[prop["property"]].extend(values)
                        else:
                            payload[prop["property"]] = values

        else: # the property is not a MARC numeric field, but an item JSON field. Get value from filtered item
            if item is not None:
                payload[prop["property"]] = [{"value": item["field"]}]

    return payload


def explicit_marc_abbreviation_omekas(code: str, abbreviation_mapping_name:str, abbreviations_dir: str ="./data/mappins/abbreviations", multi_code_separator=" ") -> list:
    """
    Returns a lsit of strings, or URIs (Wikidata) or integers (OmekaS item) from MARC code based on abbreviations mappings
    """
    # load abbreviation json 
    abbreviation_mapping = json2dict(os.path.join(abbreviations_dir,f"{abbreviation_mapping_name}.json"))

    # retrieve code value
    results = []
    multi_code = code.split(multi_code_separator)
    for c in multi_code:
        query = list(filter(lambda x: x["code"] == code, abbreviation_mapping))
    if len(query) > 0:
        # return only first matching value
        if "wd_qid" in query.keys():
            if query["wd_label"] != "":
                results.append({"value": f"http://wikidata.org/entity/{query["wd_qid"]}", "o:label": query["wd_label"]})
            else:
                results.append({"value": f"http://wikidata.org/entity/{query["wd_qid"]}", "o:label": query["label"]})
        elif "omekas_id" in query.keys():
            results.append({"o:id":query["omekas_id"]})
        else:
            results.append({"value": query["label"]})

    return results    


def change_item_property_value(
    session: OmekaAPIClient,
    value: str,
    property_name: str,
    resource_id: int,
    resource_type: str,
    value_position: int = 0,
):
    """Change the value of a specific statement of a property of a given resource.
    Args:
        session: `omeka_s_tools` session generated by [pyreslib.omekas.omekas_session].
        value (str): new value for the property.
        property_name (str): name of the property to be updated, such as `dcterms:title`.
        resource_id (int): ID of the item set to be added to the site.
        resource_type (str): Resource type, such as `items`, `item_sets` and `media`.
        value_position (int): position of the value to be change, in case of multiple statements for property. 0 is default.

    Returns:
        None

    """
    data = session.get_resource_by_id(resource_id, resource_type=resource_type)
    data[property_name][value_position]["@value"] = value
    session.update_resource(data, resource_type=resource_type)
