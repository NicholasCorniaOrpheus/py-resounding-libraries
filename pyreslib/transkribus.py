import requests
import urllib
import xml.etree.ElementTree as ET
import os, json
from pathlib import Path
from shapely.geometry import Polygon
from pyreslib import koha


### TO-DO
"""
1. Conversion option for PAGEXML format, such TEIXML.
2. Authorities spotting via Fuzzy Search in trascribed text

"""


def api_login(user: str, password: str):
    """
    Args:
                                                                    user (user): Client Username
                                                                    password (str): Client secret Password
    Returns:
                                                                    session: requests.Session() for Transkribus API
    """
    session = requests.Session()
    response = session.post(
        "https://transkribus.eu/TrpServer/rest/auth/login",
        data={"user": user, "pw": password},
    )
    if response.status_code == requests.codes.ok:
        return session
    else:
        print(r)
        print("Login failed.")
        return None


def get_documents_metadata(session, collection_id: int) -> list:
    """
    Returns a full dictionary of documents, including pages metadata.

    Args:
                                                                    session: Transkribus session from `pyreslib.transkribus.api_login()` method.
                                                                    collection_id (int): Collection ID identifier from Transkribus.

    Returns:
                                                                    documents (list): List of documents, with metadata and pagelist.

    Examples:

                                                                    >>> session = pyreslib.transkribus.api_login(user,password)
                                                                    >>> documents = pyreslib.transkribus.get_documents_metadata(session,collection_id=2792)
                                                                    >>> [{"md": {...}, "pageList": {"pages":[...]},"collection": {...}, ... }]
    """
    headers = {"Accept": "application/json"}
    collection = session.get(
        f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/list",
        headers=headers,
    ).json()

    documents_metadata = []

    for document in collection:
        document = session.get(
            f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document['docId']}/fulldoc",
            headers=headers,
        )

        documents_metadata.append(document.json())

    return documents_metadata


def get_document_metadata(session, collection_id: int, document_id: int) -> dict:
    """
    Returns a document metadata from Transkribus API

    Args:
                                                                    session: Transkribus session from `pyreslib.transkribus.api_login()` method.
                                                                    collection_id (int): Collection ID identifier from Transkribus.
                                                                    document_id (int): Document ID identifier from Transkribus.


    Returns:
                                                                    document (dict): Document metadata

    Examples:

                                                                    >>> session = pyreslib.transkribus.api_login(user,password)
                                                                    >>> document = pyreslib.transkribus.get_document_metadata(session,collection_id=2792,document_id=16606356)
                                                                    >>> {"md": {...}, "pageList": {"pages":[...]}, ... }
    """

    # Get document metadata
    headers = {"Accept": "application/json"}
    document = session.get(
        f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/fulldoc",
        headers=headers,
    ).json()

    return document


# # NOT WORKING problem with status URL.
# def get_alto_xml_via_export(session, collection_id: int, document_id: int, page_number: int) -> str:
# 	"""
# 	Triggers a document export job on Transkribus to extract a page's ALTO XML string.
# 	"""
# 	# 1. Trigger the export via POST using the exact parameter from the WADL
# 	export_url = f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/export"

# 	# Configure the query parameters as defined in the WADL schema
# 	params = {
# 		"doExportPageXml": "false",       # We only want ALTO
# 		"doExportAltoXml": "true",        # The target WADL parameter
# 		"pages": str(page_number)         # Restrict export to only our target page
# 	}

# 	print(f"Triggering export job for Collection {collection_id}, Doc {document_id}, Page {page_number}...")
# 	# This must be a POST request according to the WADL specification
# 	response = session.post(export_url, params=params)
# 	response.raise_for_status()

# 	# 2. Extract the Job ID from the XML response metadata
# 	# The response is a job status structural element containing an <jobId> tag
# 	job_id = response.text.strip()
# 	print(f"Export Job initialized. Job ID: {job_id}")

# 	# 3. Poll the job status endpoint until processing completes
# 	status_url = f"https://transkribus.eu/TrpServer/rest/jobs/{job_id}"

# 	while True:
# 		status_response = session.get(status_url)
# 		status_response.raise_for_status()

# 		status_root = ET.fromstring(status_response.text)
# 		current_status = status_root.find('status').text
# 		print(f"Current Job Status: {current_status}")

# 		if current_status == "FINISHED":
# 			# The download URL is stored inside the <exportUrl> element
# 			download_url = status_root.find('exportUrl').text
# 			break
# 		elif current_status in ["FAILED", "CANCELED"]:
# 			raise RuntimeError(f"Transkribus export job {job_id} terminated unexpectedly: {current_status}")

