import requests
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import json
import os
import datetime
from copy import deepcopy
from time import time

import statistics as stat

from wikibaseintegrator import wbi_login, WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from SPARQLWrapper import SPARQLWrapper, JSON

from bisect import bisect_left

from multiprocessing import Pool, cpu_count
from typing import List, Dict, Any
import traceback

from pyreslib import koha, utilities

### TO-DO
"""
1. Import umbrella terms to authority from Wikidata based on mapping.
2. Import Wikidata description into catalogue record (append to field 500$a).
3. Import authorities from OpenRefine CSV reconciliation list with headers = {"auth_id","auth_main_heading","qid","wd_uri","wd_label"} 

"""


def wikibase_integrator_session_basic(
	username: str,
	password: str,
	mediawiki_api_url="https://www.wikidata.org/w/api.php",
):
	"""Returns an wikibase_integrator session, given user and password of your Wikidata account. We advice to create a Wikidata user in oder to prevent a "Too Many Requests HTTP 429" code.

	Args:
		username (str): Username associated with your Wikidata user.
		password (str): Password associated with your Wikidata user.
		mediawiki_api_url (str): Wikidata REST API by default. You can change it by replacing the `https://www.wikidata.org/w/api.php` with your own Wikibase URL.

	Returns:
		wb (WikibaseIntegrator): WikibaseIntegrator session

	Examples:
		>>> wb = pyreslib.koha.wikibase_integrator_session_basic(username="{USERNAME}"", password="{PASSWORD}" , mediawiki_api_url="https://www.wikidata.org/w/rest.php/wikibase/v1")

	"""

	# Set up user-agent type
	wbi_config[
		"USER_AGENT"
	] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"

	# login using basic credentials
	login_instance = wbi_login.Clientlogin(
		user=username, password=password, mediawiki_api_url=mediawiki_api_url
	)

	wb = WikibaseIntegrator(login=login_instance)

	return wb


def wikibase_integrator_session_oauth2(
	consumer_token: str,
	consumer_secret: str,
	mediawiki_api_url:str ="https://www.wikidata.org/w/api.php",
):
	"""Returns an wikibase_integrator session, given API consumer token and secret keys of your Wikidata account. You have to make a request to Wikimedia via this [URL](https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose/oauth2) in order to have such credentials. For advanced use only.

	Args:
		consumer_token (str): API consumer key associated with your Wikidata user.
		consumer_secret (str): API secret key associated with your Wikidata user.
		mediawiki_api_url (str): Wikidata REST API by default. You can change it by replacing the `https://www.wikidata.org/w/api.php` with your own Wikibase URL.

	Returns:
		wb (WikibaseIntegrator): Wikibase Integrator session

	Examples:
		>>> wb = pyreslib.koha.wikibase_integrator_session_oauth2(consumer_token="{TOKEN}"", consumer_secret="{SECRET_TOKEN}" , mediawiki_api_url="https://www.wikidata.org/w/api.php")

	"""

	# Set up user-agent type
	wbi_config[
		"USER_AGENT"
	] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"

	# login using basic credentials
	try:
		login_instance = wbi_login.OAuth2(
			consumer_token=consumer_token,
			consumer_secret=consumer_secret,
			mediawiki_api_url=mediawiki_api_url,
		)
	except KeyError as e:
		print(f"KeyError during OAuth2 init: {e}")
		print(f"Consumer token: {consumer_token[:10]}..." if consumer_token else "None")
		print(f"API URL: {mediawiki_api_url}")
		raise

	wb = WikibaseIntegrator(login=login_instance)

	return wb


def convert_point_in_time_to_date(point_in_time: str, date_format=f"%Y-%m-%d") -> str:
	"""Returns a formatted date given a Wikibase [Point in time] string. The default format is `%y-%m-%d` according to the [datetime](https://docs.python.org/3/library/datetime.html) syntaxt. For `DD/MM/YYYY` format use `%d/%m/%y` instead.

	Args:
		point_in_time: Wikibase Point in Time string similar to ISO 8061 date, with the exception of + sign. The conversion only works for AD dates.
		date_format (str): `datetime` formatting string. Default set to ISO 8601 date.


	Returns:
		date (str): Formatted date.

	Examples:
		>>> point_in_time = "+2016-01-01T00:00:00Z"
		>>> date_value = convert_point_in_time_to_date(point_in_time)
		>>> print(date_value)
		>>> '2016-01-01'
	"""
	# extract date from Wikibase Point in time
	extracted_date = point_in_time[1:11]
	year = extracted_date.split("-")[0]
	month = extracted_date.split("-")[1]
	day = extracted_date.split("-")[2]
	date = ""
	# Convert missing date information to fit Koha date format.
	if day == "00":
		if month == "00":
			date = datetime.date(int(year), 1, 1).strftime(date_format)
		else:
			date = datetime.date(int(year), int(month), 1).strftime(date_format)
	else:
		date = datetime.date(int(year), int(month), int(day)).strftime(date_format)

	return date


