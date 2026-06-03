import requests
from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import json
import os
import datetime

import statistics as stat

from wikibaseintegrator import wbi_login, WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from SPARQLWrapper import SPARQLWrapper, JSON

from bisect import bisect_left

from multiprocessing import Pool, cpu_count
from typing import List, Dict, Any
import traceback


### TO-DO
"""
1. Import umbrella terms to authority from Wikidata based on mapping.
2. Import Wikidata description into catalogue record (append to field 500$a).
3. Import authorities from OpenRefine CSV reconciliation list with headers = {"auth_id","auth_main_heading","qid","wd_uri","wd_label"} 

"""


def wikibase_integrator_session_basic(
	username: str,
	password: str,
	mediawiki_api_url="https://www.wikidata.org/w/rest.php/wikibase/v1",
):
	"""Returns an wikibase_integrator session, given user and password of your Wikidata account. We advice to create a Wikidata user in oder to prevent a "Too Many Requests HTTP 429" code.

	Args:
		username (str): Username associated with your Wikidata user.
		password (str): Password associated with your Wikidata user.
		mediawiki_api_url (str): Wikidata REST API by default. You can change it by replacing the `https:wikidata.org/` with your own Wikibase URL.

	Returns:
		wb (WikibaseIntegrator): Wikibase Integrator session

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
	mediawiki_api_url="https://www.wikidata.org/w/rest.php/wikibase/v1",
):
	"""Returns an wikibase_integrator session, given API consumer token and secret keys of your Wikidata account. You have to make a request to Wikimedia via this [URL](https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose/oauth2) in order to have such credentials. For advanced use only.

	Args:
		consumer_token (str): API consumer key associated with your Wikidata user.
		consumer_secret (str): API secret key associated with your Wikidata user.
		mediawiki_api_url (str): Wikidata REST API by default. You can change it by replacing the `https:wikidata.org/` with your own Wikibase URL.

	Returns:
		wb (WikibaseIntegrator): Wikibase Integrator session

	Examples:
		>>> wb = pyreslib.koha.wikibase_integrator_session_basic(username="{USERNAME}"", password="{PASSWORD}" , mediawiki_api_url="https://www.wikidata.org/w/rest.php/wikibase/v1")

	"""

	# Set up user-agent type
	wbi_config[
		"USER_AGENT"
	] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"

	# login using basic credentials
	login_instance = wbi_login.OAuth2(
		consumer_token=username,
		consumer_secret=password,
		mediawiki_api_url=mediawiki_api_url,
	)

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
	# Convert missing date information to fit Koha date format.
	if day == "00":
		if month == "00":
			return datetime.date(year, 1, 1).strftime(date_format)
		else:
			return datetime.date(year, month, 1).strftime(date_format)
	else:
		return datetime.date(year, month, day).strftime(date_format)


def convert_qid_to_URI(qid: str, base_uri="http://wikidata.org/") -> str:
	"""Returns a a QID string into the entity URI. By default the method uses the Wikidata Concept URI.

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


def wb_get_property_data(wb_entity, pid: str, wikibase_URI=True, base_uri="http://wikidata.org/", date_format: str = f"%Y-%m-%d") -> dict:
	"""Returns a dictionary with information related to statements, given a WikibaseIntegrator entity tied to a QID, and a specific property PID.

	Args:
		wb_entity: `ItemEntity` object retrieved by using the `item.get()` WikibaseIntegrator mwethod.
		pid (str): String indicating the PID of the property.
		wikibase_URI (bool): Returns full URI of Wikibase item. True by default.
		base_uri (str): Base Concept URI for the item. By default `http://wikidata.org/`.
		date_format (str): `datetime` formatting string. Default set to ISO 8601 date.


	Returns:
		statements: List of dictionaries with statement values, qualifiers and references.

	Examples:
		>>> qid = "Q1296"
		>>> pid = "P1082"
		>>> wb_entity = wb.item.get(qid)
		>>> statements = wb_get_property_data(wb_entity,pid)
		>>> print(statements)
		>>> [{"value": 257029,"references": [], "qualifiers": [{"pid": "P585","value": "2016-01-01"}]}, {"value": 230951,"references": [{"pid": "P143", "value": ""http://wikidata.org/"Q206855"}], "qualifiers": [{"pid": "P585","value": "2005-01-01"}]}  ]

	"""
	try:
		statements = []
		prop_values = entity.claims.get(pid)
		for prop_value in prop_values:
			statements.append({"value": "","qualifiers": [], "references": []})
			# add statement value
			value = ""
			if prop_value.datavalue["type"] == "wikibase-entityid":
				if wikibase_URI:
					value = f"{base_uri}{prop_value.datavalue["value"]["id"]}"
				else:
					value = prop_value.datavalue["value"]["id"]

			elif prop_value.datavalue["type"] == "quantity":
				# get rid of + sing. This means that negative quantities are not supported!
				value = prop_value.datavalue["value"]["amount"][1:]
			elif prop_value.datavalue["type"] == "time":
				# convert to ISO 8061 date, meaning that point in time without day or month are set to 1.
				value = convert_point_in_time_to_date(point_in_time=prop_value.datavalue["value"]["time"],date_format=date_format)

			else:
				# strings, such as URLs
				value = prop_value.datavalue["value"]

			# append value
			statements[-1]["value"] = value


			# add references
			for reference in prop_value.references:
				value = ""
				if reference.datavalue["type"] == "wikibase-entityid":
					if wikibase_URI:
						value = f"{base_uri}{reference.datavalue["value"]["id"]}"
					else:
						value = reference.datavalue["value"]["id"]

				elif reference.datavalue["type"] == "quantity":
					# get rid of + sing. This means that negative quantities are not supported!
					value = reference.datavalue["value"]["amount"][1:]
				elif reference.datavalue["type"] == "time":
					# convert to ISO 8061 date, meaning that point in time without day or month are set to 1.
					value = convert_point_in_time_to_date(point_in_time=reference.datavalue["value"]["time"],date_format=date_format)

				else:
					# strings, such as URLs
					value = reference.datavalue["value"]

				# append reference
				statements[-1]["references"].append({"pid": reference.property_number, "value": value})

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
