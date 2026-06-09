import requests
import urllib
import xml.etree.ElementTree as ET
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
			f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document["docId"]}/fulldoc",
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




def get_page_xml(session, collection_id: int,document_id: int,page_number:int) -> str:
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

def get_jpg_image(session, collection_id: int,document_id: int,page_number:int, output_filepath: str):
	"""
	Extract the JPG image of a given page from Transkribus API
	
	Args:
		session (): Transkribus session from `pyreslib.transkribus.api_login()` method.
		collection_id (int): Collection ID identifier from Transkribus.
		document_id (int): Document ID identifier from Transkribus.
		page_number (int): Internal page number identifier from Transkribus.
		output_filepath (str): local path for download.

	Returns:
		`None`

	Examples:
		>>> session = pyreslib.transkribus.api_login(user,password)
		>>> output_filepath = f"./tmp/{str(document_id)}_{str(page_number).zfill(3)}"
		>>> get_jpg_image(session,collection_id=2792,document_id=145869,page_number=14,output_filepath=output_filepath)
	"""

	# Get document metadata
	document = get_document_metadata(session=session, collection_id=collection_id,document_id=document_id)

	# Find page metadata
	page_metadata = list(filter(lambda x: x["pageNr"] == page_number,document["pageList"]["pages"]))
	if len(page_metadata) >0:
		# page found, get image URL
		image_url = page_metadata[0]["url"]
		urllib.request.urlretrieve(image_url,output_filepath)
	else:
		print(f"Page not found for {document_id}/{page_number}")

	return None	


def get_page_txt(session, collection_id: int,document_id: int,page_number:int) -> str:
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
	page_xml = get_page_xml(session=session,collection_id=collection_id,document_id=document_id,page_number=page_number)
	# parse PAGEXML and extract plain text
	root = ET.fromstring(page_xml)
	text_regions = root.findall("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Page/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextRegion/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextLine")
	plain_text = ""
	for region in text_regions:
		text_elements = region.findall("./{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}TextEquiv/{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Unicode")

		for text_elem in text_elements:
			plain_text += text_elem.text + "\n"


	return plain_text


def import_text_transcription_to_koha_field(text: str, biblio_id: int, koha_session, koha_base_url: str, field: list = ["520","a"]):
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
	record = koha.get_biblio_marc(biblio_id=biblio_id,session=koha_session,base_url=koha_base_url)
	print(f"Number of fields: {len(record["fields"])}")
	# Add new statement for given field
	query_field = list(filter(lambda x: field[0] in x.keys(), record["fields"]))
	if len(query_field) >0: # append new statement
		pos = record["fields"].index(query_field[0])
		new_statement = {field[0]: {
			"ind2": " ",
			"ind1": " ",
			"subfields": [{field[1]: text}]
		  }}
		# append the field statement after the first found with the same tag.
		record["fields"].insert(pos,new_statement)
	else:
		# append the field according to order
		field_n = int(field[0])
		for statement in record["fields"]:
			stat_n = int(list(statement.keys())[0])
			if field_n < stat_n:
				pos = record["fields"].index(statement)
				new_statement = {field[0]: {
					"ind2": " ",
					"ind1": " ",
					"subfields": [{field[1]: text}]
				  }}

				record["fields"].insert(pos-1,new_statement)
				break


	# update record back to Koha catalogue
	print(f"Updating transcription to biblionumber {biblio_id}")
	koha.update_biblio_marc(session=koha_session, biblio_id=biblio_id, marc_json=record, base_url=koha_base_url)



def post_page_xml(session,page_xml:str,collection_id: int,document_id:int,page_number:int,filepath=True):
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
		page_xml_file = open(page_xml,'rb')
		page_xml_data = page_xml_file.read()
		page_xml_file.close()
	else:
		page_xml_data = page_xml

	page_xml_response = session.post(
			f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/{page_number}/text",
			headers=headers,
			data=page_xml_data
		)

	if page_xml_response.status_code in [200, 201]:
		print("Success! The Kraken PAGE XML structure has been bound to the page.")
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

def extract_reading_order_index(text_region: ET.Element) -> int:
	"""
	Extract the readingOrder index from the custom attribute.
	
	Returns:
		Index value, or float('inf') if not found
	"""
	custom = text_region.get('custom', '')
	
	# Parse readingOrder {index:N;} pattern
	if 'readingOrder {index:' in custom:
		try:
			start = custom.index('readingOrder {index:') + len('readingOrder {index:')
			end = custom.index(';', start)
			return int(custom[start:end])
		except (ValueError, IndexError):
			return float('inf')
	
	return float('inf')


