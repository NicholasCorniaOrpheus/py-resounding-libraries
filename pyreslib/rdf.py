"""
This module exports bibliographic and authority records as RDF data structures,
according to a given mapping.
"""

from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, XSD, RDFS
import os
from pyreslib import utilities, koha


def _setup_namespaces(g: Graph, namespaces_filepath: str) -> dict:
    """Load and bind namespaces to the graph.

    Args:
        g (rdflib.Graph): The RDF graph to bind namespaces to.
        namespaces_filepath (str): Path to the namespaces JSON file.

    Returns:
        dict: Dictionary mapping namespace strings to their URIs.
    """
    namespaces = utilities.json2dict(namespaces_filepath)

    for ns in namespaces:
        namespace_prefix = ns["namespace"]
        namespace_uri = Namespace(ns["base_URI"])
        g.bind(namespace_prefix, namespace_uri)

    return {ns["namespace"]: ns["base_URI"] for ns in namespaces}


def _get_namespace_uri(namespace_key: str, namespaces: list) -> str:
    """Get the base URI for a given namespace key.

    Args:
        namespace_key (str): The namespace identifier to look up.
        namespaces (list): List of namespace dictionaries.

    Returns:
        str: The base URI for the namespace.

    Raises:
        ValueError: If namespace not found.
    """
    matching = list(filter(lambda x: x["namespace"] == namespace_key, namespaces))
    if not matching:
        raise ValueError(f"Namespace '{namespace_key}' not found in namespaces file")
    return matching[0]["base_URI"]


