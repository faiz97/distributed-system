# 1. Cara pemakaian: python server.py [port], gunakan python3
# 2. Pelajaran:
# - Memahami struktur dari HTTP/1.0 dan HTTP/1.1
# - Memahami cara kerja server
# - Membuat server ternyata tidak semudah yang dibayangkan

import socket
import sys
import random
import datetime
import json
import requests
from urllib.parse import unquote

def process(data, conn):
    if len(data) == 0:
        http_bad_request('Empty Request', conn)

    request_string = data.decode('utf-8')
    arr_of_str = request_string.split('\n')
    req_line = arr_of_str[0].split()
    
    if len(req_line) != 3:
        http_bad_request('Invalid HTTP request', conn)
        return      

    method = req_line[0].upper()
    if method != 'GET' and method != 'POST':
        http_not_implemented(method, conn)
        return

    version = req_line[2].upper()
    if version != 'HTTP/1.0' and version != 'HTTP/1.1':
        http_bad_request('Only support HTTP/1.0 and HTTP/1.1', conn)
        return

    create_response(data, conn)


def create_response(data, conn):
    request_string = data.decode('utf-8')
    header_body_splitter = request_string.split('\r\n\r\n')
    req_fields = header_body_splitter[0].split('\r\n')
    req_body = header_body_splitter[len(header_body_splitter)-1]
    req_line = req_fields[0].split()
    req_fields.pop(0)

    content_type = 'text/html; charset=UTF-8'
    content_length = 0

    for line in req_fields:

        if 'Content-Type' in line:
            temp = line.split(':')
            content_type = temp[1].strip()

    method = req_line[0].upper()
    temp = req_line[1].split('?')
    if len(temp) > 1:
        path = temp[0]
        path_query = temp[1]
    else:
        path = temp[0]

    if path == '/':
        http_redirect('/hello-world', conn)

    elif path == '/hello-world':
        hello_world(method, req_body, content_type, conn)

    elif method == 'GET' and path != '/':
        if path == '/style':
            css = open('style.css', 'rb').read().decode()
            content_type = 'text/css; charset=UTF-8'
            http_ok(content_type, css, conn)
        elif path == '/background':
            background = open('background.jpg', 'rb').read()
            content_type = 'image/jpeg; charset=UTF-8'
            http_ok_image(content_type, background, conn)
        elif path == '/info':
            if path_query != 0:
                dictionary = {}
                parse_query(path_query, dictionary)
                type = dictionary['type']
                if type.lower() == 'random':
                    num = str(random.randint(0, 1000000))
                    content_type = 'text/plain; charset=UTF-8'
                    http_ok(content_type, num, conn)
                    return
                if type.lower() == 'time':
                    time = str(datetime.datetime.now())
                    content_type = 'text/plain; charset=UTF-8'
                    http_ok(content_type, time, conn)
                    return
                
                content_type = 'text/plain; charset=UTF-8'
                http_ok(content_type, 'No Data', conn)
        elif len(path.split('/')) == 4:
            path = path.split('/')
            path.pop(0)
            if path[0] == 'api' and path[1] == 'plusone':
                try:
                    num = int(path[2])
                    plus_one(num, conn)
                except Exception as e:
                    detail = 'The requested URL was not found on the server. \
                    If you entered the URL manually please check your spelling and try again.'
                    status = 404
                    title = 'Not Found'
                    content = json.dumps({'detail': detail, 'status': status, 'title': title})
                    content_type = 'application/json'
                    http_not_found(conn, content_type, content)
            else:
                detail = 'The requested URL was not found on the server. \
                If you entered the URL manually please check your spelling and try again.'
                status = 404
                title = 'Not Found'
                content = json.dumps({'detail': detail, 'status': status, 'title': title})
                content_type = 'application/json'
                http_not_found(conn, content_type, content)

        elif len(path.split('/')) == 3:
            path = path.split('/')
            path.pop(0)
            if path[0] == 'api' and path[1] == 'spesifikasi.yaml':
                yaml = open('spesifikasi.yaml', 'rb').read().decode()
                content_type = 'text/yaml; charset=UTF-8'
                http_ok(content_type, yaml, conn)

    elif method == 'POST':
        path = path.split('/')
        path.pop(0)
        if path[0] == 'api':
            if len(path) == 2 and path[1] == 'hello':
                hello(req_body, content_type, conn)

    else:
        http_not_found(conn)

            
