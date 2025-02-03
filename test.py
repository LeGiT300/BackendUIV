from requests import get

base = 'http://localhost:5000/'

response = get(base + 'helloworld/leku/34')
print(response.json())