# 		time.sleep(2)  # Wait 2 seconds before checking again

# 	# 4. Download and extract the ALTO XML file from the ZIP archive stream
# 	print("Downloading processed ZIP payload...")
# 	zip_response = session.get(download_url)
# 	zip_response.raise_for_status()

# 	# Read the archive straight out of memory
# 	with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
# 		# Find any file ending with .xml inside the archive
# 		xml_files = [f for f in z.namelist() if f.endswith('.xml')]
# 		if not xml_files:
# 			raise FileNotFoundError("No ALTO XML structures were found inside the generated archive.")

# 		# Read the file text stream content directly
# 		with z.open(xml_files[0]) as f:
# 			return f.read().decode('utf-8')


def get_page_xml(
    session, collection_id: int, document_id: int, page_number: int
) -> str:
    """
    Retrieves the PAGEXML transcription of a given page of a document as string.

    Args:
                                                                    session: Transkribus session from `pyreslib.transkribus.api_login()` method.
                                                                    collection_id (int): Collection ID identifier from Transkribus.
                                                                    document_id (int): Document ID identifier from Transkribus.
                                                                    page_number (int): Internal page number identifier from Transkribus.

    Returns:
                                                                    page_xml (str): string serialization of the PAGEXML transcription of the page by Transkribus. You can parse it later by usin `xml.etree.ElementTree.fromstring()` method.

    Examples:
                                                                    >>> import xml.etree.ElementTree as ET
                                                                    >>> session = pyreslib.transkribus.api_login(user,password)
                                                                    >>> page_xml = pyreslib.transkribus.get_page_xml(session,collection_id=2792,document_id=145869,page_number=14)
                                                                    >>> root = ET.fromstring(page_xml)
    """

    headers = {"Accept": "application/xml"}
    page_xml = session.get(
        f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/{page_number}/text",
        headers=headers,
    )

    if page_xml.status_code in [200, 201]:
        pass
    else:
        print(f"Failed with Status Code: {page_xml.status_code}")
        print(f"Server Response: {page_xml.text}")

    return str(page_xml.text).encode("utf-8")


def get_jpg_image(
    session, collection_id: int, document_id: int, page_number: int, output_dir: str
):
    """
    Extract the JPG image of a given page from Transkribus API

    Args:
            session (): Transkribus session from `pyreslib.transkribus.api_login()` method.
            collection_id (int): Collection ID identifier from Transkribus.
            document_id (int): Document ID identifier from Transkribus.
            page_number (int): Internal page number identifier from Transkribus.
            output_dir (str): local directory for download. The filename is equal to the one stored in Transkribus metadata.

    Returns:
            `None`

    Examples:
            >>> session = pyreslib.transkribus.api_login(user,password)
            >>> output_filepath = f"./data/kraken/transcriptions/{str(document_id)}"
            >>> get_jpg_image(session,collection_id=2792,document_id=145869,page_number=14,output_dir=output_dir)
    """

    # Get document metadata
    document = get_document_metadata(
        session=session, collection_id=collection_id, document_id=document_id
    )

    # Find page metadata
    page_metadata = list(
        filter(lambda x: x["pageNr"] == page_number, document["pageList"]["pages"])
    )
    if len(page_metadata) > 0:
        output_filepath = os.path.join(output_dir, page_metadata[0]["imgFileName"])
        # page found, get image URL
        image_url = page_metadata[0]["url"]
        urllib.request.urlretrieve(image_url, output_filepath)
    else:
        print(f"Page not found for {document_id}/{page_number}")

    return None


def import_jpg_from_document(
    session, collection_id: int, document_id: int, output_dir: str | Path
):
    """
    Downloads JPG images from transkribus, giving them the same basename. as the page filename.
    Args:
            session(requests.Session): Transkribus session from `pyreslib.transkribus.api_login()` method.
            collection_id (int): Collection ID identifier from Transkribus.
            document_id (int): Document ID identifier from Transkribus.
            output_dir(str | Path): Directory path for JPG files.

    """

    # initialize path
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    # get document metadata
    document_metadata = get_document_metadata(
        session=session, collection_id=collection_id, document_id=document_id
    )
    pages = document_metadata.get("pageList", {}).get("pages", [])
    print(
        f"Found {len(pages)} pages to download for document {document_id}. Press Enter to continue."
    )
    input()
    # loop each page and extract pagexml
    for page in pages:
        # Extract relevant metadata from page element
        page_number = page["pageNr"]
        base_name = Path(page["imgFileName"]).stem
        print(f"Processing page {page_number}")
        get_jpg_image(
            session=session,
            collection_id=collection_id,
            document_id=document_id,
            page_number=page_number,
            output_dir=output_dir,
        )

        print(f"JPG saved as {output_dir}/{base_name}.jpg")