def convert_qid_to_URI(qid: str, base_uri="http://wikidata.org/") -> str:
	"""Returns a QID string into the entity URI. By default the method uses the Wikidata Concept URI.

	Args:
		qid (str): Wikibase Point in Time string similar to ISO 8061 date, with the exception of + sign. The conversion only works for AD dates.
		base_uri (str): By default set to `http://wikidata.org/`.


	Returns:
		URI (str): URI of the entity.

	Examples:
		>>> qid = "Q1296"
		>>> print(convert_qid_to_URI(qid,base_uri="http://my.wikibase.org/"))
		>>> 'http://my.wikibase.org/Q1296'
	"""
	return f"{base_uri}{qid}"


def wb_get_property_data(wb_entity, pid: str, wikibase_URI=False, base_uri="http://wikidata.org/entity/", date_format: str = f"%Y-%m-%d") -> dict:
	"""
	Returns a dictionary with information related to statements, given a `WikibaseIntegrator` entity tied to a QID and a specific property PID.

	Args:
		wb_entity: `ItemEntity` object retrieved by using the `item.get()` WikibaseIntegrator method.
		pid (str): String indicating the PID of the property.
		wikibase_URI (bool): Returns full URI of Wikibase item. False by default.
		base_uri (str): Base Concept URI for the item. By default `http://wikidata.org/entity/`.
		date_format (str): `datetime` formatting string. Default set to ISO 8601 date.


	Returns:
		statements: List of dictionaries with statement values, qualifiers and references.

	Examples:
		>>> qid = "Q1296"
		>>> pid = "P1082"
		>>> wb_entity = wb.item.get(qid)
		>>> statements = wb_get_property_data(wb_entity,pid)
		>>> print(statements)
		>>> [{"value": "Q257029","references": [], "qualifiers": [{"pid": "P585","value": "2016-01-01"}]}, {"value": 230951,"references": [{"pid": "P143", "value": ""http://wikidata.org/"Q206855"}], "qualifiers": [{"pid": "P585","value": "2005-01-01"}]}  ]

	"""
	try:
		statements = []
		prop_values = wb_entity.claims.get(pid)
		for prop_value in prop_values:
			statements.append({"value": "","qualifiers": [], "references": []})
			# add statement value
			value = ""
			if prop_value.mainsnak.datavalue["type"] == "wikibase-entityid":
				if wikibase_URI:
					value = f"{base_uri}{prop_value.mainsnak.datavalue["value"]["id"]}"
				else:
					value = prop_value.mainsnak.datavalue["value"]["id"]

			elif prop_value.mainsnak.datavalue["type"] == "quantity":
				# get rid of + sing. This means that negative quantities are not supported!
				value = prop_value.mainsnak.datavalue["value"]["amount"][1:]
			elif prop_value.mainsnak.datavalue["type"] == "time":
				# convert to ISO 8061 date, meaning that point in time without day or month are set to 1.
				value = convert_point_in_time_to_date(point_in_time=prop_value.datavalue["value"]["time"],date_format=date_format)

			else:
				# strings, such as URLs
				value = prop_value.mainsnak.datavalue["value"]

			# append value
			statements[-1]["value"] = value


			# add references
			for reference in prop_value.references:
				value = ""
				reference_pid = list(reference.snaks.snaks.keys())[0]
				reference_dict = reference.snaks.snaks[reference_pid][0]
				if reference_dict.datavalue["type"] == "wikibase-entityid":
					if wikibase_URI:
						value = f"{base_uri}{reference_dict.datavalue["value"]["id"]}"
					else:
						value = reference_dict.datavalue["value"]["id"]

				elif reference_dict.datavalue["type"] == "quantity":
					# get rid of + sing. This means that negative quantities are not supported!
					value = reference_dict.datavalue["value"]["amount"][1:]
				elif reference_dict.datavalue["type"] == "time":
					# convert to ISO 8061 date, meaning that point in time without day or month are set to 1.
					value = convert_point_in_time_to_date(point_in_time=reference_dict.datavalue["value"]["time"],date_format=date_format)

				else:
					# strings, such as URLs
					value = reference_dict.datavalue["value"]

				# append reference
				statements[-1]["references"].append({"pid": reference_dict.property_number, "value": value})

			# add qualifiers
			for qualifier in prop_value.qualifiers:
				value = ""
				if qualifier.datavalue["type"] == "wikibase-entityid":
					if wikibase_URI:
						value = f"{base_uri}{qualifier.datavalue["value"]["id"]}"
					else:
						value = qualifier.datavalue["value"]["id"]

				elif qualifier.datavalue["type"] == "quantity":
					# get rid of + sing. This means that negative quantities are not supported!
					value = qualifier.datavalue["value"]["amount"][1:]
				elif qualifier.datavalue["type"] == "time":
					# convert to ISO 8061 date, meaning that point in time without day or month are set to 1.
					value = convert_point_in_time_to_date(point_in_time=qualifier.datavalue["value"]["time"],date_format=date_format)

				else:
					# strings, such as URLs
					value = qualifier.datavalue["value"]

				# append qualifier
				statements[-1]["qualifiers"].append({"pid": qualifier.property_number, "value": value})


			

		return statements
	except Exception:
		return []


