from flask import Blueprint
item = Blueprint('item', __name__, template_folder='templates')
from app.items import views
