from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from time import sleep
import app.smrtlink as smrtlink
import app.staging as staging
import app.globus as globus
from app import logger, OutOfSyncError
import re

PROJECT_PATH = '/smrt-link/projects'

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
    def _log_request(self, code):
        if code == 200:
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
    
    def _get_response_code(self):
        '''Return the appropriate response code for the request'''
        assert self.command in ['POST', 'PUT', 'DELETE']
        if self.command in ['PUT', 'DELETE']:
            return 200 if _get_project_id(self.path) \
                        else 404
        else: # POST
            return 200 if self.path == '/smrt-link/projects' \
                        else 404
            
    def _respond_log_wait(self):
        code = self._get_response_code()
        self.send_response(code) # RESPOND to client/proxy
        self.end_headers()
        self._log_request(code) # LOG the request
        if code == 404:
            raise InvalidRequestError
        sleep(1) # WAIT for SMRT Link to process the request
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self._log_request(200)
        self.wfile.write(b'smrtlink-share app is online')

    def do_PUT(self):
        '''
        Anything may need to be modified, including
        files, directory names, and access rules
        '''
        try:
            self._respond_log_wait()
        except InvalidRequestError:
            return
        project_id = _get_project_id(self.path)
        if project_id:
            pass

    def do_POST(self):
        try:
            self._respond_log_wait()
        except InvalidRequestError:
            return
        try:
            project = smrtlink.get_new_project()
            staging.new(project)
        except OutOfSyncError:
            pass

    def do_DELETE(self):
        try:
            self._respond_log_wait()
        except InvalidRequestError:
            return
        project_id = _get_project_id(self.path)
        if project_id:
            pass
        for rule_id in globus.get_project_access_rule_ids(project_id):
            globus.delete_acl_rule(rule_id)

class App(ThreadingHTTPServer):

    def __init__(self, server_address):
        super().__init__(server_address, RequestHandler)

    def run(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()