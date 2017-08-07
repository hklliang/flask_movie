
from flask import Flask,render_template
from flask_sqlalchemy import SQLAlchemy
import os
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:123456@127.0.0.1:3306/movie"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY']='98feca3a146d4aa0bbf58213d873c2b9'
app.config['UP_DIR']=os.path.join(os.path.abspath(os.path.dirname(__file__)),'static/uploads/')
app.config['FC_DIR']=os.path.join(os.path.abspath(os.path.dirname(__file__)),'static/uploads/users/')
app.debug=True
db = SQLAlchemy(app)


from app.home import home as home_blueprint
from app.admin import admin as admin_blueprint


app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint,url_prefix="/admin")

@app.errorhandler(404)
def page_not_found(error):
    return render_template('home/404.html'),404