def get_page_txt(
    session, collection_id: int, document_id: int, page_number: int
) -> str:
    """
    Retrieves the TXT transcription of a given page of a document as string.

    Args:
                                                                    session: Transkribus session from `pyreslib.transkribus.api_login()` method.
                                                                    collection_id (int): Collection ID identifier from Transkribus.
                                                                    collection_id (int): Document ID identifier from Transkribus.
                                                                    page_number (int): Internal page number identifier from Transkribus.

    Returns:
                                                                    plain_text (str): string of the plaintext transcription of the page by Transkribus.

    Examples:
                                                                    >>> session = pyreslib.transkribus.api_login(user,password)
                                                                    >>> plain_text = pyreslib.transkribus.get_page_txt(session,collection_id=2792,document_id=145869,page_number=14)
    """

    # get PAGEXML
    page_xml = get_page_xml(
        session=session,
        collection_id=collection_id,
        document_id=document_id,
        page_number=page_number,
    )
    # parse PAGEXML and extract plain text
    root = ET.fromstring(page_xml)
    text_regions = root.findall(
        "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine"
    )
    plain_text = ""
    for region in text_regions:
        text_elements = region.findall(
            "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextEquiv/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Unicode"
        )

        for text_elem in text_elements:
            try:
                plain_text += text_elem.text + "\n"
            except TypeError:
                pass

    return plain_text


def import_txt_from_document(
    session, collection_id: int, document_id: int, output_dir: str | Path
):
    """
    Downloads TXT transcriptions from transkribus, giving them the same basename. as the page filename.
    Args:
            session(requests.Session): Transkribus session from `pyreslib.transkribus.api_login()` method.
            collection_id (int): Collection ID identifier from Transkribus.
            document_id (int): Document ID identifier from Transkribus.
            output_dir(str | Path): Directory path for TXT files.

    """

    # initialize path
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    # get document metadata
    document_metadata = get_document_metadata(
        session=session, collection_id=collection_id, document_id=document_id
    )
    pages = document_metadata.get("pageList", {}).get("pages", [])
    print(
        f"Found {len(pages)} pages to download for document {document_id}. Press Enter to continue."
    )
    input()
    # loop each page and extract pagexml
    for page in pages:
        # Extract relevant metadata from page element
        page_number = page["pageNr"]
        base_name = Path(page["imgFileName"]).stem
        print(f"Processing page {page_number}")
        txt = get_page_txt(
            session=session,
            collection_id=collection_id,
            document_id=document_id,
            page_number=page_number,
        )

        # saving txt string to file
        with open(output_path / f"{base_name}.txt", "w") as f:
            f.write(txt)

        print(f"TXT saved as {output_dir}/{base_name}.txt")


def import_text_transcription_to_koha_field(
    text: str,
    biblio_id: int,
    koha_session,
    koha_base_url: str,
    field: list = ["520", "a"],
):
    """
    Creates a new field statement for a bibliographic record with the given Transkribus transcription.

    Args:
                                                                    text (str): String to be ingested in Koha.
                                                                    biblio_id (int): Biblio ID for the record.
                                                                    koha_session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
                                                                    koha_base_url (str): Koha API url from credentials.
                                                                    field (list): Field and subfield where the text has to be added to record. Default is Summary/Abstract (520$a) field = ["520","a"]

    Returns:
                                                                    None
    """

    # Import record via API
    print(f"Importing record {biblio_id} from Koha API...")
    record = koha.get_biblio_marc(
        biblio_id=biblio_id, session=koha_session, base_url=koha_base_url
    )
    print(f"Number of fields: {len(record['fields'])}")
    # Add new statement for given field
    query_field = list(filter(lambda x: field[0] in x.keys(), record["fields"]))
    if len(query_field) > 0:  # append new statement
        pos = record["fields"].index(query_field[0])
        new_statement = {
            field[0]: {"ind2": " ", "ind1": " ", "subfields": [{field[1]: text}]}
        }
        # append the field statement after the first found with the same tag.
        record["fields"].insert(pos, new_statement)
    else:
        # append the field according to order
        field_n = int(field[0])
        for statement in record["fields"]:
            stat_n = int(list(statement.keys())[0])
            if field_n < stat_n:
                pos = record["fields"].index(statement)
                new_statement = {
                    field[0]: {
                        "ind2": " ",
                        "ind1": " ",
                        "subfields": [{field[1]: text}],
                    }
                }

                record["fields"].insert(pos - 1, new_statement)
                break

    # update record back to Koha catalogue
    print(f"Updating transcription to biblionumber {biblio_id}")
    koha.update_biblio_marc(
        session=koha_session,
        biblio_id=biblio_id,
        marc_json=record,
        base_url=koha_base_url,
    )


