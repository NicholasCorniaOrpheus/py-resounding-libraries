from PIL import Image
import os
from kraken import binarization
from kraken import serialization
from kraken.containers import Segmentation
from kraken.tasks import SegmentationTaskModel, RecognitionTaskModel
from kraken.configs import SegmentationInferenceConfig, RecognitionInferenceConfig
import xml.etree.ElementTree as ET

from pyreslib import transkribus


def transcribe_directory(
	dir_path: str = "./data/kraken/transcriptions",
	segmentation_model_path: str = None,
	recognition_model_path: str = "./data/kraken/models/catmus-large/catmus-print-fondue-large.mlmodel",
	export_dir: str = "./data/kraken/transcriptions",
	xml_namespace: str = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15",
):
	"""
	Transcribe image files within directory (no subdirectories allowed) using Kraken.

	Args:
		dir_path(str): Directory path where images are stored. Default is `./data/kraken/transcriptions`
		segmentation_model_path (str): Path to segmentation model. Default is `None`, but you can install dfine_kraken plugin and upload your custom model in `"./data/kraken/models/`.
		recognition_model_path(str): Path to recognition model. Default is the [CATMUS Print large](https://zenodo.org/records/10592716) "./data/kraken/models/catmus-large/catmus-print-fondue-large.mlmodel"
		export_dir(str): Export directory for the PAGEXML files. Default is `./data/kraken/transcriptions`
		xml_namespace(str): PAGEXML namespace used by Kraken 7: `http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15`.
	
	Returns:
		`None`
	"""
	# Load models once outside the loop
	print("Loading segmentation model...")
	try:
		seg_model = SegmentationTaskModel.load_model(segmentation_model_path)
	except ValueError as e:
		print(f"Error loading segmentation model: {e}")
		print("Falling back to default BLLA segmentation model...")
		seg_model = SegmentationTaskModel.load_model()  # Load default model

	print("Loading recognition model...")
	rec_model = RecognitionTaskModel.load_model(recognition_model_path)

	seg_config = SegmentationInferenceConfig()
	rec_config = RecognitionInferenceConfig()

	for file in os.scandir(dir_path):
		if file.name.endswith((".png", ".jpg", ".jpeg", ".tif", ".gif")):
			print(f"Processing {file.name}...")

			try:
				# Open and binarize image
				img = Image.open(file.path)
				bw_img = binarization.nlbin(img)

				# Perform segmentation
				segmentation = seg_model.predict(bw_img, seg_config)

				# Perform recognition
				records = list(rec_model.predict(bw_img, segmentation, rec_config))

				# Build segmentation with recognition results
				recognized_segmentation = Segmentation(
					lines=records,
					imagename=file.path,
					type=segmentation.type,
					text_direction=segmentation.text_direction,
					script_detection=segmentation.script_detection,
					regions=segmentation.regions,
				)

				# Serialize and save results
				serialization_prediction(
					segmentation=recognized_segmentation,
					file_path=file.path,
					image=bw_img,
					export_dir=export_dir,
					xml_namespace=xml_namespace,
				)
			except Exception as e:
				print(f"Error processing {file.name}: {e}")
				continue

