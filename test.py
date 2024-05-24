import requests

headers = {
    'Accept': 'application/json'
}

a = requests.get('https://check-host.net/check-http?host=finland.ggkala.shop:2053', headers=headers)
a = requests.get('https://check-host.net/check_result/19d6ce2ek123', headers=headers)

print(a.json())