def post_page_xml(
    session,
    page_xml: str,
    collection_id: int,
    document_id: int,
    page_number: int,
    filepath=True,
):
    """
    Post a PAGEXML file back to Transkribus, either from string or local file.
    Args:
    session: Transkribus session from `pyreslib.transkribus.api_login()` method.
    page_xml (str): Filepath or XML string. Set filepath=True if you wish to interpret it as a path.
    collection_id (int): Collection ID identifier from Transkribus.
    document_id (int): Document ID identifier from Transkribus.
    page_number (int): Internal page number identifier from Transkribus.
    filepath (bool): `True` if page_xml is a filepath, `False` for page_xml as string.

    Returns:
    None

    Examples:
    >>> session = pyreslib.transkribus.api_login(user,password)
    >>>
    """
    headers = {"Content-Type": "application/xml; charset=UTF-8"}
    if filepath:
        page_xml_file = open(page_xml, "rb")
        page_xml_data = page_xml_file.read()
        page_xml_file.close()
    else:
        page_xml_data = page_xml

    page_xml_response = session.post(
        f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/{page_number}/text",
        headers=headers,
        data=page_xml_data,
    )

    if page_xml_response.status_code in [200, 201]:
        print("Success! PAGEXML has been updated to Transkribus.")
    else:
        print(f"Failed with Status Code: {page_xml_response.status_code}")
        print(f"Server Response: {page_xml_response.text}")

    return None


# Adjusting reading order


def get_polygonal_centroids(
    coordinate_list: list,
):
    """
    Returns the centroids of a lsit of coordinates.

    Args:
                                                                    coordinate_list (list): List of coordinates [(x_1,y_1), ... (x_n,x_n)].

    Returns:
                                                                    centroids: Tuple of x and y centroids.


    """
    n = len(coordinate_list)
    if n > 0:
        sum_x = float(0)
        sum_y = float(0)
        for point in coordinate_list:
            sum_x += point[0]
            sum_y += point[1]

        return (sum_x / n, sum_y / n)
    else:
        return (0, 0)


def extract_region_polygonal_coordinates(
    region: ET.Element,
) -> list:
    """
    Returns a list of coordinates given the region id.

    Args:
                                                                    region (ET.Element): ET XML element of the region.

    Returns:
                                                                    coordinates (list): List of (x,y) tuples of coordinates.

    """
    # initialize coordinates
    coordinates = []

    coordinates_element = region.find(
        "./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Coords"
    )
    points_string = coordinates_element.attrib["points"]
    points_list = points_string.split(" ")
    for point in points_list:
        x = int(point.split(",")[0])
        y = int(point.split(",")[1])
        coordinates.append((x, y))

    return coordinates


def intersection_area(coords1: list, coords2: list) -> float:
    """
    Calcuate the intesection area between two 2D-coordinate lists.

    Args:
                                                                    coords1 (list): First list of float coordinates.
                                                                    coords2 (list): Second list of float coordinates.

    Returns:
                                                                    intersection_area (float): Size of intersection between two polygonal shapes.

    """
    # import coordinates as polygons using Shapely
    polygon1 = Polygon(coords1)
    polygon2 = Polygon(coords2)

    intersection_area = polygon1.intersection(polygon2).area

    return intersection_area


