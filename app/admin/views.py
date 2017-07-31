from . import admin
#引用的是__init__.py里面的admin

@admin.route("/")
def index():
    return "<h1 style='color:red'>this is admin </h1>"