def reading_order_regions(session, collection_id: int,document_id: int,page_number: int, n_columns: int = 2, page_center_method: str = "image_width",reference_type: str = None):
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
	print(f'Importing PAGEXML from API...')
	print(f"page_number: {page_number}")
	page_xml = get_page_xml(session=session, collection_id=collection_id,document_id=document_id,page_number=page_number)
	# Parse via ET
	root = ET.fromstring(page_xml)
	PAGEXML_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"
	ET.register_namespace('', PAGEXML_NS)
	# Get image width
	image_width = root.find(f"{{{PAGEXML_NS}}}Page").attrib["imageWidth"]
	# Calculate page center
	if page_center_method == "image_width":
		page_center = float(image_width) / 2
	elif page_center_method == "reference_region":
		# get region with reference_type tag:
		found = False
		for region in root.findall(f"{{{PAGEXML_NS}}}Page/{{{PAGEXML_NS}}}TextRegion"):
			if region.attrib["custom"].split("type:")[1].split(";")[0] == reference_type:
				page_center = get_polygonal_centroids(extract_region_polygonal_coordinates(region))[0]
				found = True
				break

		if found is False:
			print("Reference region not found, skipping page.")
			return None


	print(f"Image width: {image_width}")
	error_margin = float(image_width)/50
	print(f"Error margin 2%: {error_margin}")
	print(f"Page center: {page_center}")

	# Get regions:
	regions = []
	for region in root.findall(
		f"{{{PAGEXML_NS}}}Page/{{{PAGEXML_NS}}}TextRegion"
	):
		coordinates = extract_region_polygonal_coordinates(region)
		try:
			regions.append({
				"id": region.attrib["id"],
				"type": region.attrib["custom"].split("type:")[1].split(";")[0],
				"centroids": get_polygonal_centroids(coordinates),
				"region_length": (max([p[0] for p in coordinates]) - min([p[0] for p in coordinates]))
				})
		except IndexError: # no type tag for region
			regions.append({
				"id": region.attrib["id"],
				"type": "",
				"centroids": get_polygonal_centroids(coordinates),
				"region_length": (max([p[0] for p in coordinates]) - min([p[0] for p in coordinates]))
				})



	# classify region
	for region in regions:
		x_left = region["centroids"][0] - region["region_length"] / 2
		x_right =  region["centroids"][0] + region["region_length"] / 2

		#print(region["id"],region["type"])

		if region["type"] == reference_type:
			region["cluster"] = "center"
		else:	
			if x_left < (page_center - error_margin) :
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
			else: # right case, add to cache
				right_regions_cache.append(region)

		# append last right regions
		for r_region in right_regions_cache:
			r += 1
			r_region["reading_order"] = r	

		reading_ordered_regions = sorted(y_orderded_regions,key=lambda x: x["reading_order"])
	
	else: # 1 column case.
		reading_ordered_regions = y_orderded_regions

	# change reading order values in PAGEXML
	reading_order = root.find(f"{{{PAGEXML_NS}}}Page/{{{PAGEXML_NS}}}ReadingOrder/{{{PAGEXML_NS}}}OrderedGroup")
	if reading_order is not None:
		# delete all subelements
		reading_order.clear()
		# add new order
		for region in reading_ordered_regions:
			new_element = ET.SubElement(reading_order,"RegionRefIndexed", attrib={"index": str(region["reading_order"]) , "regionRef": str(region["id"])})
		# change reading_order value in each region
	else:
		print("ReadingOder element not present.")
		pass 	

	for region in root.findall(f"{{{PAGEXML_NS}}}Page/{{{PAGEXML_NS}}}TextRegion"):

		# get new reading order
		ordered_region = list(filter(lambda x: x["id"] == region.attrib["id"], reading_ordered_regions))[0]
		# substitute reading order in custom attribute
		old_reading_order = region.attrib["custom"].split("index:")[1].split(";")[0]
		region.attrib["custom"] = region.attrib["custom"].replace(f"index:{old_reading_order}",f"index:{ordered_region["reading_order"]}")

	# string export
	page_xml_string = ET.tostring(root,encoding="utf-8", xml_declaration=True,method='xml')
	# Export back to Transkribus API
	print("Exporting back to Transkribus...")
	post_page_xml(session=session,page_xml=page_xml_string,collection_id=collection_id,document_id=document_id,page_number=page_number,filepath=False)
	return page_xml_string




def get_page_status(session, collection_id: int,document_id: int,page_number:int) -> str:
	"""
	Retrieves the PAGEXML transcription status of a given page of a document as string.
	"""
	# get document metadata 
	document_metadata = get_document_metadata(session=session,collection_id=collection_id,document_id=document_id)

	# get page metadata
	page_metadata = list(filter(lambda x: x["pageNr"] == page_number, document_metadata["pageList"]["pages"]))[0]

	# get latest transcript status
	return page_metadata["tsList"]["transcripts"][0]["status"]


def reading_order_document(session,collection_id: int,document_id: int, n_columns: int = 2, page_center_method: str = "image_width",reference_type: str = "page-number", min_page_status ="FINAL"):
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
	tr_statuses = ["NEW","IN_PROGRESS","DONE","FINAL","GT"]
	# Get minimal status for reading order application
	index_min_status = tr_statuses.index(min_page_status)

	# retrieve collection metadata
	print(f"Importing metadata for document {document_id}")
	documents_metadata = get_documents_metadata(session=session,collection_id=collection_id)

	# get document metadata
	document_metadata = list(filter(lambda x: x["md"]["docId"] == document_id, documents_metadata))[0]


	print(f"Reference type: {reference_type}")
	for page in document_metadata["pageList"]["pages"]:
		page_status = get_page_status(session=session, collection_id=collection_id,document_id=document_id,page_number=page["pageNr"])

		if tr_statuses.index(page_status) >= index_min_status:
			print(f"Current page: {page["pageNr"]}")
			reading_order_regions(session=session, collection_id=collection_id,document_id=document_id,page_number=page["pageNr"], n_columns=n_columns, page_center_method=page_center_method,reference_type=reference_type)


	print(f"Reading order completed, Check your collection at https://app.transkribus.org/collection/{collection_id}/doc/{document_id}")