def transcribe_image(
	image_filepath: str,
	export_dir: str,
	segmentation_model_path: str = None,
	recognition_model_path: str = "./data/kraken/models/catmus-large/catmus-print-fondue-large.mlmodel",
	xml_namespace: str = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15",
):
	"""
	Transcribe image file using Kraken, returning a PAGEXML and TXT transcriptions.

	Args:
		dir_path(str): Directory path where images are stored. Default is `./data/kraken/transcriptions`
		segmentation_model_path (str): Path to segmentation model. Default is `None`, but you can install dfine_kraken plugin and upload your custom model in `"./data/kraken/models/`.
		recognition_model_path(str): Path to recognition model. Default is the [CATMUS Print large](https://zenodo.org/records/10592716) "./data/kraken/models/catmus-large/catmus-print-fondue-large.mlmodel"
		xml_namespace(str): PAGEXML namespace used by Kraken 7: `http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15`.
	
	Returns:
		`None`
	"""
	# Load models once outside the loop
	print("Loading segmentation model...")
	try:
		seg_model = SegmentationTaskModel.load_model(segmentation_model_path)
	except ValueError as e:
		print(f"Error loading segmentation model: {e}")
		print("Falling back to default BLLA segmentation model...")
		seg_model = SegmentationTaskModel.load_model()  # Load default model

	print("Loading recognition model...")
	rec_model = RecognitionTaskModel.load_model(recognition_model_path)

	seg_config = SegmentationInferenceConfig()
	rec_config = RecognitionInferenceConfig()

	print(f"Processing {image_filepath}...")

	try:
		# Open and binarize image
		img = Image.open(image_filepath)
		bw_img = binarization.nlbin(img)

		# Perform segmentation
		segmentation = seg_model.predict(bw_img, seg_config)

		# Perform recognition
		records = list(rec_model.predict(bw_img, segmentation, rec_config))

		# Build segmentation with recognition results
		recognized_segmentation = Segmentation(
			lines=records,
			imagename=image_filepath,
			type=segmentation.type,
			text_direction=segmentation.text_direction,
			script_detection=segmentation.script_detection,
			regions=segmentation.regions,
		)

		# Serialize and save results
		serialization_prediction(
			segmentation=recognized_segmentation,
			file_path=image_filepath,
			image=bw_img,
			export_dir=export_dir,
			xml_namespace=xml_namespace,
		)
	except Exception as e:
		print(f"Error processing {image_filepath}: {e}")

def serialization_prediction(
	segmentation, file_path: str, image, export_dir: str, xml_namespace: str
):
	"""
	Serializes recognition results to PageXML and plain text files.

	Args:
			segmentation: Segmentation object with recognition results
			file_path (str): Path of the original image.
			image: PIL.Image object
			export_dir (str): Export directory.
			xml_namespace (str): XML namespace for PageXML output.

	Returns:
			None
	"""
	# Serialize to PageXML
	page_xml = serialization.serialize(
		segmentation,
		image_size=image.size,
		template="pagexml",
		sub_line_segmentation=False,
	)

	# Get base filename without extension
	base_filename = os.path.splitext(os.path.basename(file_path))[0]

	# Save XML to file
	xml_output_path = os.path.join(export_dir, f"{base_filename}.xml")
	print(f"Serializing image into {xml_output_path}...")
	with open(xml_output_path, "w") as f:
		f.write(page_xml)

	# Parse PageXML and extract plain text
	root = ET.fromstring(page_xml)
	plain_text = ""

	# Find all TextLine elements (using wildcard for namespace)
	for line in root.iter():
		if line.tag.endswith("TextLine"):
			for child in line.iter():
				if child.tag.endswith("Unicode") and child.text:
					plain_text += child.text
			plain_text += "\n"

	# Save TXT to file
	txt_output_path = os.path.join(export_dir, f"{base_filename}.txt")
	print(f"Saving text to {txt_output_path}...")
	with open(txt_output_path, "w") as f:
		f.write(plain_text)

