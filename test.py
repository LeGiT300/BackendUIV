from requests import get

base = 'http://localhost:5000/'

response = get(base + 'helloworld')
print(response)