def parse_query(queries, dictionary):
    queries = queries.split('&')
    for query in queries:
        temp = query.split('=')
        if len(temp) > 1:
            dictionary[unquote(temp[0])] = unquote(temp[1]).replace('+', ' ')
        else:
            dictionary[unquote(temp[0])] = ''


def hello_world(method, req_body, content_type, conn):
    html = open('hello-world.html', 'rb').read().decode()
    name = 'World'

    if method.upper() == 'POST':
        if content_type.lower() != 'application/x-www-form-urlencoded':
            http_bad_request('Content-Type must application/x-www-form-urlencoded not ' + content_type, conn)
        queries = req_body
        dictionary = {}
        parse_query(queries, dictionary)
        name = dictionary['name']

    html = html.replace('__HELLO__', name)
    content_type = 'text/html; charset=UTF-8'
    http_ok(content_type, html, conn)


def hello(req_body, content_type, conn):
    detail = "'request' is a required property"
    status = 404
    title = 'Bad Request'
    content = json.dumps({'detail': detail, 'status': status, 'title': title})

    if content_type.lower() == 'application/json':
        try:
            parse_body = json.loads(req_body)
            request = parse_body['request']

            apiversion = '1.0'
            count = _hello_count(_hello_count_read())
            currentvisit = str(datetime.datetime.now())
            response = _hello_response(request)

            content = json.dumps({'apiversion': apiversion, 'count': count, 'currentvisit': currentvisit, 'response': response})
            http_ok(content_type, content, conn)
        except Exception as e:
            http_not_found(conn, content_type, content)
    else:
        http_not_found(conn, content_type, content)


def _hello_response(request):
    resp = requests.get('http://172.22.0.222:5000').json()
    response = 'Good ' + resp['state'] + ', ' + request

    return response


def _hello_count(num):
    with open('state.txt', 'w') as state:
        state.write(str(num))
        
        return int(num)


def _hello_count_read():
    with open('state.txt') as state:
        num = state.read()
        num = int(num) + 1
    
        return num


def plus_one(num, conn):
    num = num + 1
    content = json.dumps({'apiversion': '1.0', 'plusoneret': num})
    content_type = 'application/json'

    http_ok(content_type, content, conn)


def http_not_found(conn, content_type='text/plain', content='404 Not Found'):
    content_length = str(len(content))
    response = bytes('HTTP/1.1 404 Not Found\r\nConnection: close\r\nContent-Type:'\
    + content_type +'; charset=UTF-8\r\nContent-Length:'+ content_length +'\r\n\r\n', 'utf-8')
    if content != None:
        res = bytes(content, 'utf-8')
    conn.send(response)
    conn.send(res)

    
def http_redirect(location, conn):
    response = bytes('HTTP/1.1 302 Found\r\nConnection: close\r\nLocation: ' + location + \
    '\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Length: ' + str(21 + len(location)) + '\r\n\r\n302 Found: Location: ' + location, 'utf-8')
    conn.send(response)


def http_bad_request(message ,conn):
    response = bytes('HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Length: ' \
    + str(25 + len(message)) + '\r\n\r\n400 Bad Request: Reason: ' + message, 'utf-8')
    conn.send(response)


def http_not_implemented(method, conn):
    response = bytes('HTTP/1.1 501 Not Implemented\r\nConnection: close\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Length: ' \
    + str(29 + len(method)) + '\r\n\r\n501 Not Implemented: Reason: ' + method, 'utf-8')
    conn.send(response)


def http_ok(content_type, content, conn):
    response = bytes('HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Type: ' + content_type + '\r\nContent-Length: ' + str(len(content)) + "\r\n\r\n" + content, 'utf-8')
    res = bytes(content, 'utf-8')
    conn.send(response)
    conn.send(res)


def http_ok_image(content_type, content, conn):
    response = bytes('HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Type: ' + content_type + '\r\nContent-Length: ' + str(len(content)) + "\r\n\r\n", 'utf-8')
    res = bytes(content)
    conn.send(response)
    conn.send(res)


port = ''

try:
    port = sys.argv[1:][0]
except IndexError:
    print('Please specify which port to listen')
    sys.exit()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    port = int(port)
    host = '0.0.0.0'
    s.bind((host, port))
    s.listen()
    print('Listening at port:', port)
    while True:
        conn, addr = s.accept()
        with conn:
            data = conn.recv(1024)
            process(data, conn)
            if not data:
                break