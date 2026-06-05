from pyreslib import koha
from pyreslib import utilities

import os, json, re
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

# Load entry types from JSON
with open(
    os.path.join("data", "mappings", "bibtex", "koha_entry_types.json"), "r"
) as f:
    entry_type_mapping = json.load(f)


def convert_biblio_to_bibtex(
    biblio_id: int,
    bibtex_filepath: str,
    koha_session,
    base_url: str,
):
    """
    Converts MARC-in-JSON record from Koha API into BibTeX file.

    Args:
        biblio_id (int): Unique idenfier for the record in Koha catalogue.
        bibtex_filepath (str): String filepath indicating the location where the .bib output has to be stored.
        koha_session (oauth2): Oauth2 session provided by `pyreslib.koha.oauth2_session` method.
        base_url (str): Koha API url from credentials.

    Returns:
        `None`

    Examples:

    """

    # get MARC-in-JSON record
    record = koha.get_biblio_marc(
        session=koha_session, biblio_id=biblio_id, base_url=base_url
    )

    # get marc biblio type
    entry_type = entry_type_mapping[koha.get_biblio_type(record)]

    # generate BibTeX entry according to type

    entry = {}

    entry_id = (
        get_authors(record).split(" ")[0].lower()
        + "_"
        + get_title(record).replace(" ", "").lower()[:10]
        + "_"
        + get_year(record)
    )

    if entry_type == "article":
        entry = {
            "ENTRYTYPE": entry_type,
            "ID": entry_id,
            "author": get_authors(record),
            "title": get_title(record),
            "journal": get_journal(record),
            "year": str(get_year(record)),
            "volume": get_volume(record),
            "number": get_issue_number(record),
            "issn": get_issn(record),
            "pages": get_pages(record),
            "url": get_url(record),
            "doi": get_doi(record),
            "keywords": get_keywords(record),
            "abstract": get_abstract(record),
            "note": get_note(record),
            "type": entry_type,
            "howpublished": get_howpublished(record),
        }

    elif entry_type == "book":
        entry = {
            "ENTRYTYPE": entry_type,
            "ID": entry_id,
            "author": get_authors(record),
            "title": get_title(record),
            "publisher": get_publisher(record),
            "address": get_address(record),
            "year": str(get_year(record)),
            "isbn": get_isbn(record),
            "pages": get_pages(record),
            "url": get_url(record),
            "doi": get_doi(record),
            "keywords": get_keywords(record),
            "abstract": get_abstract(record),
            "note": get_note(record),
            "type": entry_type,
            "howpublished": get_howpublished(record),
        }

    elif entry_type == "incollection":
        entry = {
            "ENTRYTYPE": entry_type,
            "ID": entry_id,
            "author": get_authors(record),
            "title": get_title(record),
            "booktitle": get_booktitle(record),
            "publisher": get_publisher(record),
            "address": get_address(record),
            "year": str(get_year(record)),
            "isbn": get_isbn(record),
            "pages": get_pages(record),
            "url": get_url(record),
            "doi": get_doi(record),
            "keywords": get_keywords(record),
            "abstract": get_abstract(record),
            "note": get_note(record),
            "type": entry_type,
            "howpublished": get_howpublished(record),
        }

    elif entry_type == "misc":
        entry = {
            "ENTRYTYPE": entry_type,
            "ID": entry_id,
            "author": get_authors(record),
            "title": get_title(record),
            "publisher": get_publisher(record),
            "address": get_address(record),
            "year": str(get_year(record)),
            "url": get_url(record),
            "doi": get_doi(record),
            "keywords": get_keywords(record),
            "abstract": get_abstract(record),
            "note": get_note(record),
            "type": entry_type,
            "howpublished": get_howpublished(record),
        }

    elif entry_type == "phdthesis":
        entry = {
            "ENTRYTYPE": entry_type,
            "ID": entry_id,
            "author": get_authors(record),
            "title": get_title(record),
            "school": get_school(record),
            "address": get_address(record),
            "year": str(get_year(record)),
            "pages": get_pages(record),
            "url": get_url(record),
            "doi": get_doi(record),
            "keywords": get_keywords(record),
            "abstract": get_abstract(record),
            "note": get_note(record),
            "type": entry_type,
            "howpublished": get_howpublished(record),
        }
    else:
        raise ValueError(f"No entry_type found for biblio_id {biblio_id}")

    # generate single bibtex file
    bibtex_db = BibDatabase()
    # initialize BibTeX writer
    bibtex_writer = BibTexWriter()

    # add entries to database
    bibtex_db.entries = [entry]

    with open(bibtex_filepath, "w") as bibfile:
        bibfile.write(bibtex_writer.write(bibtex_db))


def latex_normalize(input_string):
    special_chars = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\^{}",
        "\\": r"\textbackslash{}",
    }

    pattern = re.compile("|".join(re.escape(key) for key in special_chars.keys()))
    normalized_string = pattern.sub(lambda x: special_chars[x.group()], input_string)

    return normalized_string


