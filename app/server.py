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

def stage_new_project(project):
    try:
        staging.new(project)
    except Exception as e:
        ... # handle staging exception
        ... # log the error

def new_project():
    try:
        project = smrtlink.get_new_project()
        if project is None:
            raise Exception('SMRT Link has no projects (other than the "General Project").')
    except Exception as e:
        logger.error(f'Cannot handle new project request: {e}.')
        return
    stage_new_project(project)    

def update_project(project_id):
    try:
        project = smrtlink.get_project(project_id)
    except OutOfSyncError as e:
        logger.info(f'App is Out-of-Sync with SMRT Link: {e.message}')
        stage_new_project(e.project)
    except Exception as e:
        logger.error(f'Cannot handle project update request: {e}.')
        return
    try:
        staging.update(project)
    except Exception as e:
        ... # handle staging exception
        ... # log the error
    
class RequestHandler(BaseHTTPRequestHandler):
    '''
    Respond to and log requests, then handle them asynchronously
    '''
    def _log_request(self, response_code):
        if response_code == 200:
            if self.command == 'POST':
                logger.info(f'Received notification that a new project was created in SMRT Link')
            elif self.command == 'PUT':
                logger.info(f'Received notification that project {_get_project_id(self.path)} was modified in SMRT Link')
            elif self.command == 'DELETE':
                logger.info(f'Received notification that project {_get_project_id(self.path)} was deleted in SMRT Link')
            else:
                logger.info(f'Received request: {self.command} {self.path}')
        elif response_code == 405:
            logger.info(f'Received request to stage project 1, which is not supported.')
        else:
            logger.info(f'Received invalid request: {self.command} {self.path}')
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self._log_request(200)
        self.wfile.write(b'smrtlink-share app is online')

    def _get_response_code(self):
        '''Return the appropriate response code for the request'''
        assert self.command in ('POST', 'PUT', 'DELETE')
        if self.command in ('PUT', 'DELETE'):
            if self.project_id:
                if self.project_id == 1:
                    return 405 # project 1 should not be shared
                return 200
            return 404
        else: # POST
            return 200 if self.path == '/smrt-link/projects' \
                        else 404
            
    def handle_response(self):
        response_code = self._get_response_code()
        self.send_response(response_code) # RESPOND to client/proxy
        self.end_headers()
        self._log_request(response_code) # LOG the request
        if response_code != 200:
            return False
        return True
    
    def parse_request(self) -> bool:
        '''
        Method called by superclass init to validate request and set
        some attributes. I'm overriding this instead of init because 
        the superclass init also calls the do_* methods, which need 
        the project_id attribute to be set.
        '''
        request_is_valid = super().parse_request()
        self.project_id = _get_project_id(self.path)
        return request_is_valid
    
    def do_PUT(self):
        if not self.handle_response():
            return
        sleep(1)
        update_project(self.project_id)        
    
    def do_POST(self):
        if not self.handle_response():
            return
        sleep(1)
        new_project()
        
    def do_DELETE(self):
        if not self.handle_response():
            return
        sleep(1)

class App(ThreadingHTTPServer):

    def __init__(self, server_address):
        super().__init__(server_address, RequestHandler)

    def run(self):
        self.serve_forever()

    def stop(self):
        self.shutdown()