def generate_qid_sorted_dict_and_list(auth_dict: list,exclude_types: list = [] ) -> list:
	"""
	Generates a list of dictionaries and a sorted list of IDs from Koha authorities.
	
	Args:
		auth_dict (list): Authorities list of dictionaries formatted according to [pyreslib.koha.import_koha_authorities_from_marc][] or [pyreslib.koha.import_koha_authorities_from_api][].
		exclude_types (list): Authority type codes to be excluded from the process. Default is empty list.

	Returns:
		auth_dict_sorted_qid, auth_qid_list (list): Sorted list of dictionaries for authorities and list of ids for bisect search.

	Examples:
		>>> auth_dict = pyreslib.koha.import_koha_authorities_from_api(session=koha_session,base_url=koha_base_url)
		>>> auth_dict_sorted_qid, auth_qid_list = pyreslib.wikidata.generate_qid_sorted_dict_and_list(auth_dict,exclude_types=["GEOGR_NAME","CHRON_TERM"])
		>>> auth_dict_sorted_qid
		>>> [{"auth_id": 20935, "wd_id": 6955, "record": {"leader": ... , "fields": [...]}}, ...]
		>>> auth_qid_list
		>>> [6955,...]

	"""
	filtered_auth_dict = []
	print(f"Excluding the following authority types: {", ".join([auth_type for auth_type in exclude_types])}")
	for auth in auth_dict:
		auth_type = koha.get_authority_type(record=auth["record"])
		if auth_type not in exclude_types + [None] :
			filtered_auth_dict.append(auth)


	filtered_dict_duplicate_qids = []
	for auth in filtered_auth_dict:
		if len(auth["wd_id"]) == 1:
			# single case
			filtered_dict_duplicate_qids.append({"auth_id": auth["auth_id"], "wd_id": auth["wd_id"][0], "record": auth["record"]})
		elif len(auth["wd_id"]) > 1:
			# multiple qids for authority, duplicate record in list
			for wd_id in auth["wd_id"]:
				filtered_dict_duplicate_qids.append({"auth_id": auth["auth_id"], "wd_id": wd_id, "record": auth["record"]})
		else:
			filtered_dict_duplicate_qids.append({"auth_id": auth["auth_id"], "wd_id": 0, "record": auth["record"]})

	auth_dict_sorted_qid = sorted(filtered_dict_duplicate_qids, key=lambda x: x["wd_id"])
	auth_qid_list = [auth["wd_id"] for auth in auth_dict_sorted_qid]

	print(f"Number of filtered authorities (with multiple QIDs duplicates: {len(auth_dict_sorted_qid)}")

	return auth_dict_sorted_qid, auth_qid_list


def retrieve_authority_from_qid(qid: str,auth_qid_list: list ,auth_dict_sorted_qid: list ) -> dict:
	"""
	Retrieves Koha authority metadata given a Wikidata QID

	Args:
		qid(str): Wikdiata QID value for entity.
		auth_qid_list (list): Sorted list of ids for bisect search generated from [pyreslib.wikidata.generate_qid_sorted_dict_and_list][].
		auth_dict_sorted_qid (list): Sorted list of dictionaries for authorities for bisect search generated from [pyreslib.wikidata.generate_qid_sorted_dict_and_list][].
		 
	Returns:
		auth (dict): Authority metadata or None if QID not present in catalogue.

	Examples:
		>>> auth_dict_sorted_qid, auth_qid_list = pyreslib.wikidata.generate_qid_sorted_dict_and_list(auth_dict,exclude_types=[])
		>>> qid = "Q6927"
		>>> pyreslib.wikidata.retrieve_authority_from_qid(qid,auth_qid_list,auth_dict_sorted_qid)
		>>> {"auth_id": 20936, "wd_id": [6927], "record": {"leader": ... , "fields": [...]}}	

	"""
	try:
		qid = int(qid.replace("Q",""))
		index = bisect_left(auth_qid_list,qid)
		if index != len(auth_qid_list) and auth_qid_list[index] == qid:
			return auth_dict_sorted_qid[index]
		else:
			print(f"Wikidata entity {qid} not found in Koha thesaurus")
			return None
	except ValueError:
		return None


