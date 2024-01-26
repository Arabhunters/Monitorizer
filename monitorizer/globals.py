import requests
import yaml

local_metadata = {
    "version": {
        "monitorizer": 3.0,
        "toolkit": 2.0
    }
}

try:
    metadata_github = yaml.safe_load(
        requests.get("https://raw.githubusercontent.com/Arabhunters/Monitorizer/master/version.yaml").text)
except:
    metadata_github = local_metadata