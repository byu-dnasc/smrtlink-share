from app import App, RequestHandler

app = App(('localhost', 9093), RequestHandler)

app.run()