def append_qid_to_qid_log(qid: str,qid_log: list, wb ):
	"""
	Appends metadata and occurrence information from a Wikidata entity which might become a candidate authority for the catalogue.
	
	The user can evaluate the final result in `data/wikidata/qid_log` folder.
	
	Args:
		qid(str): Wikdiata QID value for entity.
		qid_log (list): List of dictionaries holding metadata on Wikidata entities that could be part of the Koha thesaurus and their occurrence in statements.
		wb: Wikibase Integrator session generated via [pyreslib.wikidata.wikibase_integrator_session_basic][] or [pyreslib.wikidata.wikibase_integrator_session_oauth2][].
	
	Returns:
		qid_log (list): Updated qid_log list.
	"""

	if qid != "":
		# search if qid is already in log
		query_qid = list(filter(lambda x: x["qid"] == qid,qid_log))
		if len(query_qid) > 0:
			# append value
			query_qid[0]["occurrence"] += 1
		else:
			# add new qid to log list
			wd_entity = wb.item.get(qid,max_retries=15,retry_after=10)
			try:
				instance_of = wd_entity.claims.get("P31")[0].mainsnak.datavalue['value']["id"]
			except (IndexError,AttributeError):
				instance_of = ""
			try:
				description = wd_entity.descriptions.get("en").value
			except (IndexError,AttributeError):
				description = ""

			try:
				label = wd_entity.labels.get("en").value
			except (IndexError,AttributeError):
				label = ""
			qid_log.append({"qid": qid, "occurrence": 1,
			 "label": label,
			  "description": description ,
			  "instance_of": instance_of,
			   "uri": "http://wikidata.org/entity/" + qid } 
			   )

	return qid_log 		   	