def fit_text_line_in_region(
    text_line: ET.Element,
    root: ET.Element,
    TRANSKRIBUS_NS_URL: str = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15",
) -> ET.Element:
    """
    Fit text_line into best region, according to area intersection

    Args:
                                                                    text_line (ET.Element): XML element of text line to be inserted.
                                                                    root (ET.Element): XML root of the page document to be enriched.

    Returns:
                                                                    root

    """
    # get all regions in root
    ET.register_namespace("", TRANSKRIBUS_NS_URL)
    regions = root.findall(
        f"./{{{TRANSKRIBUS_NS_URL}}}Page/{{{TRANSKRIBUS_NS_URL}}}TextRegion"
    )

    # select best region according to area interception
    text_line_coords = extract_region_polygonal_coordinates(text_line)
    best_region = None
    for region in regions:
        # print(f"Current region {region.attrib["id"]}")
        region_coords = extract_region_polygonal_coordinates(region)
        int_area = intersection_area(text_line_coords, region_coords)
        # print(f"Intersection area: {int_area}")

        if best_region is None:
            best_region = region
        else:
            if int_area > intersection_area(
                text_line_coords, extract_region_polygonal_coordinates(best_region)
            ):
                best_region = region

    # append line_text to  best region
    if (
        intersection_area(
            text_line_coords, extract_region_polygonal_coordinates(best_region)
        )
        > 0
    ):
        best_region.append(text_line)

    return root


def extract_reading_order_index(text_region: ET.Element) -> int:
    """
    Extract the readingOrder index from the custom attribute.

    Returns:
                                                                    Index value, or float('inf') if not found
    """
    custom = text_region.get("custom", "")

    # Parse readingOrder {index:N;} pattern
    if "readingOrder {index:" in custom:
        try:
            start = custom.index("readingOrder {index:") + len("readingOrder {index:")
            end = custom.index(";", start)
            return int(custom[start:end])
        except (ValueError, IndexError):
            return float("inf")

    return float("inf")


