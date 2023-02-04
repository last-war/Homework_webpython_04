import json
import logging
import urllib.parse
import pathlib
import mimetypes
import socket
from threading import Thread, RLock
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_DIR = pathlib.Path()
UDP_IP = '127.0.0.1'
UDP_PORT = 5000


class StudyHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """detect files which need send to browser"""

        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html_file('front-init/index.html')
            case '/message.html':
                self.send_html_file('front-init/message.html')
            case _:
                file = BASE_DIR.joinpath('front-init', route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file('front-init/error.html', 404)

    def send_html_file(self, filename, status=200):
        """send to browser html files"""
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def do_POST(self):
        """send data to socket"""
        data = self.rfile.read(int(self.headers['Content-Length']))

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serv = UDP_IP, UDP_PORT
        sock.sendto(data, serv)
        sock.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_static(self, file):
        """send to browser static files"""
        self.send_response(200)
        mt = mimetypes.guess_type(file)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'{file}', 'rb') as file:
            self.wfile.write(file.read())

def run_http_server(server=HTTPServer, handler=StudyHTTPRequestHandler):
    """start HTTP server"""
    logging.info("start HTTP server")

    address = ('', 3000)
    study_http_server = server(address, handler)
    try:
        study_http_server.serve_forever()
    except KeyboardInterrupt:
        logging.debug("close HTTP server")
        study_http_server.server_close()


def run_server():
    """start echo server"""
    logging.info("start echo server")

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_sock.bind((UDP_IP, UDP_PORT))
    try:
        while True:
            data, address = server_sock.recvfrom(1024)
            logging.debug(f"send {data} to server")
            save_packet(data)
    except KeyboardInterrupt:
        logging.debug("close echo server")
        server_sock.close()
    finally:
        logging.debug("close echo server")
        server_sock.close()

def save_packet(data):
    """save data to json"""
    data_parse = urllib.parse.unquote_plus(data.decode())
    try:
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        log_json = {str(datetime.datetime.now()): data_dict}
        with open('front-init/storage/data.json', 'a', encoding='utf-8') as data_file:
            logging.debug(f"file 'front-init/storage/data.json' ")

            json.dump(log_json, data_file, ensure_ascii=False)
    except ValueError as error:
        logging.error(f'Some error:{error}')
    except OSError:
        logging.error('problem with file')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    server_http = Thread(target=run_http_server)
    server_echo = Thread(target=run_server)

    server_http.start()
    server_echo.start()