def external_sources_metadata_authorities(
	auth_dict,
	wb,
	backup_auth_dir: str = os.path.join("data","wikidata","backup_auth"),
	changed_auth_dir: str = os.path.join("data","wikidata","changed_auth"),
	external_ids_mapping_filepath: str = os.path.join("data","mappings","lod","external_identifiers.json"),
	uri_field: list =["024","1"],
	source_subfield: str ="2",
	label_subfield: str ="9",
	id_subfield: str="a"):
	"""
	Given a list of External identifiers, by default stored in `data/mappins/lod/external_identifiers.json`, authorities' 024 fields are enhanced with extra metadata such as source, label and id.
	
	Args:
		auth_dict (list): Authorities list of dictionaries formatted according to [pyreslib.koha.import_koha_authorities_from_marc][] or [pyreslib.koha.import_koha_authorities_from_api][].
		wb: Wikibase Integrator session generated via [pyreslib.wikidata.wikibase_integrator_session_basic][] or [pyreslib.wikidata.wikibase_integrator_session_oauth2][].
		external_ids_mapping_filepath (str): Path to external ids mapping JSON.
		source_subfield(str): Koha subfield where the name of the external source is recorded. Default is "2", but you can change it according to your MARC framework.
		label_subfield(str): Koha subfield where the label of the external source is recorded. Default is "9", but you can change it according to your MARC framework.
		id_subfield(str): Koha subfield where the id of the external source is recorded. Default is "a", but you can change it according to your MARC framework.

	Returns:
		changed_authorities, backup_authorities (list): Lists of dictionaries for the enhanced authorities and their backups. You can locally store, or submit the changes to the catalogue via the API later on.		
	
	Examples:
		>>> auth_dict = pyreslib.koha.import_koha_authorities_from_api(session=koha_session,base_url=koha_base_url)
		>>> changed_authorities, backup_authorities  = pyreslib.wikidata.external_sources_metadata_authorities(auth_dict=auth_dict)
		>>> changed_authorities
		>>> [{{"auth_id": 34922,"wd_id": [254], "record": {... "fields": {"024": {... "subfields": [{"1": "http://www.wikidata.org/entity/Q254"},{"9": "Wolfgang Amadeus Mozart"},{"a": "Q254"},{"2": "Wikidata"} } ... ]} ...]
		>>> backup_authorities
		>>> >>> [{{"auth_id": 34922,"wd_id": [254], "record": {... "fields": {"024": {... "subfields": [{"1": "http://www.wikidata.org/entity/Q254"}] ...} ]
	"""
	# import external mapping file
	external_ids_mapping = utilities.json2dict(external_ids_mapping_filepath)

	# initialize changed authorities and their backup lists.
	changed_authorities = []
	backup_authorities = []

	for auth in auth_dict:
		modified = False
		# look for URI field
		backup_auth = deepcopy(auth)
		query_uri_field = list(filter(lambda x: uri_field[0] in x.keys(), auth["record"]["fields"] ))
		if len(query_uri_field) > 0:
			for uri in query_uri_field:
				# get current subfields
				try:
					uri_value = list(filter(lambda x: uri_field[1] in x.keys(), uri[uri_field[0]]["subfields"]))[0][uri_field[1]]
					if uri_value.split("/")[-1] != "": # exclude empty URI, like wikidata.org/entity/
						source_value = list(filter(lambda x: source_subfield in x.keys(), uri[uri_field[0]]["subfields"]))
						label_value = list(filter(lambda x: label_subfield in x.keys(), uri[uri_field[0]]["subfields"]))
						id_value = list(filter(lambda x: id_subfield in x.keys(), uri[uri_field[0]]["subfields"]))
						# if incomplete information
						if any(len(subfield) == 0 for subfield in [source_value,label_value,id_value]):
							# query values from URI
							for external_source in external_ids_mapping:
								if external_source["domain_name"] in uri_value:
									# found source
									# add source
									if len(source_value) > 0:
										modified = True
										source_value[0][source_subfield] = external_source["source"]
									else:
										modified = True
										uri[uri_field[0]]["subfields"].append({source_subfield: external_source["source"]})
									# add identifier
									if len(id_value) > 0:
										modified = True
										id_value[0][id_subfield] = uri_value.split("/")[-1]
									else:
										modified = True
										uri[uri_field[0]]["subfields"].append({id_subfield: uri_value.split("/")[-1]})
									# add label (only wikidata)
									if external_source["source"] == "Wikidata":
										try:
											entity = wb.item.get(uri_value.split("/")[-1])
											try:
												modified = True
												label = entity.labels.get('en').value
												if len(label_value) > 0:
													label_value[0][label_subfield] = label								
												else:
													modified = True
													uri[uri_field[0]]["subfields"].append({label_subfield: label})
											except AttributeError:
												pass
										except ValueError:
											pass

									break


				except IndexError:
					continue

		if modified:
			# adding changes
			print(f"Adding changes for {auth["auth_id"]}...")
			backup_authorities.append(backup_auth)
			changed_authorities.append(auth)
			#print(backup_authorities[-1])
			#print(changed_authorities[-1])
			#input()
			

	print("Saving to JSON...")

	utilities.dict2json(
	    backup_authorities,
	    os.path.join(
	        backup_auth_dir,
	        f"backup_auth-{utilities.get_current_date()}.json"
	    ),
	)

	utilities.dict2json(
	    changed_authorities,
	    os.path.join(
	        changed_auth_dir,
	        f"changed_auth-{utilities.get_current_date()}.json"
	    )
	)			


	return backup_authorities,changed_authorities

