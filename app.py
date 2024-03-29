from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from time import sleep
import project

def _get_project_id(uri):
    project_id = uri.split('/')[-1]
    try:
        return int(project_id)
    except ValueError:
        return None

def _handler_with_logger(logger):
    '''
    Factory function to create a RequestHandler class ("Dispatcher") with a logger
    '''
    class Dispatcher(BaseHTTPRequestHandler):
        '''
        Respond to and log requests, then dispatch a handler
        '''
        log = logger

        def _log_request(self):
            content_length = 0
            if 'Content-Length' in self.headers:
                content_length = int(self.headers['Content-Length'])
            self.log.info(f'{self.command} {self.path} {content_length}')
        
        def _minimum_viable_response(self):
            '''
            Send the minimum viable response to NGINX (proxy)
            Anything less may work, but an error will be logged
            '''
            self.send_response(200)
            self.end_headers()
        
        def _respond_log_wait(self):
            self._minimum_viable_response() # RESPOND to NGINX
            self._log_request() # LOG the request
            sleep(1) # WAIT for SMRT Link to process the request
        
        def do_GET(self):
            self._minimum_viable_response()
            self._log_request()
            self.wfile.write(b'smrtlink-share app is online')

        def do_PUT(self):
            self._respond_log_wait()
            project_id = _get_project_id(self.path)
            if project_id:
                pass

        def do_POST(self):
            self._respond_log_wait()
            try:
                new_project = project.get_new()
                # TODO: stage project
                new_project.save(force_insert=True)
            except project.OutOfSyncError:
                pass

        def do_DELETE(self):
            self._respond_log_wait()
            project_id = _get_project_id(self.path)
            if project_id:
                pass

    return Dispatcher

class App(ThreadingHTTPServer):

    def __init__(self, server_address, logger):
        super().__init__(server_address, _handler_with_logger(logger))

    def run(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()