def reading_order_regions(
    session,
    collection_id: int,
    document_id: int,
    page_number: int,
    n_columns: int = 2,
    page_center_method: str = "image_width",
    reference_type: str = None,
):
    """
    Update region order via Transkribus API.

    Args:
                                                                    session: Transkribus session from [pyreslib.transkribus.api_login][] method.
                                                                    collection_id (int): Collection ID identifier from Transkribus.
                                                                    doocument_id (int): Document ID identifier from Transkribus.
                                                                    page_number (int): Internal page number identifier from Transkribus.
                                                                    n_columns (int): Number of columns. The method accepts only 1 or 2. Default is 2.
                                                                    page_center_method (str): Reference method in order to determine page center. Options are "image_width" (get half of the whole image length) and "reference_region" (a specific region is used as center).
                                                                    reference_type (str): Region tag used for "reference_region" as `page_center_method` parameter. Default is `None`.

    Returns:
                                                                    page_xml_string (str): String serialization of the modified PAGEXML file. The new XML file is automatically updated back to Transkribus via [pyreslib.transkribus.post_page_xml][] method.

    Examples:
                                                                    >>> ordered_page_xml = reading_order_regions(
                                                                    session=transkribus_session,
                                                                    collection_id=2353709,document_id=14756063,page_number=29,
                                                                    n_columns=2,page_center_method="reference_region",reference_type="page-number")
                                                                    >>> Exporting back to Transkribus...



    """

    # Import page_xml from Transkribus API
    print(f"Importing PAGEXML from API...")
    print(f"page_number: {page_number}")
    page_xml = get_page_xml(
        session=session,
        collection_id=collection_id,
        document_id=document_id,
        page_number=page_number,
    )
    # Parse via ET
    root = ET.fromstring(page_xml)
    PAGEXML_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"
    ET.register_namespace("", PAGEXML_NS)
    # Get image width
    image_width = root.find(f"{{{PAGEXML_NS}}}Page").attrib["imageWidth"]
    # Calculate page center
    if page_center_method == "image_width":
        page_center = float(image_width) / 2
    elif page_center_method == "reference_region":
        # get region with reference_type tag:
        found = False
        for region in root.findall(f"{{{PAGEXML_NS}}}Page/{{{PAGEXML_NS}}}TextRegion"):
            try:
                if (
                    region.attrib["custom"].split("type:")[1].split(";")[0]
                    == reference_type
                ):
                    page_center = get_polygonal_centroids(
                        extract_region_polygonal_coordinates(region)
                    )[0]
                    found = True
                    break
            except IndexError:
                # exclude regions without structural tag
                pass

        if found is False:
            print("Reference region not found, Use image_width instead")
            page_center = float(image_width) / 2

    print(f"Image width: {image_width}")
    error_margin = float(image_width) / 50
    print(f"Error margin 2%: {error_margin}")
    print(f"Page center: {page_center}")

    # Get regions:
    regions = []
    for region in root.findall(f"{{{PAGEXML_NS}}}Page/{{{PAGEXML_NS}}}TextRegion"):
        coordinates = extract_region_polygonal_coordinates(region)
        try:
            regions.append(
                {
                    "id": region.attrib["id"],
                    "type": region.attrib["custom"].split("type:")[1].split(";")[0],
                    "centroids": get_polygonal_centroids(coordinates),
                    "region_length": (
                        max([p[0] for p in coordinates])
                        - min([p[0] for p in coordinates])
                    ),
                }
            )
        except IndexError:  # no type tag for region
            regions.append(
                {
                    "id": region.attrib["id"],
                    "type": "",
                    "centroids": get_polygonal_centroids(coordinates),
                    "region_length": (
                        max([p[0] for p in coordinates])
                        - min([p[0] for p in coordinates])
                    ),
                }
            )

    # classify region
    for region in regions:
        x_left = region["centroids"][0] - region["region_length"] / 2
        x_right = region["centroids"][0] + region["region_length"] / 2

        # print(region["id"],region["type"])

        if region["type"] == reference_type:
            region["cluster"] = "center"
        else:
            if x_left < (page_center - error_margin):
                if x_right < (page_center + error_margin):
                    region["cluster"] = "left"
                else:
                    region["cluster"] = "center"
            else:
                region["cluster"] = "right"

    # order regions according to y-centroids
    y_orderded_regions = sorted(regions, key=lambda x: x["centroids"][1])

    if n_columns == 2:
        # generate correct reading order, assuming Western left-to-right reading.
        r = -1
        right_regions_cache = []
        for region in y_orderded_regions:
            if region["cluster"] == "center":
                # append right_regions chache
                for r_region in right_regions_cache:
                    r += 1
                    r_region["reading_order"] = r

                # delete cache
                right_regions_cache = []
                # append new centered region
                r += 1
                region["reading_order"] = r

            elif region["cluster"] == "left":
                r += 1
                region["reading_order"] = r
            else:  # right case, add to cache
                right_regions_cache.append(region)

        # append last right regions
        for r_region in right_regions_cache:
            r += 1
            r_region["reading_order"] = r

        reading_ordered_regions = sorted(
            y_orderded_regions, key=lambda x: x["reading_order"]
        )

    else:  # 1 column case.
        reading_ordered_regions = y_orderded_regions

    # change reading order values in PAGEXML
    reading_order = root.find(
        f"{{{PAGEXML_NS}}}Page/{{{PAGEXML_NS}}}ReadingOrder/{{{PAGEXML_NS}}}OrderedGroup"
    )
    if reading_order is not None:
        # delete all subelements
        reading_order.clear()
        # add new order
        for region in reading_ordered_regions:
            new_element = ET.SubElement(
                reading_order,
                "RegionRefIndexed",
                attrib={
                    "index": str(region["reading_order"]),
                    "regionRef": str(region["id"]),
                },
            )
        # change reading_order value in each region
    else:
        print("ReadingOder element not present.")
        pass

    for region in root.findall(f"{{{PAGEXML_NS}}}Page/{{{PAGEXML_NS}}}TextRegion"):
        # get new reading order
        ordered_region = list(
            filter(lambda x: x["id"] == region.attrib["id"], reading_ordered_regions)
        )[0]
        # substitute reading order in custom attribute
        old_reading_order = region.attrib["custom"].split("index:")[1].split(";")[0]
        region.attrib["custom"] = region.attrib["custom"].replace(
            f"index:{old_reading_order}", f"index:{ordered_region['reading_order']}"
        )

    # string export
    page_xml_string = ET.tostring(
        root, encoding="utf-8", xml_declaration=True, method="xml"
    )
    # Export back to Transkribus API
    print("Exporting back to Transkribus...")
    post_page_xml(
        session=session,
        page_xml=page_xml_string,
        collection_id=collection_id,
        document_id=document_id,
        page_number=page_number,
        filepath=False,
    )
    return page_xml_string


def get_page_status(
    session, collection_id: int, document_id: int, page_number: int
) -> str:
    """
    Retrieves the PAGEXML transcription status of a given page of a document as string.
    """
    # get document metadata
    document_metadata = get_document_metadata(
        session=session, collection_id=collection_id, document_id=document_id
    )

    # get page metadata
    page_metadata = list(
        filter(
            lambda x: x["pageNr"] == page_number, document_metadata["pageList"]["pages"]
        )
    )[0]

    # get latest transcript status
    return page_metadata["tsList"]["transcripts"][0]["status"]


