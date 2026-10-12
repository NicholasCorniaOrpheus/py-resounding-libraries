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
    omeka_session: OmekaAPIClient,
    koha_session,
    koha_api_base_url: str,
    koha_base_url: str,
    omekas_mapping: dict,
    resource_template_id: int,
    update_existing: bool = False,
    authority_path_url: str = "cgi-bin/koha/authorities/detail.pl?authid=",
    biblio_path_url: str = "cgi-bin/koha/catalogue/detail.pl?biblionumber=",
    OMEKA_SYSTEM_KEYS: dict = {
                    '@context', '@id', '@type', 'o:id', 'o:is_public', 'o:owner', 
                    'o:resource_class', 'o:resource_template', 'o:thumbnail', 'thumbnail_display_urls', 'o:primary_media', 'o:media', 'o:item_set',
                    'o:created', 'o:modified','o:title', 'o:site','@reverse','o-access:status','o-module-group:group'
                }
):
    """
    Imports Koha authorities based on an existing public report as Omeka S items of the same resource template type.

    Args:
        koha_report_id (int): Koha public report ID.
        koha_public_report_url (str): Koha public report URL.
        omeka_session (OmekaAPIClient): Omeka S session.
        omekas_mapping (dict): Omeka S mapping dictionary.
        resource_template_name (str): Omeka S resource template name.
        update_existing(bool): If set to True, it will update missing statements from the item, based on Koha metadata. Default is False.
        OMEKAS_SYSTEM_KEYS(dict): Set of system keys excluded from the update of existing resources.
    """

    resource_mapping = omekas_mapping[str(resource_template_id)]

    print("Loading resource mapping based on template ID...")
    #print(resource_mapping)
    #input()

    koha_authorities = koha.get_ids_list_from_koha_public_report(session=koha_session,koha_public_report_url=koha_public_report_url,koha_report_id=koha_report_id)

    print("Retrieving authority IDs from Koha Public Report...")
    print(koha_authorities)
    input()

    for auth in koha_authorities:
        print(f"Current authority: {auth} \n")
        # extract metadata from Koha API
        auth_metadata = koha.get_authority_marc(
            session=koha_session, auth_id=int(auth), base_url=koha_api_base_url
        )
        print("Getting record metadata from Koha API...")
        #print(auth_metadata)
        #input()
        # Lookup for existing Omeka S item using koha_authority_base_url+auth_id
        search_results = omeka_session.filter_items_by_property(
            filter_property="dcterms:identifier",
            filter_value=f"{koha_base_url}{authority_path_url}{str(auth)}",
            filter_type="eq",
        )
        #print(search_results["results"])
        #input()
        if search_results["total_results"] > 0:
            print(f"Authority {auth} already exists in Omeka S:")
            print(search_results["results"][0]["@id"])
            print(search_results["results"][0]["o:title"])
            if update_existing: # add missing metadata and update item
                # generate payload
                payload = generate_omekas_payload_from_marc_in_json(
                            marc_json=auth_metadata, 
                            record_id=int(auth), 
                            omekas_mapping=omekas_mapping, 
                            resource_template_id=resource_template_id,
                            koha_session=koha_session,
                            koha_api_base_url=koha_api_base_url,
                            koha_base_url=koha_base_url)
                
                prep_payload = prepare_omekas_payload_from_template_with_labels(
                    session=omeka_session,
                    payload=payload,
                    template_id=resource_template_id)

                # compare prep_payload with existing one, and add missing statements.
                existing_payload = search_results["results"][0]
                payload_was_updated = False

                for key in prep_payload.keys():
                    for statement in prep_payload[key]:
                        if key in OMEKA_SYSTEM_KEYS:
                            continue # Skip system keys
                        else: 
                            # search if statement appears in existing_payload. Use only core value for comparison
                            new_val = (statement.get('@value') or statement.get('@id')).strip()
                            try:
                                # Extract core values from the existing items to compare cleanly
                                existing_vals = [
                                    item.get('@value') or item.get('@id') 
                                    for item in existing_payload[key]
                                ]
                                
                                if new_val in existing_vals:
                                    continue # Core value already exists, skip it!
                                else:
                                    existing_payload[key].append(statement)
                                    payload_was_updated = True
                                    
                            except KeyError: # If the property isn't present yet
                                existing_payload[key] = [statement]
                                payload_was_updated = True

                if payload_was_updated:
                    print(f"Updating payload for {auth}...")
                    try:
                        omeka_session.update_resource(existing_payload)
                    except Exception as e:
                        print("--- CRITICAL PAYLOAD ERROR ---")
                        print(json.dumps(existing_payload, indent=2))
                        
                        # If the response has a body, Omeka S sometimes returns a JSON error tracking text
                        if hasattr(e, 'response') and e.response is not None:
                            print("Server Response Text:", e.response.text)
                        raise e               
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
                        koha_session=koha_session,
                        koha_api_base_url=koha_api_base_url,
                        koha_base_url=koha_base_url)
            #print(payload)
            #input()
            prep_payload = prepare_omekas_payload_from_template_with_labels(
                session=omeka_session,
                payload=payload,
                template_id=resource_template_id)
            # Native function from omekas_tools does not take into accounts label!
            # prep_payload = omeka_session.prepare_item_payload_using_template(
            #     payload, template_id=resource_template_id
            # )
            print(prep_payload)
            #input()

            # create new item using resource template
            print("Adding item to OmekaS...")
            input()
            try:
                omeka_session.add_item(prep_payload, template_id=resource_template_id)
            except Exception as e:
                print("--- CRITICAL PAYLOAD ERROR ---")
                print(json.dumps(prep_payload, indent=2))
                
                # If the response has a body, Omeka S sometimes returns a JSON error tracking text
                if hasattr(e, 'response') and e.response is not None:
                    print("Server Response Text:", e.response.text)
                raise e


