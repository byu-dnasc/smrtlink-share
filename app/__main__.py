import logging

from app.server import App

logging.basicConfig(filename='request.log', level=logging.INFO)

app = App(('localhost', 9093), logging.getLogger(__name__))

app.run()