# CONVERT FUNCTIONS MARC2BIBTEX

### I am assuming a record as marc-in-json format


def get_abstract(record_dict, field="520", subfield="a"):
    abstract = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            abstract = subfield_query[0][subfield]

    return abstract


country_codes = utilities.csv2dict(
    os.path.join("data", "mappings", "bibtex", "country_codes.csv")
)

country_acronyms = {}

for country in country_codes:
    country_acronyms[country["code"]] = country["label"]


def get_address(
    record_dict,
    field="260",
    subfield="a",
    country_field="044",
    country_subfield="a",
    acronyms_mapping=country_acronyms,
):
    address = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            address = subfield_query[0][subfield]

        else:  # case of country of publication field 044$a
            filter_query = list(
                filter(lambda x: country_field in x.keys(), record_dict["fields"])
            )

            if len(filter_query) > 0:
                subfield_query = list(
                    filter(
                        lambda x: subfield in x.keys(),
                        filter_query[0][country_field]["subfields"],
                    )
                )
                if len(subfield_query) > 0:
                    address = acronyms_mapping[subfield_query[0][country_subfield]]

    return address


role_codes = utilities.csv2dict(
    os.path.join("data", "mappings", "bibtex", "role_codes.csv")
)

role_acronyms = {}

for role in role_codes:
    role_acronyms[role["code"]] = role["label"]


def get_authors(
    record_dict,
    main_field="100",
    main_subfield="a",
    alt_field="700",
    alt_subfield="a",
    role_subfield="4",
    acronyms_mapping=role_acronyms,
    roles=False,
):
    author_list = []

    if roles is not True:
        # get main author
        filter_query = list(
            filter(lambda x: main_field in x.keys(), record_dict["fields"])
        )

        if len(filter_query) > 0:
            for entry in filter_query:
                subfield_query = list(
                    filter(
                        lambda x: main_subfield in x.keys(),
                        entry[main_field]["subfields"],
                    )
                )
                if len(subfield_query) > 0:
                    author_list.append(subfield_query[0][main_subfield])

        # get additional authors
        filter_query = list(
            filter(lambda x: alt_field in x.keys(), record_dict["fields"])
        )

        if len(filter_query) > 0:
            for entry in filter_query:
                subfield_query = list(
                    filter(
                        lambda x: alt_subfield in x.keys(),
                        entry[alt_field]["subfields"],
                    )
                )
                if len(subfield_query) > 0:
                    author_list.append(subfield_query[0][alt_subfield])
    else:
        # get main author
        filter_query = list(
            filter(lambda x: main_field in x.keys(), record_dict["fields"])
        )

        if len(filter_query) > 0:
            for entry in filter_query:
                subfield_query = list(
                    filter(
                        lambda x: main_subfield in x.keys(),
                        entry[main_field]["subfields"],
                    )
                )
                if len(subfield_query) > 0:
                    author_list.append(
                        f"{subfield_query[0][main_subfield]} ({acronyms_mapping[subfield_query[0][role_subfield]]})"
                    )

        # get additional authors
        filter_query = list(
            filter(lambda x: alt_field in x.keys(), record_dict["fields"])
        )

        if len(filter_query) > 0:
            for entry in filter_query:
                subfield_query = list(
                    filter(
                        lambda x: alt_subfield in x.keys(),
                        entry[alt_field]["subfields"],
                    )
                )
                if len(subfield_query) > 0:
                    author_list.append(
                        f"{subfield_query[0][alt_subfield]} ({acronyms_mapping[subfield_query[0][role_subfield]]})"
                    )

    # parse authors in one string
    return " and ".join(author_list)


def get_howpublished(
    record_dict,
    license_field="506",
    licence_subfield="a",
    referee_field="591",
    referee_subfield="a",
    acronyms_mapping={
        "0": "Not peer-reviewed",
        "1": "Peer-reviewed",
        "Editorial review": "Peer-reviewed",
    },
):
    howpublished = ""

    # License information
    filter_query = list(
        filter(lambda x: license_field in x.keys(), record_dict["fields"])
    )

    if len(filter_query) > 0:
        subfield_query = list(
            filter(
                lambda x: licence_subfield in x.keys(),
                filter_query[0][license_field]["subfields"],
            )
        )
        if len(subfield_query) > 0:
            howpublished = subfield_query[0][licence_subfield]

    # Referee information

    filter_query = list(
        filter(lambda x: referee_field in x.keys(), record_dict["fields"])
    )

    if len(filter_query) > 0:
        subfield_query = list(
            filter(
                lambda x: referee_subfield in x.keys(),
                filter_query[0][referee_field]["subfields"],
            )
        )
        if len(subfield_query) > 0:
            howpublished += f", {acronyms_mapping[subfield_query[0][referee_subfield]]}"

    return howpublished


def get_booktitle(record_dict, field="773", subfield="t"):
    booktitle = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            booktitle = subfield_query[0][subfield]

    return booktitle