def import_koha_biblios_to_omekas_from_report(
    koha_report_id: int,
    koha_public_report_url: str,
    omeka_session: OmekaAPIClient,
    koha_session,
    koha_api_base_url: str,
    koha_base_url: str,
    omekas_mapping: dict,
    resource_template_id: int,
    update_existing: bool = False,
    authority_path_url: str = "cgi-bin/koha/authorities/detail.pl?authid=",
    biblio_path_url: str = "cgi-bin/koha/catalogue/detail.pl?biblionumber=",
    OMEKA_SYSTEM_KEYS: dict = {
                    '@context', '@id', '@type', 'o:id', 'o:is_public', 'o:owner', 
                    'o:resource_class', 'o:resource_template', 'o:thumbnail', 'thumbnail_display_urls', 'o:primary_media', 'o:media', 'o:item_set',
                    'o:created', 'o:modified','o:title', 'o:site','@reverse','o-access:status','o-module-group:group'
                },
    resource_classes_mapping: dict = {
        "REC": "bibo:AudioVisualDocument",
        "BOO": "bibo:Book",
        "CHA": "bibo:BookSection",
        "DIS": "bibo:Thesis",
        "ART": "bibo:Article",
        "SCO": 'bf:NotatedMusic',
        "NWO": "bibo:Event",
        "DAT": "dctype:Dataset",
    },
    koha_record_type: str = "942$c"
):
    """
    Imports Koha biblios based on an existing public report as Omeka S items of the same resource template type.

    Args:
        koha_report_id (int): Koha public report ID.
        koha_public_report_url (str): Koha public report URL.
        omeka_session (OmekaAPIClient): Omeka S session.
        omekas_mapping (dict): Omeka S mapping dictionary.
        resource_template_name (str): Omeka S resource template name.
        update_existing(bool): If set to True, it will update missing statements from the item, based on Koha metadata. Default is False.
        OMEKAS_SYSTEM_KEYS(dict): Set of system keys excluded from the update of existing resources.
    """

    resource_mapping = omekas_mapping[str(resource_template_id)]

    print("Loading resource mapping based on template ID...")

    koha_biblios = koha.get_ids_list_from_koha_public_report(session=koha_session,koha_public_report_url=koha_public_report_url,koha_report_id=koha_report_id)

    print(f"Retrieving {len(koha_biblios)} biblio IDs from Koha Public Report...")
    #print(koha_biblios)
    #input()

    for biblio in koha_biblios:
        print(f"Current biblio: {biblio} \n")
        # extract metadata from Koha API
        biblio_metadata = koha.get_biblio_marc(
            session=koha_session, biblio_id=int(biblio), base_url=koha_api_base_url
        )
        print("Getting record metadata from Koha API...")
        #print(biblio_metadata)
        #input()
        # Lookup for existing Omeka S item using koha_authority_base_url+biblio_id
        search_results = omeka_session.filter_items_by_property(
            filter_property="dcterms:identifier",
            filter_value=f"{koha_base_url}{biblio_path_url}{str(biblio)}",
            filter_type="eq",
        )
        #print(search_results["results"])
        #input()
        if search_results["total_results"] > 0:
            print(f"Record {biblio} already exists in Omeka S:")
            #print(search_results["results"][0]["@id"])
            #print(search_results["results"][0]["o:title"])
            if update_existing: # add missing metadata and update item
                # generate payload
                payload = generate_omekas_payload_from_marc_in_json(
                            marc_json=biblio_metadata, 
                            record_id=int(biblio), 
                            omekas_mapping=omekas_mapping, 
                            resource_template_id=resource_template_id,
                            koha_session=koha_session,
                            koha_api_base_url=koha_api_base_url,
                            koha_base_url=koha_base_url)
                
                prep_payload = prepare_omekas_payload_from_template_with_labels(
                    session=omeka_session,
                    payload=payload,
                    template_id=resource_template_id)

                # compare prep_payload with existing one, and add missing statements.
                existing_payload = search_results["results"][0]
                payload_was_updated = False

                for key in prep_payload.keys():
                    for statement in prep_payload[key]:
                        if key in OMEKA_SYSTEM_KEYS:
                            continue # Skip system keys
                        else: 
                            # search if statement appears in existing_payload. Use only core value for comparison
                            new_val = (statement.get('@value') or statement.get('@id')).strip()
                            try:
                                # Extract core values from the existing items to compare cleanly
                                existing_vals = [
                                    item.get('@value') or item.get('@id') 
                                    for item in existing_payload[key]
                                ]
                                
                                if new_val in existing_vals:
                                    continue # Core value already exists, skip it!
                                else:
                                    existing_payload[key].append(statement)
                                    payload_was_updated = True
                                    
                            except KeyError: # If the property isn't present yet
                                existing_payload[key] = [statement]
                                payload_was_updated = True

                if payload_was_updated:
                    print(f"Updating payload for {biblio}...")
                    #input()
                    try:
                        # removing group statement, causing errors.
                        if "o-module-group:group" in existing_payload:
                            del existing_payload["o-module-group:group"]

                        omeka_session.update_resource(existing_payload)

                    except Exception as e:
                        print("--- CRITICAL PAYLOAD ERROR ---")
                        #print(json.dumps(existing_payload, indent=2))
                        
                        # If the response has a body, Omeka S sometimes returns a JSON error tracking text
                        if hasattr(e, 'response') and e.response is not None:
                            print("Server Response Text:", e.response.text)
                        raise e

                # update resource class using koha2omekas mapping
                koha_type = list(filter(lambda x: str(koha_record_type.split("$")[0]) in x.keys(), biblio_metadata["fields"]))[0][koha_record_type.split("$")[0]]["subfields"][0][koha_record_type.split("$")[1]]
                resource_class = resource_classes_mapping[koha_type]

                resource_class_dict = omeka_session.get_resource_by_term(
                        resource_class, "resource_classes"
                    )

                if existing_payload["o:resource_class"]["o:id"] != resource_class_dict["o:id"]:
                    existing_payload["o:resource_class"] = {
                            "@id": resource_class_dict["@id"],
                            "o:id": resource_class_dict["o:id"]
                        }

                    # updating payload using update
                    print("Updating class value...")
                    omeka_session.update_resource(existing_payload)               
        else:
            print(
                f"Record {biblio} is missing. Creating new item according to resource_template"
            )
            # generate payload
            payload = generate_omekas_payload_from_marc_in_json(
                        marc_json=biblio_metadata, 
                        record_id=int(biblio), 
                        omekas_mapping=omekas_mapping, 
                        resource_template_id=resource_template_id,
                        koha_session=koha_session,
                        koha_api_base_url=koha_api_base_url,
                        koha_base_url=koha_base_url)

            prep_payload = prepare_omekas_payload_from_template_with_labels(
                session=omeka_session,
                payload=payload,
                template_id=resource_template_id)


            #print(prep_payload)
            #input()

            # create new item using resource template
            print("Adding item to OmekaS... press Enter to continue...")
            #input()
            try:
                new_item = omeka_session.add_item(prep_payload, template_id=resource_template_id)

                print(f"Resource ID for new item: {new_item.get("o:id")}")

                # add resource class using koha2omekas mapping
                #print("Updating class value...")
                koha_type = list(filter(lambda x: str(koha_record_type.split("$")[0]) in x.keys(), biblio_metadata["fields"]))[0][koha_record_type.split("$")[0]]["subfields"][0][koha_record_type.split("$")[1]]
                resource_class = resource_classes_mapping[koha_type]

                resource_class_dict = omeka_session.get_resource_by_term(
                        resource_class, "resource_classes"
                    )

                new_item["o:resource_class"] = {
                        "@id": resource_class_dict["@id"],
                        "o:id": resource_class_dict["o:id"]
                    }

                # updating payload using update

                omeka_session.update_resource(new_item)



            except Exception as e:
                print("--- CRITICAL PAYLOAD ERROR ---")
                #print(json.dumps(prep_payload, indent=2))
                
                # If the response has a body, Omeka S sometimes returns a JSON error tracking text
                if hasattr(e, 'response') and e.response is not None:
                    print("Server Response Text:", e.response.text)
                raise e

