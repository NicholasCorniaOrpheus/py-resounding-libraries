import requests
import urllib
import xml.etree.ElementTree as ET


### TO-DO
"""
1. Conversion option for PAGEXML format, such as Plain Text and TEIXML.
2. Authorities spotting via Fuzzy Search in trascribed text

"""

def api_login(user: str, password: str):
	"""
	Args:
	user (user): Client Username
	pw (str): Client secret Password
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
	"""Returns a full dictionary of documents, including pages metadata.
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

def get_page_xml(session, collection_id: int,document_id: int,page_number:int) -> str:
	"""
	Retrieves the PAGEXML transcription of a given page of a document as string.
	Args:
	session: Transkribus session from `pyreslib.transkribus.api_login()` method.
	collection_id (int): Collection ID identifier from Transkribus.
	collection_id (int): Document ID identifier from Transkribus.
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
	
	return str(page_xml.text).encode("utf-8")

def get_jpg_image(session, collection_id: int,document_id: int,page_number:int, output_filepath: str):
	"""
	Extract the JPG image of a given page from Transkribus API
	Args:
	session: Transkribus session from `pyreslib.transkribus.api_login()` method.
	collection_id (int): Collection ID identifier from Transkribus.
	document_id (int): Document ID identifier from Transkribus.
	page_number (int): Internal page number identifier from Transkribus.
	output_filepath (str): local path for download.

	Returns:
	None

	Examples:
	>>> session = pyreslib.transkribus.api_login(user,password)
	>>> output_filepath = f"./tmp/{str(document_id)}_{str(page_number).zfill(3)}"
	>>> get_jpg_image(session,collection_id=2792,document_id=145869,page_number=14,output_filepath=output_filepath)
	"""

	# Get document metadata
	document = session.get(
			f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/fulldoc",
			headers=headers,
		)

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



def post_page_xml(session,page_xml:str,collection_id: int,document_id:int,page_number:int,filepath=True):
	"""
	Post a PAGEXML file back to Transkribus, either from string or local file.
	Args:
	session: Transkribus session from `pyreslib.transkribus.api_login()` method.
	page_xml (str): Filepath or XML string. Set filepath=True if you wish to interpret it as a path.
	collection_id (int): Collection ID identifier from Transkribus.
	collection_id (int): Document ID identifier from Transkribus.
	page_number (int): Internal page number identifier from Transkribus.
	filepath (bool): `True` if page_xml is a filepath, `False` for page_xml as string.

	Returns:
	None

	Examples:
	>>> session = pyreslib.transkribus.api_login(user,password)
	>>> 
	"""
	headers = {"Content-Type": "application/xml"}
	if filepath:
		page_xml_file = open(page_xml_filepath,'rb')
		page_xml_data = page_xml_file.read()
		page_xml_file.close()
	else:
		page_xml_data = page_xml

	page_xml_response = session.post(
			f"https://transkribus.eu/TrpServer/rest/collections/{collection_id}/{document_id}/{page_number}/text",
			headers=headers,
			data=page_xml_data
		)

	return None


	