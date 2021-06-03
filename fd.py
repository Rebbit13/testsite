import requests
import os
from models import Session


resp = requests.post("http://127.0.0.1:8000/web/api/item/product",
                     headers={"X-session-id": "5", "X-session-token": "EhBFO7H0jKMrbum9PvnXlDw2qk5UGso3"},
                     data="""{"product": {"name": "Роза Алая", "type": "Роза", "price": 120, "discount_check": true, "pic": "розаалая.jpg"}}""".encode('utf-8'))
print(resp, resp.json())
