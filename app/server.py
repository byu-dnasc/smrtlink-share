from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from time import sleep
import app.smrtlink as smrtlink
import app.staging as staging
import app.globus as globus
from app import logger, OutOfSyncError
import re

class InvalidRequestError(Exception):
    pass

def _get_project_id(uri):
    '''Try to get project ID from URI, return None if not found'''
    match = re.match(r'/smrt-link/projects/(\d+)', uri)
    if match:
        return int(match.group(1))
    else:
        return None
    
class RequestHandler(BaseHTTPRequestHandler):
    '''
    Respond to and log requests, then handle them asynchronously
    '''
    def _log_request(self):
        if self.response_code == 200:
            if self.command == 'POST':
                logger.info(f'Received notification that a new project was created in SMRT Link')
            elif self.command == 'PUT':
                logger.info(f'Received notification that project {_get_project_id(self.path)} was modified in SMRT Link')
            elif self.command == 'DELETE':
                logger.info(f'Received notification that project {_get_project_id(self.path)} was deleted in SMRT Link')
            else:
                logger.info(f'Received request: {self.command} {self.path}')
        else:
            logger.info(f'Received invalid request: {self.command} {self.path}')
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self._log_request(200)
        self.wfile.write(b'smrtlink-share app is online')

    def _get_response_code(self):
        '''Return the appropriate response code for the request'''
        assert self.command in ['POST', 'PUT', 'DELETE']
        if self.command in ['PUT', 'DELETE']:
            self.project_id = _get_project_id(self.path)
            return 200 if self.project_id \
                        else 404
        else: # POST
            return 200 if self.path == '/smrt-link/projects' \
                        else 404
            
    def _respond_log_wait(self):
        self.send_response(self.response_code) # RESPOND to client/proxy
        self.end_headers()
        self._log_request() # LOG the request
        if self.response_code == 404:
            raise InvalidRequestError
        sleep(1) # WAIT for SMRT Link to process the request
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = _get_project_id(self.path)
        self.response_code = self._get_response_code()
    
    def do_PUT(self):
        try:
            self._respond_log_wait()
        except InvalidRequestError:
            return
        try:
            project = smrtlink.get_project(self.project_id)
        except Exception as e:
            logger.error(f'Error getting project {self.project_id} from SMRT Link: {e}')
            return
        try:
            staging.update(project)
        except Exception as e:
            pass

    def do_POST(self):
        try:
            self._respond_log_wait()
        except InvalidRequestError:
            return
        try:
            project = smrtlink.get_new_project()
        except OutOfSyncError:
            project = smrtlink.sync_projects()
            # log
        try:
            staging.new(project)
        except Exception as e:
            pass

    def do_DELETE(self):
        try:
            self._respond_log_wait()
        except InvalidRequestError:
            return

class App(ThreadingHTTPServer):

    def __init__(self, server_address):
        super().__init__(server_address, RequestHandler)
        projects = smrtlink.load_db()
        staging.sync(projects)

    def run(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()