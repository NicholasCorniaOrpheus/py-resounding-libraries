from pyreslib import koha
from pyreslib import utilities

import pyorcid
import orcid

"""
Series of scripts that interact with the ORCiD API. It aligns and updates research output from and
to Koha catalogue into individual ORCiD accounts of researchers belonging to the institution.
"""

def orcid_person_session(
	orcid_id: str,
	secret_key: str):
	"""
	Returns a session using the orcid/pyorcid libraray
	"""
	pass 


def generate_researchers_list_from_public_report(
	koha_public_report_url:str,
	koha_report_id: int # 94 in my istance,
	koha_session,
	koha_base_url: str,
	orcid_base_url: str = "http://orcid.org/",
	orcid_id_format: str = "0000-0000-0000-0000",
	koha_fields_mapping: dict = {
		"label": "100$a", 
		"auth_id": "001", 
		"orcid_uri": "024$1", # one of this two is mandatory!
		"orcid_id": "024$a"
		}
	) -> list:
	
	# Get public report from koha
	# Get Koha report data, as raw list of list of the form [ [value], [value2] ...]
    response = koha_session.get(f"{koha_public_report_url}{str(koha_report_id)}")
    # avoid duplicates
    auth_ids = list(set([i[0] for i in response.json()]))

    researchers = []
    for auth_id in auth_ids:
    	# Extract metadata information for each researcher from Koha API and according to mapping
    	auth_metadata = koha.get_authority_marc(koha_session,int(auth_id),koha_base_url)

    	# Extract relevant metadata for researchers. Filter out the orcid_id or uri based on base URL and format  
    	researcher = {}
    	for key in koha_fields_mapping:
    		field = koha_fields_mapping[key].split("$")[0]
    		try:
    			subfield = koha_fields_mapping[key].split("$")[1]
    		except IndexError:
    			subfield = None
    		# extract relevant field/subfield
    		query_field = list(filter(lambda x: field in x.keys(),auth_metadata["fields"]))
    		
    		if len(query_field) > 0:
    			for statement in query_field:
    				if subfield is not None:
    					# get subfield value, assuming only one!
    					query_subfields = list(filter(lambda x: subfield in x.keys(), statement[field]["subfields"]))
    					value = query_subfields[0][subfield]

    				else:
    					value = statement[field]

    				# check if the value is conform with orcid_base_url or orcid_id format
    				# add value to corresponding key in researcher

    	researchers.append(researcher)


    return researchers 


def generate_research_output_list_from_public_report(
	koha_public_report_url:str,
	koha_report_id: int # 95 in my istance,
	koha_session,
	koha_base_url: str,
	koha_orcid_mapping_filepath: str = "./data/mappings/orcid/koha2orcid.json"
	) -> list :

	# Get public report from koha
	# Get Koha report data, as raw list of list of the form [ [value], [value2] ...]
    response = koha_session.get(f"{koha_public_report_url}{str(koha_report_id)}")
    biblio_ids = [i[0] for i in response.json()]

    # Import koha_orcid mapping as dictionary

    koha_orcid_mapping = utilities.json2dict(koha_orcid_mapping_filepath)

    research_outputs = []
    for biblio_id in biblio_ids:
    	# Extract metadata information for each research output from Koha API
    	biblio_metadata = koha.get_biblio_marc(koha_session,int(biblio_id),koha_base_url)

    	# Extract relevant metadata for researchers. Filter out the orcid_id or uri based on base URL and format  
    	research_output = {}
    	for key in koha_orcid_mapping:
    		field = koha_orcid_mapping[key].split("$")[0]
    		try:
    			subfield = koha_orcid_mapping[key].split("$")[1]
    		except IndexError:
    			subfield = None
    		# extract relevant field/subfield
    		query_field = list(filter(lambda x: field in x.keys(),biblio_metadata["fields"]))
    		
    		### TO BE CONTINUED
    		if len(query_field) > 0:
    			for statement in query_field:
    				if subfield is not None:
    					# get subfield value, assuming only one!
    					query_subfields = list(filter(lambda x: subfield in x.keys(), statement[field]["subfields"]))
    					value = query_subfields[0][subfield]

    				else:
    					value = statement[field]

    			

    	research_outputs.append(research_output)


    	...

	







  


