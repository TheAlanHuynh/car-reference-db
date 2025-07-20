# lets “backend” be imported as a package
from .app import create_app   # so FLASK_APP=backend:create_app works