from .directive import AutoConfigDirective


def setup(app):
    app.add_directive('autoconfig', AutoConfigDirective)