def reading_order_document(
    session,
    collection_id: int,
    document_id: int,
    n_columns: int = 2,
    page_center_method: str = "image_width",
    reference_type: str = "page-number",
    min_page_status="FINAL",
):
    """
    Applies reading order to whole document, only for pages with status equal or better that given parameter.

    Args:
                                                                    session: Transkribus session from [pyreslib.transkribus.api_login][] method.
                                                                    collection_id (int): Collection ID identifier from Transkribus.
                                                                    doocument_id (int): Document ID identifier from Transkribus.
                                                                    n_columns (int): Number of columns. The method accepts only 1 or 2. Default is 2.
                                                                    page_center_method (str): Reference method in order to determine page center. Options are "image_width" (get half of the whole image length) and "reference_region" (a specific region is used as center).
                                                                    reference_type (str): Region tag used for "reference_region" as `page_center_method` parameter. Default is `None`.
                                                                    min_page_status (str): Minimal status in order to apply reordering to page. Default is `FINAL`, but you can use `NEW`,`IN_PROGRESS`, `DONE` and `GT` instead.

    Retuns:
                                                                    `None`

    """
    # Transkribus statusses:
    tr_statuses = ["NEW", "IN_PROGRESS", "DONE", "FINAL", "GT"]
    # Get minimal status for reading order application
    index_min_status = tr_statuses.index(min_page_status)

    # retrieve collection metadata
    print(f"Importing metadata for document {document_id}")
    documents_metadata = get_documents_metadata(
        session=session, collection_id=collection_id
    )

    # get document metadata
    document_metadata = list(
        filter(lambda x: x["md"]["docId"] == document_id, documents_metadata)
    )[0]

    print(f"Reference type: {reference_type}")
    for page in document_metadata["pageList"]["pages"]:
        page_status = get_page_status(
            session=session,
            collection_id=collection_id,
            document_id=document_id,
            page_number=page["pageNr"],
        )

        if tr_statuses.index(page_status) >= index_min_status:
            print(f"Current page: {page['pageNr']}")
            reading_order_regions(
                session=session,
                collection_id=collection_id,
                document_id=document_id,
                page_number=page["pageNr"],
                n_columns=n_columns,
                page_center_method=page_center_method,
                reference_type=reference_type,
            )

    print(
        f"Reading order completed, Check your collection at https://app.transkribus.org/collection/{collection_id}/doc/{document_id}"
    )


def import_pagexml_from_document(
    session: requests.Session,
    collection_id: int,
    document_id: int,
    output_dir: str | Path,
):
    """
    Downloads PAGEXML transcriptions from transkribus, giving them the same basename. as the page filename.
    Args:
            session(requests.Session): Transkribus session from `pyreslib.transkribus.api_login()` method.
            collection_id (int): Collection ID identifier from Transkribus.
            document_id (int): Document ID identifier from Transkribus.
            output_dir(str | Path): Directory path for PAGEXML files.

    """

    # initialize path
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    # get document metadata
    document_metadata = get_document_metadata(
        session=session, collection_id=collection_id, document_id=document_id
    )
    pages = document_metadata.get("pageList", {}).get("pages", [])
    print(
        f"Found {len(pages)} pages to download for document {document_id}. Press Enter to continue."
    )
    input()
    # loop each page and extract pagexml
    for page in pages:
        # Extract relevant metadata from page element
        page_number = page["pageNr"]
        base_name = Path(page["imgFileName"]).stem
        print(f"Processing page {page_number}")
        # get pagexml as string from Transkribus API
        page_xml = get_page_xml(
            session=session,
            collection_id=collection_id,
            document_id=document_id,
            page_number=page_number,
        )
        file_path = output_path / f"{base_name}.xml"
        # save pagexml to output directory
        with open(file_path, "wb") as f:
            f.write(page_xml)

        print(f"PAGEXML saved as {file_path}")


def classify_region_two_columns(
    region: ET.Element, page_center: float, error_margin: float
) -> str:
    """
    Classify a region based o page_center x-coordinates, returning left, center or right
    """
    # Extract centroids for region
    coordinates = extract_region_polygonal_coordinates(region)
    centroids = get_polygonal_centroids(coordinates)
    x_centroid = centroids[0]
    y_centroid = centroids[1]
    region_length = max([p[0] for p in coordinates]) - min([p[0] for p in coordinates])

    x_left = x_centroid - region_length / 2
    x_right = x_centroid + region_length / 2

    # Thresholds for the central 'neutral' column
    left_threshold = page_center - error_margin
    right_threshold = page_center + error_margin

    if x_left < (left_threshold):
        if x_right < (right_threshold):
            return "left"
        else:
            return "center"
    else:
        return "right"


