"""
Basic utilities scripts
"""
import json, csv
import pandas as pd
from time import gmtime, strftime, time
import math
import os
import requests


def csv2dict(csv_filename, encoding="utf-8-sig", orient="records", na_values=""):
    df = pd.read_csv(csv_filename, encoding=encoding)
    df = df.fillna(na_values)
    d = df.to_dict(orient=orient)
    return d


def dict2csv(d, csv_filename, separator: str = ",", index: bool = False):
    df = pd.DataFrame(data=d)
    df.to_csv(csv_filename, sep=separator, index=index)


def json2dict(json_filename):  # imports a JSON file as dictionary
    with open(json_filename, "r") as f:
        json_file = json.load(f)
        return json_file


def dict2json(
    d, json_filename, ensure_ascii=False, indent=2
):  # export a dictionary to JSON file
    with open(json_filename, "w") as json_file:
        json.dump(d, json_file, indent=indent, ensure_ascii=ensure_ascii)


def get_current_date():
    return strftime("%Y-%m-%d", gmtime())


def get_latest_file(basepath):  # returns latest file path in a directory
    files = os.listdir(basepath)
    paths = [os.path.join(basepath, basename) for basename in files]
    return max(paths, key=os.path.getctime)