def get_doi(
    record_dict,
    field="856",
    subfield="u",
    control_field="856",
    control_subfield="3",
    control_value="DOI",
):
    doi = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))
    if len(filter_query) > 0:
        for entry in filter_query:
            control_subfield_query = list(
                filter(
                    lambda x: control_subfield in x.keys(),
                    entry[control_field]["subfields"],
                )
            )
            if len(control_subfield_query) > 0:
                if control_subfield_query[0][control_subfield] == control_value:
                    subfield_query = list(
                        filter(
                            lambda x: subfield in x.keys(), entry[field]["subfields"]
                        )
                    )
                    if len(subfield_query) > 0:
                        doi = latex_normalize(subfield_query[0][subfield]).replace(
                            "https://doi.org/", ""
                        )

    return doi


def get_institution(record_dict, field="610", subfield="a"):
    institution = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            institution = subfield_query[0][subfield]

    return institution


def get_issn(record_dict, field="773", subfield="x"):
    issn = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            issn = subfield_query[0][subfield].replace("-", "")

    return issn


def get_isbn(record_dict, fields=[["020", "a"], ["773", "z"]]):
    isbn = ""

    for field in fields:
        filter_query = list(
            filter(lambda x: field[0] in x.keys(), record_dict["fields"])
        )

        if len(filter_query) > 0:
            subfield_query = list(
                filter(
                    lambda x: field[1] in x.keys(),
                    filter_query[0][field[0]]["subfields"],
                )
            )
            if len(subfield_query) > 0:
                # found isbn
                isbn = subfield_query[0][field[1]]
                return isbn


def get_journal(record_dict, field="773", subfield="t"):
    journal = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            journal = subfield_query[0][subfield]

    return journal


def get_keywords(record_dict, field="650", subfield="a"):
    keywords_list = []

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        for entry in filter_query:
            subfield_query = list(
                filter(lambda x: subfield in x.keys(), entry[field]["subfields"])
            )
            if len(subfield_query) > 0:
                keywords_list.append(subfield_query[0][subfield])

    # parse keywords in one string
    return ", ".join(keywords_list)


def get_note(record_dict, field="500", subfield="a"):
    note = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            note = subfield_query[0][subfield]

    return note


def get_issue_number(record_dict, field="773", subfield="g"):
    issue_number = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            # check if there are multiple informations, such as volume and issue.
            comma_sep = subfield_query[0][subfield].split(",")
            if len(comma_sep) == 1:  # only pages case
                pass

            else:  # volume,issue,pages case
                issue_number = comma_sep[1].replace(" ", "")

    return issue_number


def get_pages(record_dict, fields=[["300", "a"], ["773", "g"]]):
    pages = ""

    for field in fields:
        filter_query = list(
            filter(lambda x: field[0] in x.keys(), record_dict["fields"])
        )

        if len(filter_query) > 0:
            subfield_query = list(
                filter(
                    lambda x: field[1] in x.keys(),
                    filter_query[0][field[0]]["subfields"],
                )
            )
            if len(subfield_query) > 0:
                # found pages
                pages = (
                    subfield_query[0][field[1]].replace("pages", "").replace("-", "--")
                )
                return pages


def get_publisher(record_dict, field="260", subfield="b"):
    publisher = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            publisher = subfield_query[0][subfield]

    return publisher


def get_school(record_dict, field="260", subfield="b"):
    school = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            school = subfield_query[0][subfield]

    return school


def get_title(record_dict, field="245", subfield="a"):
    title = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            title = subfield_query[0][subfield]

    return title


def get_url(record_dict, field="856", subfield="u"):
    url = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))
    if len(filter_query) > 0:
        # only considering first url value:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            url = subfield_query[0][subfield]

    return url


def get_volume(record_dict, field="773", subfield="g"):
    volume = ""

    filter_query = list(filter(lambda x: field in x.keys(), record_dict["fields"]))

    if len(filter_query) > 0:
        subfield_query = list(
            filter(lambda x: subfield in x.keys(), filter_query[0][field]["subfields"])
        )
        if len(subfield_query) > 0:
            # check if there are multiple informations, such as volume and issue.
            comma_sep = subfield_query[0][subfield].split(",")
            if len(comma_sep) == 1:  # only pages case
                pass

            else:  # volume,issue,pages case
                volume = comma_sep[0]

    return volume


def get_year(record_dict, fields=[["502", "a"], ["366", "b"], ["260", "c"]]):
    year = ""

    for field in fields:
        filter_query = list(
            filter(lambda x: field[0] in x.keys(), record_dict["fields"])
        )

        if len(filter_query) > 0:
            subfield_query = list(
                filter(
                    lambda x: field[1] in x.keys(),
                    filter_query[0][field[0]]["subfields"],
                )
            )
            if len(subfield_query) > 0:
                # found date of publication in the format yyyy-mm-dd
                year = subfield_query[0][field[1]].split("-")[0]
                return year