def classify_regions_two_colums(
    page_xml_path: str | Path,
    page_center_method: str = "reference_region",
    reference_type: str = "page-number",
    PAGEXML_NS: str = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15",
) -> list:
    """
    Classifies regions according to two-column layout. You can use a reference region to define the center.
    It returns a list of dictionaries, with XML element and classification tag.

    Args:
                    page_xml_path(str): Path to PAGEXML file.
                    page_center_method (str): Reference method in order to determine page center. Options are "image_width" (get half of the whole image length) and "reference_region" (a specific region is used as center).
                    reference_type (str): Region tag used for "reference_region" as `page_center_method` parameter. Default is `page-number`.
                    PAGEXML_NS(str): Namespace URI for PAGEXML schema. Default is "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15".
    Returns:
                    ordered_regions(list): List of blocks

    """
    # import PAGEXML
    with open(page_xml_path, "rb") as f:
        page_xml = f.read()
        f.close()

    root = ET.fromstring(page_xml)
    ET.register_namespace("", PAGEXML_NS)

    # initialize classified_regions list
    region_blocks = []

    # get TextRegions
    regions = root.findall(f".//{{{PAGEXML_NS}}}TextRegion")
    # sort regions according to two-colum layout and reference region

    # Get image width
    image_width = root.find(f".//{{{PAGEXML_NS}}}Page").attrib["imageWidth"]

    # Calculate page center
    if page_center_method == "image_width":
        page_center = float(image_width) / 2
    elif page_center_method == "reference_region":
        # get region with reference_type tag:
        found = False
        for region in regions:
            try:
                if (
                    region.attrib["custom"].split("type:")[1].split(";")[0]
                    == reference_type
                ):
                    page_center = get_polygonal_centroids(
                        extract_region_polygonal_coordinates(region)
                    )[0]
                    found = True
                    break
            except IndexError:
                # exclude regions without structural tag
                pass
        if found is False:
            page_center = float(image_width) / 2

    print(f"Image width: {image_width}")
    error_margin = float(image_width) / 50
    print(f"Error margin 2%: {error_margin}")
    print(f"Page center: {page_center}")

    # sort regions in blocks based on their y_centroid coordinate. Everytime a centered region comes, we generate a new block.
    # left regions are stored in order in left column, while right regions in right one.

    for region in regions:
        # classify region
        try:
            region_type = region.attrib["custom"].split("type:")[1].split(";")[0]
            if (
                region.attrib["custom"].split("type:")[1].split(";")[0]
                == reference_type
            ):
                region_class = "center"
            else:
                region_class = classify_region_two_columns(
                    region, page_center=page_center, error_margin=error_margin
                )
        except IndexError:
            continue

        region_y_centroid = get_polygonal_centroids(
            extract_region_polygonal_coordinates(region)
        )[1]

        region_data = {
            "id": region.attrib["id"],
            "class": region_class,
            "y_centroid": region_y_centroid,
            "xml_element": region,
        }

        # 2. Block Generation Logic (The Fix)
        if region_class == "center":
            # Always initiate a new isolated block for centered elements
            region_blocks.append([region_data])

        else:
            # For 'left' or 'right' regions:
            # Start a NEW block if:
            # - No blocks exist yet
            # - OR the previous block contains a 'center' region
            if not region_blocks or region_blocks[-1][-1]["class"] == "center":
                region_blocks.append([region_data])
            else:
                # Otherwise, it's a left/right region following another left/right;
                # append to the current 'column' group
                region_blocks[-1].append(region_data)

    # Order each block based on y_centroid and left/right priority
    ordered_regions = []
    for i, block in enumerate(region_blocks, 1):
        # Separate regions in the current block by class
        center_regs = [r for r in block if r["class"] == "center"]
        left_regs = [r for r in block if r["class"] == "left"]
        right_regs = [r for r in block if r["class"] == "right"]

        # Sort the left and right columns vertically (y_centroid)
        left_regs_sorted = sorted(left_regs, key=lambda x: x["y_centroid"])
        right_regs_sorted = sorted(right_regs, key=lambda x: x["y_centroid"])

        # Construction of the final sequence for this block
        # 1. The 'divider' (Center) usually comes first (e.g., a header)
        for r in center_regs:
            r["block"] = i
            ordered_regions.append(r)

        # 2. Entire left column content
        for r in left_regs_sorted:
            r["block"] = i
            ordered_regions.append(r)

        # 3. Entire right column content
        for r in right_regs_sorted:
            r["block"] = i
            ordered_regions.append(r)

    return ordered_regions
