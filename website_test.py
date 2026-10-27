import json


def load_websites():
    try:
        with open("websites.json",encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError,json.JSONDecodeError):
        return {}
    
    return {k.lower(): v for k,v in data.items()}



print(load_websites())