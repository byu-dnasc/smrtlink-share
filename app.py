import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(filename='request.log', level=logging.INFO)

class App(HTTPServer):

    def run(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()

class RequestHandler(BaseHTTPRequestHandler):

    def _log_request(self):
        content_length = 0
        if 'Content-Length' in self.headers:
            content_length = int(self.headers['Content-Length'])
        logging.info(f'{self.command} {self.path} {content_length}')
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'smrtlink-share app is online')
        self._log_request()
        print('GET request received')

    def do_POST(self):
        self._log_request()

    def do_PUT(self):
        self._log_request()
        
    def do_DELETE(self):
        self._log_request()