from flask import Flask
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, static_folder="static")
import views
app.config.from_object('config')
csrf = CSRFProtect(app)