def update_kraken_XML_to_transkribus(session,collection_id: int,document_id:int, page_number: int,page_xml_filepath: str):

	"""
	Converts and updates PAGEXML generated by Kraken back to Transkribus via API.

	Args:
		session: Transkribus session from `pyreslib.transkribus.api_login()` method.
		collection_id (int): Collection ID identifier from Transkribus.
		document_id (int): Document ID identifier from Transkribus.
		page_number (int): Internal page number identifier from Transkribus.
		page_xml_filepath (str): Filepath for Kraken generated PAGEXML file.

	Returns:
		`None`

	"""
	# convert PAGEXML kraken file for Transkribus
	TRANSKRIBUS_NS_URL = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"
	KRAKEN_NS_URL = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
	tree = ET.parse(page_xml_filepath)
	root = tree.getroot()
	# PAGE XML namespace map for searching elements
	ns = {'xmlns': KRAKEN_NS_URL}

	if 'xsi:schemaLocation' in root.attrib:
		del root.attrib['{http://w3.org}schemaLocation']

	# 3. Patch TextRegions: Add readingOrder and change layout structural names
	for idx, region in enumerate(root.findall('.//xmlns:TextRegion', ns)):
		# Transkribus reads layouts via 'structure {type:heading/paragraph/etc}'
		region.set('custom', f"readingOrder {{index:{idx};}} structure {{type:paragraph;}}")

	# 4. Patch TextLines: Transkribus expects 'layout' definitions rather than 'default'
	for idx, line in enumerate(root.findall('.//xmlns:TextLine', ns)):
		line.set('custom', f"readingOrder {{index:{idx};}}")

	# namespaces
	#ET.register_namespace('', 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15')
	ET.register_namespace("",TRANSKRIBUS_NS_URL) # use Transkribus version
	#ET.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")
	#ET.register_namespace('schemaLocation',"http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15 http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15/pagecontent.xsd")
	# 5. Convert back to string bytes 
	# Transkribus explicitly requires the XML declaration at the top
	xml_patched_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
	# replace Kraken namespace with transkribus one
	xml_patched_bytes = xml_patched_bytes.replace(KRAKEN_NS_URL.encode('utf-8'), TRANSKRIBUS_NS_URL.encode('utf-8'))

	# post file back to Transkribus via API
	print(f"Updating transcription from {page_xml_filepath} back to Transkribus")
	transkribus.post_page_xml(session=session,page_xml=xml_patched_bytes,collection_id=collection_id,document_id=document_id,page_number=page_number,filepath=False)

	

def transcription_dir_to_transkribus(transcription_dir: str, session, collection_id:int, document_id:int):
	"""
	Transcribes a whole Transkribus document by:

	1. Getting all images from API using [pyreslib.transkribus.get_jpg_image][]
	2. Transcribing images using kraken [pyreslib.kraken.transcribe_image][] 
	3. Updating transcriptions backt to Transkribus via [pyreslib.kraken].update_kraken_XML_to_transkribus][].

	"""
	# 1. images

	# document_metadata
	print("Importing document metadata...")
	document_metadata = transkribus.get_document_metadata(session=session,collection_id=collection_id,document_id=document_id)

	print("Getting images from Transkribus API...")
	for page in document_metadata["pageList"]["pages"]:
		# import images in directory
		print(f"Current page: {page["pageNr"]}")
		transkribus.get_jpg_image(session=session, collection_id=collection_id,document_id=document_id,page_number=page["pageNr"], output_filepath=os.path.join(transcription_dir,page["imgFileName"]))

	# 2. Kraken
	print("Transcribing images using Kraken, by default it skips the image if an XML file is present.")
	print("It might take a while...")

	all_files = list(os.scandir(transcription_dir))
	existing_xml_basenames = {
    	f.name.replace(".xml", "") 
    	for f in all_files 
    	if f.name.endswith(".xml")
		}

	for f in all_files:
		if f.path.endswith(".jpg"):
			img_basename = f.name.replace(".jpg","")
			if img_basename in existing_xml_basenames:
				print("Skipping image. Transcription is already present.")
			else:
				transcribe_image(image_filepath=f.path,export_dir=transcription_dir)


	# 3. Transkribus
	print("Converting and updating transcriptions back to Transkribus")
	for f in all_files:
		if f.path.endswith(".xml"):
			# retrieve page number from filename
			xml_page_number = list(filter(lambda x: x["imgFileName"] == f.name.replace(".xml",".jpg"), document_metadata["pageList"]["pages"]))[0]["pageNr"]
			update_kraken_XML_to_transkribus(session=session,collection_id=collection_id,document_id=document_id, page_number=xml_page_number,page_xml_filepath=f.path)