def auth_records_to_rdf(
    auth_ids: list,
    session,
    base_url: str,
    koha_namespace: str,
    auth_rdf_mapping_filepath: str = "./data/mappings/lod/koha-rdf_mapping-auth.csv",
    namespaces_filepath: str = "./data/mappings/lod/rdf_namespaces.json",
    output_dir: str = "./data/rdf/auth/",
    serialization_format: str = "turtle",
    explicit_abbreviations: bool = True,
) -> Graph:
    """Convert authority records to RDF graph.

    Given a list of authority IDs, returns an rdflib.Graph object with RDF
    serializations of the authority records according to the provided mapping.

    Args:
        auth_ids (list): List of authority record IDs as integers.
        session (requests.Session): OAuth2 session provided by `koha_session()`.
        base_url (str): Koha API URL from credentials.
        koha_namespace (str): Prefix used for your Koha namespace in the
            namespaces JSON file (e.g., "oikoha"). Omit "auth" suffix.
        auth_rdf_mapping_filepath (str): File path for MARC-to-RDF mapping CSV.
            Default is `./data/mappings/lod/koha-rdf_mapping-auth.csv`.
        namespaces_filepath (str): JSON file with RDF namespaces.
            Default is `./data/mappings/lod/rdf_namespaces.json`.
        output_dir (str): Output directory for RDF files. Files are named
            `{auth_id}.ttl` (or other extension based on format).
            Default is `./data/rdf/auth/`. Set to None to skip file output.
        serialization_format (str): RDF serialization format. Options: "turtle",
            "json-ld", "pretty-xml", "xml". Default is "turtle".
        explicit_abbreviations (bool): Whether to expand MARC abbreviation codes
            using `koha.explicit_abbreviations_from_marc()`. Default is True.

    Returns:
        rdflib.Graph: Combined RDF graph containing all authority records.

    Raises:
        FileNotFoundError: If mapping or namespaces files not found.
        ValueError: If required namespaces not found in namespaces file.

    Examples:
        >>> auth_ids = [1, 342, 17]
        >>> session = koha.koha_session(client_id="...", ...)
        >>> g = auth_records_to_rdf(
        ...     auth_ids=auth_ids,
        ...     session=session,
        ...     base_url="https://koha.example.com/api/v1",
        ...     koha_namespace="oikoha"
        ... )
        >>> g.serialize(format="turtle", destination="authorities.ttl")
    """
    # Initialize main RDF graph
    g = Graph()

    # Load namespaces and bind to main graph
    namespaces = utilities.json2dict(namespaces_filepath)
    namespace_map = _setup_namespaces(g, namespaces_filepath)

    # Load MARC-to-RDF mapping
    auth_rdf_mapping = utilities.csv2dict(auth_rdf_mapping_filepath)

    # Get Koha authority namespace URI
    koha_auth_namespace_key = koha_namespace + "auth"
    koha_auth_base_url = _get_namespace_uri(koha_auth_namespace_key, namespaces)

    # Create output directory if needed
    if output_dir is not None and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Determine file extension
    extension_map = {
        "turtle": ".ttl",
        "json-ld": ".json",
        "pretty-xml": ".xml",
        "xml": ".xml",
    }
    extension = extension_map.get(serialization_format, "")

    for auth_id in auth_ids:
        print(f"Processing authority {auth_id}...")

        # Define subject URI
        subject_uri = URIRef(f"{koha_auth_base_url}{auth_id}")

        # Create graph for this record
        g_record = Graph()

        # Bind all namespaces to this record's graph
        for ns in namespaces:
            g_record.bind(ns["namespace"], Namespace(ns["base_URI"]))

        # Add type statement
        g_record.add((subject_uri, RDF.type, RDFS.Resource))

        try:
            # Fetch authority record from Koha API
            auth = koha.get_authority_marc(
                auth_id=auth_id, session=session, base_url=base_url
            )

            # Expand abbreviations if requested
            if explicit_abbreviations:
                auth = koha.explicit_abbreviations_from_marc(record=auth)

            # Process each mapping rule
            for mapping in auth_rdf_mapping:
                try:
                    field = str(mapping["field"]).zfill(3)
                    subfield = str(mapping.get("subfield", ""))

                    # Get predicate URI
                    namespace_key = mapping.get("namespace", "")
                    property_name = mapping.get("property", "")

                    if not namespace_key or not property_name:
                        continue

                    try:
                        base_uri = _get_namespace_uri(namespace_key, namespaces)
                    except ValueError:
                        print(
                            f"⚠ Warning: Namespace '{namespace_key}' not found, skipping mapping"
                        )
                        continue

                    predicate_uri = URIRef(f"{base_uri}{property_name}")

                    # Find matching MARC fields
                    field_query = list(
                        filter(lambda x: field in x.keys(), auth.get("fields", []))
                    )

                    for field_statement in field_query:
                        # If subfield specified, filter by subfield
                        if subfield:
                            subfield_query = list(
                                filter(
                                    lambda x: subfield in x.keys(),
                                    field_statement[field].get("subfields", []),
                                )
                            )
                        else:
                            # No subfield specified, use all subfields
                            subfield_query = field_statement[field].get("subfields", [])

                        for subfield_statement in subfield_query:
                            # Extract value based on data type
                            value = (
                                subfield_statement.get(subfield)
                                if subfield
                                else subfield_statement
                            )

                            if value is None:
                                continue

                            # Create object based on data type
                            data_type = mapping.get("data_type", "Text")
                            is_authority = mapping.get("is_authority", False)

                            if data_type == "Text":
                                obj = Literal(value, datatype=XSD.string)
                            else:  # URI type
                                if is_authority:
                                    obj = URIRef(f"{koha_auth_base_url}{value}")
                                else:
                                    obj = URIRef(value)

                            # Add statement to graph
                            g_record.add((subject_uri, predicate_uri, obj))

                except KeyError as e:
                    print(f"⚠ Warning: Missing key in mapping: {e}")
                    continue

            # Serialize individual record if output directory specified
            if output_dir is not None:
                output_path = os.path.join(output_dir, f"{auth_id}{extension}")
                g_record.serialize(format=serialization_format, destination=output_path)
                print(f"✓ Saved to {output_path}")

            # Append to main graph
            g += g_record

        except Exception as e:
            print(f"✗ Error processing authority {auth_id}: {e}")
            continue

    print(f"✓ Successfully processed {len(auth_ids)} authorities")
    return g