def enhance_authorities_via_wikidata(
	auth_dict: list,
	wb,
	auth_id_range: list = {"min": 1,"max": None},
	backup_frequency: int = 10,
	qid_log_dir: str = os.path.join("data","wikidata","qid_log"),
	wikidata_koha_mapping_filepath: str = os.path.join("data","mappings","wikidata","wikidata-koha-properties.csv"),
	wikibase_base_url: str = "http://wwww.wikidata.org/entity/",
	backup_auth_dir: str = os.path.join("data","wikidata","backup_auth"),
	changed_auth_dir: str = os.path.join("data","wikidata","changed_auth"),
	in_progress: bool = False,
	exclude_types: list = [],
	koha_fields: dict = {"PERSO_NAME": "500","CORPO_NAME": "510","CHRON_TERM": "548","TOPIC_TERM": "550","GEOGR_NAME": "551"},
	headings: dict = {"PERSO_NAME": "100","CORPO_NAME": "110","CHRON_TERM": "148","TOPIC_TERM": "150","GEOGR_NAME": "151"}
	):
	"""
	Generates a list of dictionaries of enhanced authorities and their backups to be later submitted via the Koha API.

	Args:
		auth_dict (list): Authorities list of dictionaries formatted according to [pyreslib.koha.import_koha_authorities_from_marc][] or [pyreslib.koha.import_koha_authorities_from_api][].
		wb: Wikibase Integrator session generated via [pyreslib.wikidata.wikibase_integrator_session_basic][] or [pyreslib.wikidata.wikibase_integrator_session_oauth2][].
		auth_id_range (dict): Minimal and maximal authority id number for enhancement, previous and subsequent ones will be ignored. Default is {"min": 1,"max": None}, meaning all catalogue is going to be exposed to enhancement.
		backup_frequency (int): Backup frequency.
		wikidata_koha_mapping_filepath (str): Path to Wikidata-Koha mapping CSV.
		wikibase_base_url(str): Base URL for Wikibase instance. Default is wikidata URI "http://wwww.wikidata.org/entity/".
		backup_auth_dir (str): Destination path for backup enhanced authorities as JSON.
		changed_auth_dir (str): Destination path for changed enhanced authorities as JSON.
		in_progress(bool): Retrieves latest files in `data/wikidata/changed_auth` and `data/wikidata/backup_auth`. Default is `False`.
		exclude_types (list): Authority type codes to be excluded from the process. Default is empty list.
		koha_fields (dict): Fields for umbrella terms statements for authority record. Default list is definined according to the 5XX MARC21 framework.
		headings (dict): Fields for main heading statements for authority record. Default list is definined according to the 1XX MARC21 framework. 

	Returns:
		changed_authorities, backup_authorities (list): Lists of dictionaries for the enhanced authorities and their backups. You can locally store, or submit the changes to the catalogue via the API later on.		
	
	Examples:
		>>> auth_dict = pyreslib.koha.import_koha_authorities_from_api(session=koha_session,base_url=koha_base_url)
		>>> changed_authorities, backup_authorities  = pyreslib.wikidata.external_sources_metadata_authorities(auth_dict=auth_dict)
		>>> changed_authorities
		>>> [{{"auth_id": 34922,"wd_id": [254], "record": {... "fields": [...,{ ... } ...] }
		>>> backup_authorities
		>>> >>> [{{"auth_id": 34922,"wd_id": [254], "record": {... "fields": [..., { ... } ] }
	"""


	# import Wikidata-Koha properties mapping from CSV
	print(f"Importing mapping CSV {wikidata_koha_mapping_filepath}...")
	wikidata_koha_mapping = utilities.csv2dict(wikidata_koha_mapping_filepath)

	n_authorities = len(auth_dict)
	print(f"Number of authorities: {n_authorities}")
	current_auth = 0
	if in_progress is not True:
		backup_authorities = []
		changed_authorities = []
		qid_log = []
	else:
		# get latest backup and changed
		print(f"Importing latest backup, changed and qid_log dictionaries...")
		backup_authorities = utilities.json2dict(get_latest_file(backup_auth_dir))
		changed_authorities = utilities.json2dict(get_latest_file(changed_auth_dir))   
		qid_log = utilities.csv2dict(get_latest_file(qid_log_dir))
		# transform qid_log occurrence field to int
		for entry in qid_log:
			entry["occurrence"] = int(entry["occurrence"])

	print("Sorting authorities according to their QID...")
	auth_dict_sorted_qid,auth_qid_list = generate_qid_sorted_dict_and_list(auth_dict,exclude_types=exclude_types)

	# Counters for partial backups, and measuring operation.
	backup_counter = 0
	start_time = time()

	if auth_id_range["max"] is None:
		# assign last authority id
		auth_id_range["max"] = int(auth_dict[-1]["auth_id"]) +1

	print("Enhancing authorities with Wikidata data...")

	for auth in auth_dict:
		current_auth +=1
		if int(auth["auth_id"]) < auth_id_range["min"]:
			continue
		elif int(auth["auth_id"]) > auth_id_range["max"]:
			break	
		else:
			print(f"\n\n####### CURRENT AUTHORITY: {auth["auth_id"]} {float(current_auth)/n_authorities*100}%")
			# check if authority is already in backup_authorities
			if in_progress is True:
				backup_query = list(filter(lambda x: x["auth_id"] == auth["auth_id"], backup_authorities))
				if len(backup_query) > 0:
					print("Authority already processed, skipping...")
					continue

			# exclude if belongs to exclude_types
			auth_type = koha.get_authority_type(auth["record"])
			if auth_type in exclude_types + [None]:
					print("Excluding authority from enhancement...")
					continue

			backup_auth = deepcopy(auth)
			changed_record = False
			if len(auth["wd_id"]) >0:
				for qid in auth["wd_id"]:
					qid = "Q"+str(qid)
					print(f"QID: {qid}")
					# get wikidata entity associated with authority
					try:
						entity = wb.item.get(qid,max_retries=10,retry_after=5)
					except Exception:
						entity = None
					# get properties from mapping according to auth_type (source field)
					properties = list(filter(lambda x: x["type_source"] == auth_type, wikidata_koha_mapping))

					if entity is not None:
						# query Wikidata for each property
						for prop in properties:
							pid = prop["pid"]
							#print(f"CURRENT PROPERTY: {pid}")
							query = wb_get_property_data(entity, pid)
							for value in [q["value"] for q in query]:
								if value != "":
									print(f"Queried value: {value}")
									if "wikidata.org" in value:
										value_uri = value
										value_qid = value.split("/")[-1]
									else:
										value_uri = wikibase_base_url + value
										value_qid = value

									if value_qid != qid: # exclude reflective statements.	
										#1. value is already in authority record, but no $i subfield --> Add value_i_subfield
										# search QID value in authority record field
										try:
											field = koha_fields[prop["type_target"]]
											field_query = list(filter(lambda x: field in x.keys(),auth["record"]["fields"]))

											if len(field_query) > 0: # statement(s) in authority

												for statement in field_query:
													#print(statement)
													#print(statement[field])
													subfield_query = list(filter(lambda x: "1" in x.keys(),statement[field]["subfields"]))
													for subfield_1 in subfield_query:
														if subfield_1["1"] == value_uri:
															# check if $i subfield is already filled
															subfield_i_query = list(filter(lambda x: "i" in x.keys(),statement[field]["subfields"]))
															try:
																if subfield_i_query[0]["i"] != "":
																	#2. value is already in authority record, and $i is filled --> skip
																	continue
																else:
																	#value is already in authority record, but no $i subfield --> Add value_i_subfield
																	subfield_i_query[0]["i"] = prop["value_i_subfield"]
																	changed_record = True


															except IndexError:
																#value is already in authority record, but no $i subfield --> Add value_i_subfield
																statement[field]["subfields"].append({"i": prop["value_i_subfield"]})
																changed_record = True

											else: # statement not in authority
												# add authority statement, if QID matches an existing authority
												retrieved_authority = retrieve_authority_from_qid(value_qid,auth_qid_list,auth_dict_sorted_qid)
												if retrieved_authority is None:
													print(f"Value {value_qid} not found in Koha thesaurus. Adding it to log list...")
													append_qid_to_qid_log(value_qid,qid_log,wb)
												else:
													# value is in the authority
													print(f"Found authority {retrieved_authority["auth_id"]}. Adding it as statement for {auth["auth_id"]}...")
													try:
														retrieved_authority_heading = list(filter(lambda x: headings[prop["type_target"]] in x.keys(), retrieved_authority["record"]["fields"] ))
														retrieved_authority_heading = retrieved_authority_heading[0][headings[prop["type_target"]]]["subfields"][0]["a"]
														#print(retrieved_authority_heading)
														#input()
														print(f"a: {retrieved_authority_heading} \n 9: {retrieved_authority["auth_id"]} \n i: {prop["value_i_subfield"]} ")
														auth["record"]["fields"].append({field: {"ind2": " ","ind1": " ", "subfields": [{"a": retrieved_authority_heading ,"9": retrieved_authority["auth_id"] ,"i": prop["value_i_subfield"] }]}})
														changed_record = True

													except Exception:
														pass

										except KeyError:
											continue

									else:
										print(f"Excluding reflective statement for {qid}")

			else:
				continue

			print(f"Changed record: {changed_record}")
			if changed_record is True:
				backup_authorities.append(backup_auth)
				changed_authorities.append(auth)
				print(changed_record)
				backup_counter +=1
				if backup_counter == backup_frequency:
					print("\n\n BACKING UP...")
					# Saving to JSON...
					utilities.dict2json(
						backup_authorities,
						os.path.join(
							backup_auth_dir, "backup_auth-" + utilities.get_current_date() + ".json"
						),
					)
					utilities.dict2json(
						changed_authorities,
						os.path.join(
							changed_auth_dir, "changed_auth-" + utilities.get_current_date() + ".json"
						),
					)
					# Saving to CSV
					utilities.dict2csv(qid_log,os.path.join(qid_log_dir,f"qid_log-{utilities.get_current_date()}.csv"))

					backup_counter = 0

				#print(f"Changed authority: {changed_authorities[-1]} \n\n")
				#input()


	

	# Saving qid_log
	print(f"Saving QIDs log file to {qid_log_dir}")
	utilities.dict2csv(qid_log,os.path.join(qid_log_dir,f"qid_log-{utilities.get_current_date()}.csv"))

	print(f"Enhancing completed in {float(time() - start_time)/60} minutes.")

	# return backup and changed_authorities
	return backup_authorities,changed_authorities

