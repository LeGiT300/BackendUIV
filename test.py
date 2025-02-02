from requests import get, put

put('http://localhost:5000/todo1', data={'data': 'Remember the milk'}).json
put('http://localhost:5000/todo2', data={'data': 'change the breaks'}).json
data = get('http://localhost:5000/todo1').json
print(data)