from flask import Flask
app = Flask(__name__)


#app是Flask的实例，它接收包或者模块的名字作为参数，但一般都是传递__name__。
#    让flask.helpers.get_root_path函数通过传入这个名字确定程序的根目录，以便获得静态文件和模板文件的目录。
@app.route('/')
def hello_world():
    return 'Hello World!'