def generate_statistics_authorities_wikidata_enhancement(
	changed_authorities: list,
	statistics_filepath: str = os.path.join("data","wikidata","statistics",f"statistics-{utilities.get_current_date()}.json"),
	wikidata_koha_mapping_filepath: str = os.path.join("data","mappings","wikidata","wikidata-koha-properties.csv"),
	koha_fields: dict ={"PERSO_NAME": "500","CORPO_NAME": "510","CHRON_TERM": "548","TOPIC_TERM": "550","GEOGR_NAME": "551"},
	authority_types:list =["PERSO_NAME","CORPO_NAME","CHRON_TERM","TOPIC_TERM","GEOGR_NAME"],
	wd_property_subfield: str = "i"):
	"""
	Generates a JSON file that records statistics for the Wikidata enhanchement, such as number of authorities modified and the type of statements ingested.

	Args:
		changed_authorities(list): Lists of dictionaries for the enhanced authorities.
		statistics_filepath (str): Path to output JSON file. Default is `data/wikidata/statistics`.
		wikidata_koha_mapping_filepath (str): CSV file with Wikidata-Koha mapping of properties and fields. Default is `data/mappings/wikidata/wikidata-koha-properties.csv`.
		koha_fields (dict): Fields for umbrella terms statements for authority record. Default list is defined according to the 5XX MARC21 framework.
		authority_types (list): List of authority type codes, according to MARC21 framework.
		wd_property_subfield (str): Subfield where the Wikidata property URI is stored. Default is "i", to be set in MARC framework for every authority.

	Returns:
		statistics (dict): Dictiorary of the statistics.
	"""

	# import mapping from CSV
	wikidata_koha_mapping = utilities.csv2dict(wikidata_koha_mapping_filepath)

	statistics = {"authorities": {"n_changed_authorities": 0, "authority_types": [{auth_type: 0} for auth_type in authority_types] }, "wikidata_properties": [{wd_property["value_i_subfield"]: 0} for wd_property in wikidata_koha_mapping] }

	for auth in changed_authorities:
		statistics["authorities"]["n_changed_authorities"] += 1

		# get authority type
		auth_type = koha.get_authority_type(auth["record"])

		if auth_type is not None:

			# increment occurrence of authority type:
			list(filter(lambda x: auth_type in x.keys(),statistics["authorities"]["authority_types"] ))[0][auth_type] +=1

			# count wikidata property statements
			for field in list(koha_fields.values()):
				field_query = list(filter(lambda x: field in x.keys(),auth["record"]["fields"]))
				if len(field_query) > 0 :
					for statement in field_query:
						i_subfield_query = list(filter(lambda x: wd_property_subfield in x.keys(),statement[field]["subfields"]))
						if len(i_subfield_query) >0:
							wd_property = i_subfield_query[0][wd_property_subfield]
							# found wikidata property statement, append to statistics
							property_query = list(filter(lambda x: wd_property in x.keys(),statistics["wikidata_properties"]))
							if len(property_query) > 0:
								# append occurence
								property_query[0][wd_property] +=1

	# saving statistics
	print(f"Saving statistics to {statistics_filepath}")
	utilities.dict2json(statistics,statistics_filepath)


	return statistics

