import requests

try:
    response = requests.get("http://localhost:11434/api/tags")
    models = response.json()['models']
    for m in models:
        print(m['name'])
except Exception as e:
    print(e)