def biblio_records_to_rdf(
    biblio_ids: list,
    session,
    base_url: str,
    koha_namespace: str,
    biblio_rdf_mapping_filepath: str = "./data/mappings/lod/koha-rdf_mapping-biblio.csv",
    namespaces_filepath: str = "./data/mappings/lod/rdf_namespaces.json",
    output_dir: str = "./data/rdf/biblio/",
    serialization_format: str = "turtle",
    explicit_abbreviations: bool = True,
) -> Graph:
    """Convert bibliographic records to RDF graph.

    Given a list of biblio IDs, returns an rdflib.Graph object with RDF
    serializations of the bibliographic records according to the provided mapping.

    Args:
        biblio_ids (list): List of bibliographic record IDs as integers.
        session (requests.Session): OAuth2 session provided by `koha_session()`.
        base_url (str): Koha API URL from credentials.
        koha_namespace (str): Prefix used for your Koha namespace in the
            namespaces JSON file (e.g., "oikoha"). Omit "biblio"/"auth" suffix.
        biblio_rdf_mapping_filepath (str): File path for MARC-to-RDF mapping CSV.
            Default is `./data/mappings/lod/koha-rdf_mapping-biblio.csv`.
        namespaces_filepath (str): JSON file with RDF namespaces.
            Default is `./data/mappings/lod/rdf_namespaces.json`.
        output_dir (str): Output directory for RDF files. Files are named
            `{biblio_id}.ttl` (or other extension based on format).
            Default is `./data/rdf/biblio/`. Set to None to skip file output.
        serialization_format (str): RDF serialization format. Options: "turtle",
            "json-ld", "pretty-xml", "xml". Default is "turtle".
        explicit_abbreviations (bool): Whether to expand MARC abbreviation codes
            using `koha.explicit_abbreviations_from_marc()`. Default is True.

    Returns:
        rdflib.Graph: Combined RDF graph containing all bibliographic records.

    Raises:
        FileNotFoundError: If mapping or namespaces files not found.
        ValueError: If required namespaces not found in namespaces file.

    Examples:
        >>> biblio_ids = [1, 342, 17]
        >>> koha_session = koha.koha_session(client_id="...", ...)
        >>> g = biblio_records_to_rdf(
        ...     biblio_ids=biblio_ids,
        ...     session=koha_session,
        ...     base_url="https://koha.example.com/api/v1",
        ...     koha_namespace="oikoha"
        ... )
        >>> g.serialize(format="turtle", destination="biblios.ttl")
    """
    # Initialize main RDF graph
    g = Graph()

    # Load namespaces and bind to main graph
    namespaces = utilities.json2dict(namespaces_filepath)
    namespace_map = _setup_namespaces(g, namespaces_filepath)

    # Load MARC-to-RDF mapping
    biblio_rdf_mapping = utilities.csv2dict(biblio_rdf_mapping_filepath)

    # Get Koha namespace URIs
    koha_biblio_namespace_key = koha_namespace + "biblio"
    koha_auth_namespace_key = koha_namespace + "auth"

    koha_biblio_base_url = _get_namespace_uri(koha_biblio_namespace_key, namespaces)
    koha_auth_base_url = _get_namespace_uri(koha_auth_namespace_key, namespaces)

    # Create output directory if needed
    if output_dir is not None and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Determine file extension
    extension_map = {
        "turtle": ".ttl",
        "json-ld": ".json",
        "pretty-xml": ".xml",
        "xml": ".xml",
    }
    extension = extension_map.get(serialization_format, "")

    for biblio_id in biblio_ids:
        print(f"Processing biblio {biblio_id}...")

        # Define subject URI
        subject_uri = URIRef(f"{koha_biblio_base_url}{biblio_id}")

        # Create graph for this record
        g_record = Graph()

        # Bind all namespaces to this record's graph
        for ns in namespaces:
            g_record.bind(ns["namespace"], Namespace(ns["base_URI"]))

        # Add type statement
        g_record.add((subject_uri, RDF.type, RDFS.Resource))

        try:
            # Fetch bibliographic record and items from Koha API
            biblio = koha.get_biblio_marc(
                biblio_id=biblio_id, session=session, base_url=base_url
            )
            biblio_items = koha.get_items_from_biblio_json(
                session=session, base_url=base_url, biblio_id=biblio_id
            )

            # Expand abbreviations if requested
            if explicit_abbreviations:
                biblio = koha.explicit_abbreviations_from_marc(record=biblio)

            # Process each mapping rule
            for mapping in biblio_rdf_mapping:
                try:
                    field = mapping.get("field", "")
                    subfield = str(mapping.get("subfield", ""))

                    # Get predicate URI
                    namespace_key = mapping.get("namespace", "")
                    property_name = mapping.get("property", "")

                    if not namespace_key or not property_name:
                        continue

                    try:
                        base_uri = _get_namespace_uri(namespace_key, namespaces)
                    except ValueError:
                        print(
                            f"⚠ Warning: Namespace '{namespace_key}' not found, skipping mapping"
                        )
                        continue

                    predicate_uri = URIRef(f"{base_uri}{property_name}")

                    # Determine if this is a MARC field or item metadata
                    try:
                        # Try to parse as MARC field (numeric)
                        field_num = str(int(field)).zfill(3)

                        # Find matching MARC fields
                        field_query = list(
                            filter(
                                lambda x: field_num in x.keys(),
                                biblio.get("fields", []),
                            )
                        )

                        for field_statement in field_query:
                            # Filter by subfield if specified
                            if subfield:
                                subfield_query = list(
                                    filter(
                                        lambda x: subfield in x.keys(),
                                        field_statement[field_num].get("subfields", []),
                                    )
                                )
                            else:
                                subfield_query = field_statement[field_num].get(
                                    "subfields", []
                                )

                            for subfield_statement in subfield_query:
                                value = (
                                    subfield_statement.get(subfield)
                                    if subfield
                                    else subfield_statement
                                )

                                if value is None:
                                    continue

                                # Create object based on data type
                                data_type = mapping.get("data_type", "Text")
                                is_authority = mapping.get("is_authority", False)
                                is_biblionumber = mapping.get("is_biblionumber", False)

                                if data_type == "Text":
                                    obj = Literal(value, datatype=XSD.string)
                                else:  # URI type
                                    if is_authority:
                                        obj = URIRef(f"{koha_auth_base_url}{value}")
                                    elif is_biblionumber:
                                        obj = URIRef(f"{koha_biblio_base_url}{value}")
                                    else:
                                        obj = URIRef(value)

                                g_record.add((subject_uri, predicate_uri, obj))

                    except ValueError:
                        # Not a MARC field, try item metadata
                        if biblio_items:
                            for item in biblio_items:
                                value = item.get(field)
                                if value is not None:
                                    obj = Literal(value, datatype=XSD.string)
                                    g_record.add((subject_uri, predicate_uri, obj))

                except Exception as e:
                    print(f"⚠ Warning: Error in mapping {mapping}: {e}")
                    continue

            # Serialize individual record if output directory specified
            if output_dir is not None:
                output_path = os.path.join(output_dir, f"{biblio_id}{extension}")
                g_record.serialize(format=serialization_format, destination=output_path)
                print(f"✓ Saved to {output_path}")

            # Append to main graph
            g += g_record

        except Exception as e:
            print(f"✗ Error processing biblio {biblio_id}: {e}")
            continue

    print(f"✓ Successfully processed {len(biblio_ids)} biblios")
    return g