def update_enhanced_authorities(
	koha_session,
	koha_base_url: str,
	changed_auth_filepath: str = os.path.join("data","wikidata","changed_auth",f"changed_auth-{utilities.get_current_date()}.json"),
	ckeck_updates: int = 5
	):
	"""
	Submit enhanced authorities via Koha API from JSON list after review.

	Args:
		changed_auth_filepath(str): Filepath of the `changed_auth-{yyyy-mm-dd}.json` file. Default is `data/wikidata/changed_auth` directory.
		koha_session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
		koha_base_url (str): Koha API url from credentials.
		check_updates (int): Number of checks before batch. To be manually done by user in Koha Staff interface.
	Returns:
		None

	Examples:

	"""
	# import changed authorities
	changed_auth = utilities.json2dict(changed_auth_filepath)
	# put each authority back to Koha via API
	n_auth = len(changed_auth)
	check = 0
	for auth in changed_auth: 
		print(f"Current authority {((changed_auth.index(auth) +1) / n_auth)*100 } % : {auth["auth_id"]}")
		koha.update_authority_marc(session=koha_session, auth_id= auth["auth_id"], marc_json= auth["record"], base_url= koha_base_url)
		if check <= ckeck_updates:
			check +=1
			input("Check the authority, then press ENTER to continue update.")
		else:
			pass 

	return None