def change_item_resource_class(
    session: OmekaAPIClient,
    resource_id: int,
    new_resource_class_term: str,
):
    """
    Change the resource class of an existing item.
    Requires direct API call because o:resource_class is a system key.
    """
    resource_class_dict = session.get_resource_by_term(
        new_resource_class_term, "resource_classes"
    )
    
    # Prepare update payload with only system-level fields
    update_payload = {
        "o:resource_class": {
            "@id": resource_class_dict["@id"],
            "o:id": resource_class_dict["o:id"]
        },
        "@type": ["o:Item", new_resource_class_term]
    }
    
    session.update_resource(update_payload)


def generate_omekas_payload_from_marc_in_json(
    marc_json: dict, 
    record_id: int, 
    omekas_mapping: dict, 
    resource_template_id: int,
    koha_session,
    koha_api_base_url: str,
    koha_base_url: str,
    item_identifier: str = None,
    item_identifier_field: str = "external_id",
    authority_path_url: str = "cgi-bin/koha/authorities/detail.pl?authid=",
    biblio_path_url: str = "cgi-bin/koha/catalogue/detail.pl?biblionumber=",
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
            # making sure the field value has zfill(3)
            field_value = prop["field"].zfill(3)
            # filter field value using lambda filter
            fields = list(filter(lambda x: field_value in x.keys(), marc_json["fields"]))
            if len(fields) > 0:
                for field in fields:
                    if prop["subfield"] != "": # extract value at subfield level
                        # check subfields
                        subfields = list(filter(lambda x: prop["subfield"] in x.keys(), field[field_value]["subfields"]))
                        if len(subfields) > 0:
                            for subfield in subfields:
                                # define label, default is value itself
                                try:
                                    label = list(filter(lambda x: prop["retrieve_label_subfield"] in x.keys(), field[field_value]["subfields"]))[0][prop["retrieve_label_subfield"]]
                                except Exception:
                                    label = subfield[prop["subfield"]]

                                if prop["is_biblionumber"]:
                                    # add biblionumber_URI to value
                                    values = [{"type": "uri", "value": f"{koha_base_url}{biblio_path_url}{subfield[prop["subfield"]]}", "o:label": label }]
                                elif prop["is_authority"]:
                                    # add authority_URI to value
                                    values = [{"type": "uri", "value": f"{koha_base_url}{authority_path_url}{subfield[prop["subfield"]]}", "o:label": label}]
                                elif prop["is_code"]:
                                    # explicit codes via Wikidata or OmekaS mappings
                                    values = explicit_marc_abbreviation_omekas(code=subfield[prop["subfield"]], abbreviation_mapping_name=prop["code_type"])
                                else:
                                    # Literals
                                    if prop["retrieve_label_subfield"] != "":
                                        values = [{"value": subfield[prop["subfield"]], "o:label": label }]
                                    else:
                                        if prop["data_type"] == "Timestamp": # convert Koha / to -
                                            values = [{"value": subfield[prop["subfield"]].replace("/","-")}]
                                        elif prop["data_type"] == "Number": # convert years, cleaning up c. and other elements from the string
                                            values = [{"value": str(utilities.extract_year(subfield[prop["subfield"]]))}]
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
                            values = [{"type": "uri", "value": f"{koha_base_url}{biblio_path_url}{field[field_value]}", "o:label": field[field_value]}]
                        elif prop["is_authority"]:
                            # add authority_URI to value
                            values = [{"type": "uri", "value": f"{koha_base_url}{biblio_path_url}{field[field_value]}", "o:label": field[field_value]}]
                        elif prop["is_code"]:
                            # explicit codes via Wikidata or OmekaS mappings
                            values = explicit_marc_abbreviation_omekas(code=field[prop["field"]], abbreviation_mapping_name=prop["code_type"])
                        else:
                            # Literals
                            values = [{"value": str(field[field_value])}]

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


def prepare_omekas_payload_from_template_with_labels(
    session: OmekaAPIClient,
    payload: dict,
    template_id: int) -> dict :
    
    """
    Improves the omekas_tools [prepare_item_payload_using_template](https://wragge.github.io/omeka_s_tools/api.html#OmekaAPIClient.prepare_item_payload_using_template) method including labels for URI fields.
    """
    # 1. Let omeka_s_tools map the property IDs, types, and values based on the template
    processed_payload = session.prepare_item_payload_using_template(payload,template_id)
    
    # 2. Re-inject the lost 'o:label' fields back into the output payload
    for term, values in payload.items():
        # Skip top-level system fields like resource template
        if term.startswith('o:') or term not in processed_payload:
            continue
            
        for i, original_item in enumerate(values):
            # If the original input had an o:label, copy it to the mapped payload
            if isinstance(original_item, dict) and 'o:label' in original_item:
                if i < len(processed_payload[term]):
                    processed_payload[term][i]['o:label'] = original_item['o:label']
                    
    return processed_payload




def explicit_marc_abbreviation_omekas(code: str, abbreviation_mapping_name:str, abbreviations_dir: str ="./data/mappings/abbreviations", multi_code_separator=" ") -> list:
    """
    Returns a lsit of strings, or URIs (Wikidata) or integers (OmekaS item) from MARC code based on abbreviations mappings
    """
    # load abbreviation json 
    abbreviation_mapping = utilities.json2dict(os.path.join(abbreviations_dir,f"{abbreviation_mapping_name}.json"))

    # retrieve code value
    results = []
    multi_code = code.split(multi_code_separator)
    for c in multi_code:
        query = list(filter(lambda x: x["code"] == c, abbreviation_mapping))
    if len(query) > 0:
        # return only first matching value
        if "wd_qid" in query[0].keys():
            if query[0]["wd_label"] != "":
                results.append({"type": "uri", "value": f"http://wikidata.org/entity/{query[0]["wd_qid"]}", "o:label": query[0]["wd_label"]})
            else:
                results.append({"type": "uri", "value": f"http://wikidata.org/entity/{query[0]["wd_qid"]}", "o:label": query[0]["label"]})
        elif "omekas_id" in query[0].keys():
            results.append({"o:id":query[0]["omekas_id"]})
        else:
            results.append({"value": query[0]["label"]})
    else:
        print(f"Warning: No mapping found for code '{c}' in {abbreviation_mapping_name}")

    return results    


def substitute_URIs_to_omekas_items(
    session: OmekaAPIClient,
    uri_base_url: str,
    uri_property_identifier: str = "dcterms:identifier",
    OMEKA_SYSTEM_KEYS: dict = {
                    '@context', '@id', '@type', 'o:id', 'o:is_public', 'o:owner', 
                    'o:resource_class', 'o:resource_template', 'o:thumbnail', 'thumbnail_display_urls', 'o:primary_media', 'o:media', 'o:item_set',
                    'o:created', 'o:modified','o:title', 'o:site','@reverse','o-access:status','o-module-group:group'
                }):

    """
    Converts, when possible, all URI statements with a given uri_base_url into corresponding 
    Omeka S items with matching uri_property_identifier value.
    """

    # Fetch page 1 to see how many total results exist
    current_page = 1
    query_items = session.get_resources('items', page=current_page)
    total_results = query_items.get("total_results", 0)
    print(f"Retrieved total of {total_results} items across multiple pages from Omeka S")

    changed_items = 0

    # Continue loop as long as the page contains results
    while query_items and "results" in query_items and len(query_items["results"]) > 0:
        items = query_items["results"]
        print(f"\n--- SCANNING PAGE {current_page} ({len(items)} items)")


        for item in items:
            changed_item = False
            print(f"Current item: {item["@id"]}")
            for key in item.keys():
                key_changed = False
                if key not in OMEKA_SYSTEM_KEYS and key != uri_property_identifier:
                    for idx, statement in enumerate(item[key]):
                        try:
                            if statement["type"] == "uri":
                                if uri_base_url in statement["@id"]:
                                    #print(f"Processing current statement: \n {statement}")
                                    # search for item with corresponding URI in Omeka S
                                    query = session.filter_items_by_property(
                                            filter_property=uri_property_identifier,
                                            filter_value=statement["@id"],
                                            filter_type="eq",
                                        )

                                    if query["total_results"] > 0:
                                        #print(f"Found matching item candidate for statement.")
                                        matching_item = query["results"][0]
                                        #print(matching_item["@id"])
                                        #print(matching_item["o:title"])
                                        # DEFENSIVE FIX: Safely parse thumbnails without crashing
                                        thumbnail_url = None
                                        raw_thumbnails = matching_item.get("thumbnail_display_urls")
                                        if isinstance(raw_thumbnails, dict):
                                            thumbnail_url = raw_thumbnails.get("square")
                                        # substitute statement value for item
                                        item[key][idx] = {
                                            "type": "resource:item",
                                            "property_id": statement.get("property_id"),
                                            "property_label": statement.get("property_label"),
                                            "is_public": statement.get("is_public"),
                                            "@id": matching_item["@id"],
                                            "value_resource_id": matching_item["o:id"],
                                            "value_resource_name": "items",
                                            "url": None,
                                            "display_title": matching_item["o:title"],
                                            "thumbnail_url": thumbnail_url,
                                        }
                                        key_changed = True
                                        changed_item = True
                        except Exception as e:
                            print(f"!!! Hidden exception caught in key '{key}': {e}")
                            continue

                    # remove duplicate items based on @id value
                    if key_changed:
                        seen_ids = set()
                        unique_list = []
                        for d in item[key]:
                            try:
                                if d["@id"] not in seen_ids:
                                    seen_ids.add(d["@id"])
                                    unique_list.append(d)
                            except KeyError: #ignore statements without @id
                                unique_list.append(d)

                        item[key] = unique_list

            if changed_item:
                #upload the item back to Omeka S
                print(f"Item {item["@id"]} has been changed.")
                #input()
                try:
                    # --- BYPASS GROUP PLUGIN PREG_MATCH BUG ---
                    # Remove the group property entirely from this specific payload.
                    # Omeka will update metadata statements but leave current item groups unchanged.
                    if "o-module-group:group" in item:
                        del item["o-module-group:group"]
                    session.update_resource(item)
                    changed_items += 1
                except Exception as e:
                    print("--- CRITICAL PAYLOAD ERROR ---")
                    #print(json.dumps(item, indent=2))
                    
                    # If the response has a body, Omeka S sometimes returns a JSON error tracking text
                    if hasattr(e, 'response') and e.response is not None:
                        print("Server Response Text:", e.response.text)
                    raise e 
            
        # Advance pagination step and fetch the next chunk of database assets
        current_page += 1
        query_items = session.get_resources('items', page=current_page)    

    
    print(f"Successfully updated {changed_items} items.")   









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
        resource_id (int): ID of the item.
        resource_type (str): Resource type, such as `items`, `item_sets` and `media`.
        value_position (int): position of the value to be change, in case of multiple statements for property. 0 is default.

    Returns:
        None

    """
    data = session.get_resource_by_id(resource_id, resource_type=resource_type)
    data[property_name][value_position]["@value"] = value
    session.update_resource(data, resource_type=resource_type)
