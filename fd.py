import requests


resp = requests.post("http://127.0.0.1:8000/web/api/registration",
                     data="""{"session": {"id": 4, "ken": "YGkHxhEVOSZo39Lawf5TtUe0nlcXd2vB"}, "customer": {"telephone": 87996217368, "password": "static", "name": "Alex"}}""")
print(resp, resp.json())
