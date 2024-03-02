from http.server import HTTPServer, BaseHTTPRequestHandler

def _handler_with_logger(logger):
    class RequestHandler(BaseHTTPRequestHandler):
        log = logger

        def _log_request(self):
            content_length = 0
            if 'Content-Length' in self.headers:
                content_length = int(self.headers['Content-Length'])
            self.log.info(f'{self.command} {self.path} {content_length}')
        
        def do_GET(self):
            self._log_request()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'smrtlink-share app is online')

        def do_POST(self):
            self.send_response_only(200)
            self._log_request()

        def do_PUT(self):
            self._log_request()
            
        def do_DELETE(self):
            self._log_request()

    return RequestHandler

class App(HTTPServer):

    def __init__(self, server_address, logger):
        super().__init__(server_address, _handler_with_logger(logger))

    def run(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()
