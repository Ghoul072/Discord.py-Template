import json


def validate_name(filename: str) -> str:
    if filename.endswith(".json"):
        return filename
    else:
        return filename + ".json"


# loads and returns a json file as a python dict
def read_file(filename: str) -> dict:
    filename = validate_name(filename)
    with open(f"data/{filename}", "r") as file:
        return json.load(file)
    
    
# completely overwrite all content in a json file
def overwrite_file(data: dict, filename: str) -> None:
    filename = validate_name(filename)
    with open(f"data/{filename}", "w") as file:
        json.dump(data, file, indent=4)


# fetch the value of a given key from a file, return None if key not found
def fetch_data(key: str, filename: str) -> str | None:
    return read_file(filename).get(key, None)
        

# writes a new key into a json file or replaces existing key
# get content of file as a dict, merge both dicts and then write into file
def append_data(data: dict, filename: str) -> None:
    file = read_file(filename)
    newdata = file | data
    overwrite_file(newdata, filename)
