class BaseController:
    def __init__(self, app):
        self.app = app

    @property
    def root(self):
        return self.app.root

    @property
    def view(self):
        return self.app.view

    @property
    def session(self):
        return self.app.session

    @property
    def state(self):
        return self.app.state
