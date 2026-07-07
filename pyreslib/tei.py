from pyreslib import transkribus
import os, json
from pathlib import Path
import requests
import xml.etree.ElementTree as ET


def render_region_to_tei(parent_element, reg_data, tag_mapping, ns_uri):
    """
    Apply mapping based on regional tag, changing Namespace.
    """
    xml_el = reg_data["xml_element"]
    custom_attr = xml_el.get("custom", "")

    # Extract tag (e.g., 'heading') from Transkribus 'custom' string
    tag_type = "paragraph"
    if "type:" in custom_attr:
        tag_type = custom_attr.split("type:")[1].split(";")[0]

    # Apply mapping
    mapping = tag_mapping.get(tag_type, {"element": "p"})
    element_name = mapping.get("element")
    attributes = mapping.get("attributes", {}).copy()  # Copy to avoid mutation

    # Create the TEI element
    tei_el = ET.SubElement(parent_element, element_name, attributes)

    # 4. Join all textlines as separate lines (\n)
    ns = {"p": ns_uri}
    unicode_lines = xml_el.findall(".//p:TextLine/p:TextEquiv/p:Unicode", ns)
    text_content = "\n".join([line.text for line in unicode_lines if line.text])
    tei_el.text = text_content


def generate_tei_from_two_column_pagexml(
    page_xml_path: str | Path,
    page_center_method: str = "reference_region",
    reference_type: str = "page-number",
    PAGEXML_NS: str = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15",
    mapping_file: str = "./mappings/pagexml2tei.json",
):
    """
    Get ordered regions according to [pyreslib.transkribus.classify_regions_two_colums][].

    Args:
        page_xml_path (str): Path to local PAGEXML.
        page_center_method(str): Method for two-column separation. Default is "reference-region". See [pyreslib.transkribus.reading_order_region][] for more information.
        reference_type(str): Tag for the region indicating the center. Default is "page-number".
        PAGEXML_NS(str): Transkribus PAGEXML Namespace. Default is http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15.
        mapping_file(str): Path to pagexml2tei.json mapping. Default is `./mappings/pagexml2tei.json`.

    Returns:
        `None`

    """

    print("Getting ordered regions in blocks based on two_column layout...")
    ordered_regions = transkribus.classify_regions_two_colums(
        page_xml_path=page_xml_path,
        page_center_method=page_center_method,
        reference_type=reference_type,
        PAGEXML_NS=PAGEXML_NS,
    )

    # Load the structural mapping
    with open(mapping_file, "r", encoding="utf-8") as f:
        tag_mapping = json.load(f)

    """example of element from ordered region:
    {'id': 'r_18', 'class': 'center', 'y_centroid': 86.5, 'xml_element': <Element '{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion' at 0x7eed1abc1760>, 'block': 1}

    """

    # 0. Initialize new TEI XML structure
    tei_root = ET.Element("TEI", xmlns="http://www.tei-c.org/ns/1.0")
    header = ET.SubElement(tei_root, "teiHeader")
    # ... [Insert minimal header logic here for FAIR compliance] ...

    text_elem = ET.SubElement(tei_root, "text")
    body = ET.SubElement(text_elem, "body")  # <--- Append content HERE, not to tei_root

    # Get ordered regions from your helper
    print("Getting ordered regions in blocks...")
    ordered_regions = transkribus.classify_regions_two_colums(
        page_xml_path=page_xml_path,
        page_center_method=page_center_method,
        reference_type=reference_type,
        PAGEXML_NS=PAGEXML_NS,
    )

    # 1. Organize sublists for each block
    blocks = {}
    for reg in ordered_regions:
        b_id = reg["block"]
        if b_id not in blocks:
            blocks[b_id] = []
        blocks[b_id].append(reg)

    # Process blocks in numerical order
    for b_id in sorted(blocks.keys()):
        block_elements = blocks[b_id]

        # 2. Block structure logic
        if len(block_elements) == 1:
            # Single element -> Render directly to body to maintain sequence
            # Pass block_elements (the dict), not the list itself
            render_region_to_tei(body, block_elements[0], tag_mapping, PAGEXML_NS)
        else:
            # Multi-element block -> Use <cb/> milestones for TEI conformance
            # Create a section wrapper to keep the block's columns together
            section_div = ET.SubElement(
                body, "div", {"type": "section", "n": str(b_id)}
            )

            # Group by class
            left = [r for r in block_elements if r["class"] == "left"]
            right = [r for r in block_elements if r["class"] == "right"]
            center = [r for r in block_elements if r["class"] == "center"]

            # Render center (headers) first, then columns
            for reg in center:
                render_region_to_tei(section_div, reg, tag_mapping, PAGEXML_NS)

            if left or right:
                ET.SubElement(section_div, "cb", {"n": "1"})
                for reg in left:
                    render_region_to_tei(section_div, reg, tag_mapping, PAGEXML_NS)

                if right:
                    ET.SubElement(section_div, "cb", {"n": "2"})
                    for reg in right:
                        render_region_to_tei(section_div, reg, tag_mapping, PAGEXML_NS)

    # 4. Save output using Path.with_suffix for robustness [General Python Knowledge]
    output_path = Path(page_xml_path).with_suffix(".tei")
    tree = ET.ElementTree(tei_root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ TEI saved in document order: {output_path}")


def document_pagexml2tei(
    document_dir: str | Path,
    page_center_method: str = "reference_region",
    reference_type: str = "page-number",
    PAGEXML_NS: str = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15",
    mapping_file: str = "./mappings/pagexml2tei.json",
):
    """
    Generates TEI files for each PAGEXML in document_dir.

    Args:
        document_dir (str): Path to local PAGEXML directory to be converted.
        page_center_method(str): Method for two-column separation. Default is "reference-region". See [pyreslib.transkribus.reading_order_region][] for more information.
        reference_type(str): Tag for the region indicating the center. Default is "page-number".
        PAGEXML_NS(str): Transkribus PAGEXML Namespace. Default is http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15.
        mapping_file(str): Path to pagexml2tei.json mapping. Default is `./mappings/pagexml2tei.json`.

    Returns:
        `None`


    """
    document_path = Path(document_dir)

    for f in document_path.iterdir():
        if f.name.endswith(".xml"):
            generate_tei_from_two_column_pagexml(
                page_xml_path=f,
                page_center_method=page_center_method,
                reference_type=reference_type,
                PAGEXML_NS=PAGEXML_NS,
                mapping_file=mapping_file,
            )
