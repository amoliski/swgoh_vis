import sys

index = """
<a href="/swgoh/cotd">CoTD Charts</a>
"""


def serve_static_file(filename, start_response):
    status = '200 OK'
    h = open('/home/amoliski/swgoh/static/{}'.format(filename), 'r')
    content = h.read()
    h.close()
    c_type = 'application/json' if filename.endswith('.json') else 'text/html'
    response_headers = [('Content-Type', c_type), ('Content-Length', str(len(content))), ('Access-Control-Allow-Origin',' *')]
    start_response(status, response_headers)
    return content.encode('utf8')


def application(environ, start_response):
    if environ.get('PATH_INFO') == '/':
        status = '200 OK'
        content = index
        response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content))), ('Access-Control-Allow-Origin',' *')]
        start_response(status, response_headers)
        yield content.encode('utf8')

    elif environ.get('PATH_INFO') == '/swgoh/cotd':
        yield serve_static_file('index.htm', start_response)

    elif environ.get('PATH_INFO') == '/swgoh/cotd/unit_list.json':
        yield serve_static_file('unit_list.json', start_response)

    elif environ.get('PATH_INFO') == '/swgoh/cotd/rosters.json':
        yield serve_static_file('rosters.json', start_response)

    elif environ.get('PATH_INFO') == '/swgoh/cotd/user_list.json':
        yield serve_static_file('user_list.json', start_response)

    elif environ.get('PATH_INFO') == '/swgoh/cache.json':
        yield serve_static_file('cache.json', start_response)


    else:
        status = '404 NOT FOUND'
        content = 'Page not found.'
        response_headers = [('Content-Type', 'text/html'), ('Content-Length', str(len(content))), ('Access-Control-Allow-Origin',' *')]
        start_response(status, response_headers)
        yield content.encode('utf8')


