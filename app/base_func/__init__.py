from flask import Blueprint
base_func = Blueprint('base_func', __name__, template_folder='templates')
from . import views
