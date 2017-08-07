from . import admin
from flask import render_template, redirect, url_for, flash, session, request,abort
from app.admin.forms import LoginForm, TagForm, MovieForm, PreviewForm, PwdForm,Authform,Roleform,Adminform

from app.models import Admin, Tag, Movie, Preview, User, Comment, Moviecol, Oplog, Adminlog, Userlog,Auth,Role
from functools import wraps
from app import db, app
from werkzeug.utils import secure_filename
import os, uuid, datetime, stat

if not os.path.exists(app.config['UP_DIR']):
    os.makedirs(app.config['UP_DIR'])
    os.chmod(app.config['UP_DIR'], stat.S_IRWXU)


# 只要加上admin.context_processor，且返回的是字典，那么久可以全局引用
@admin.context_processor
def tpl_extra():
    data = dict(
        online_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    return data

#登录装饰器
def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin.login', next=request.url))  # 记录要进入的地址参数
        return f(*args, **kwargs)

    return decorated_function

#权限控制装饰器
def admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin=Admin.query.join(
            Role
        ).filter(
            Role.id==Admin.role_id,
            Admin.id==session['admin_id']
        ).first()
        auths=admin.role.auths
        auths=list(map(lambda v:int(v),auths.split(',')))
        auth_list=Auth.query.all()
        urls=[v.url for v in auth_list for val in auths if val==v.id]
        rule=str(request.url_rule)
        if admin.is_super!=1 and rule not in urls:
            abort(404)
        return f(*args, **kwargs)

    return decorated_function


# 引用的是__init__.py里面的admin
# flash信息闪现

def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex) + fileinfo[-1]

    return filename


@admin.route("/")
@admin_login_req
@admin_auth
def index():
    return render_template('admin/index.html')


@admin.route("/login/", methods=['GET', 'POST'])
def login():
    if 'admin' in session:
        return redirect(url_for('admin.index'))

    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data['account']).first()
        if not admin.check_pwd(data['pwd']):
            flash('密码错误！', 'err')
            # return redirect(url_for('admin.login'))
            return render_template('admin/login.html', form=form)
        # 将账号加入到session字典中
        session['admin'] = data['account']
        session['admin_id'] = admin.id
        adminlog=Adminlog(
            admin_id=admin.id,
            ip=request.remote_addr
        )
        db.session.add(adminlog)
        db.session.commit()
        return redirect(request.args.get('next') or url_for('admin.index'))  # 是否有要进入的参数
    return render_template('admin/login.html', form=form)


@admin.route("/logout/")
@admin_login_req
def logout():
    session.pop('admin')
    return redirect(url_for('admin.login'))


# 修改密码,要注意在html加上post，否则不会传递任何数据和进行校验
@admin.route("/pwd/", methods=['GET', 'POST'])
@admin_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session['admin']).first()
        from werkzeug.security import generate_password_hash
        admin.pwd = generate_password_hash(data['new_pwd'])
        db.session.commit()
        flash('修改密码成功', 'ok')
        # return redirect(url_for('admin.logout'))
    return render_template('admin/pwd.html', form=form)


@admin.route("/tag/add/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data['name']).count()

        if tag >= 1:
            flash('名称已经存在！', 'err')
            return render_template('admin/tag_add.html', form=form)
        tag = Tag(
            name=data['name']
        )
        db.session.add(tag)

        oplog = Oplog(
            admin_id=session['admin_id'],
            ip=request.remote_addr,
            reason='添加标签%s' % data['name']
        )
        db.session.add(oplog)
        db.session.commit()
        flash('添加标签成功！', 'ok')

        return redirect(url_for('admin.tag_add'))
    return render_template('admin/tag_add.html', form=form)  # 因为在html中引用了form


@admin.route("/tag/edit/<int:id>/<int:page>/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def tag_edit(id, page=None):
    form = TagForm()  # 点了提交才有数据传过来了，get请求是没有数据,所以需要借用到tag
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        # filter_by只能用=，而不能用!=，没有filter灵活
        tag_count = Tag.query.filter(Tag.name == data['name'], Tag.id != id).count()
        tag.name = data['name']
        if tag_count >= 1:
            flash('名称已经存在！', 'err')
            return render_template('admin/tag_edit.html', form=form, tag=tag)

        # 更新不用写额外的session操作

        flash('修改标签成功！', 'ok')

        db.session.commit()
        return redirect(url_for('admin.tag_list', page=page))

    return render_template('admin/tag_edit.html', form=form, tag=tag)


# 标签删除
@admin.route("/tag/del/<int:id>/<int:page>/", methods=['GET'])
@admin_login_req
@admin_auth
def tag_del(id=None, page=None):
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()

    flash('删除标签成功！', 'ok')

    return redirect(url_for('admin.tag_list', page=page or 1))


@admin.route("/tag/list/<int:page>/", methods=['GET'])
@admin_login_req
@admin_auth
def tag_list(page=None):
    if page is None:
        page = 1
    page_data = Tag.query.order_by(
        Tag.addtime.desc()
    ).paginate(page=page, per_page=10,error_out=False)
    if page == 1 or page_data.items:
        return render_template('admin/tag_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.tag_list', page=1))


@admin.route("/movie/add/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title=data['title']).count()
        if movie_count >= 1:
            flash('该电影已经存在！', 'err')
            return render_template('admin/movie_add.html', form=form)

        file_url = secure_filename(form.url.data.filename)
        file_logo = secure_filename(form.logo.data.filename)

        url = change_filename(file_url)
        logo = change_filename(file_logo)
        form.url.data.save(app.config['UP_DIR'] + url)
        form.logo.data.save(app.config['UP_DIR'] + logo)
        movie = Movie(
            title=data['title'],
            url=url,
            info=data['info'],
            logo=logo,
            star=int(data['star']),
            playnum=0,
            commentnum=0,
            tag_id=int(data['tag_id']),
            area=data['area'],
            release_time=data['release_time'],
            length=data['length']
        )
        db.session.add(movie)
        db.session.commit()

        flash('添加电影成功！', 'ok')
        return redirect(url_for('admin.movie_add'))
    return render_template('admin/movie_add.html', form=form)


@admin.route("/movie/list/<int:page>/", methods=['GET'])
@admin_login_req
@admin_auth
def movie_list(page=None):
    if page is None:
        page = 1
    page_data = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id
    ).order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=10)
    if page == 1 or page_data.items:
        return render_template('admin/movie_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.movie_list', page=1))


@admin.route("/movie/list/<int:id>/<int:page>", methods=['GET'])
@admin_login_req
@admin_auth
def movie_del(id=None, page=None):
    movie = Movie.query.get_or_404(int(id))
    db.session.delete(movie)
    db.session.commit()
    flash('删除电影成功！', 'ok')
    return redirect(url_for('admin.movie_list', page=page or 1))


@admin.route("/movie/edit/<int:id>/<int:page>/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def movie_edit(id, page=None):
    form = MovieForm()  # 没有点提交时，没有任何数据
    movie = Movie.query.get_or_404(int(id))  # 只能通过id在数据库里查

    if request.method == 'GET':  # input可以用form.title(value=movie.title)，但是类似于textarea或者select等标签是不可以的
        form.info.data = movie.info  # 但是如果是在src里的地址，只能通过movie.logo
        form.tag_id.data = movie.tag_id
        form.star.data = movie.star

    form.logo.validators = []  # 去掉封面和电影的校验，否则会提示上传数据
    form.url.validators = []  #

    if form.validate_on_submit():  # 校验通过时
        data = form.data
        movie_count = Movie.query.filter(Movie.title == data['title'], Movie.id != id).count()
        if movie_count > 1:
            flash('该电影已经存在！', 'err')
            return render_template('admin/movie_edit.html', form=form, movie=movie)
        url = form.url.data.filename
        logo = form.logo.data.filename

        # 要先判断是否有上传文件
        if url:
            file_url = secure_filename(url)
            movie.url = change_filename(file_url)
            form.url.data.save(app.config['UP_DIR'] + movie.url)

        if logo:
            file_logo = secure_filename(logo)
            movie.logo = change_filename(file_logo)
            form.logo.data.save(app.config['UP_DIR'] + movie.logo)

        movie.star = data['star']
        movie.tag_id = data['tag_id']
        movie.info = data['info']
        movie.title = data['title']
        movie.area = data['area']
        movie.length = data['length']
        movie.release_time = data['release_time']

        # db.session.add(movie)#加不加都可以
        db.session.commit()

        flash('修改电影成功！', 'ok')
        return redirect(url_for('admin.movie_list', page=page or 1))
    return render_template('admin/movie_edit.html', form=form, movie=movie)


@admin.route("/preview/add/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        preview_count = Preview.query.filter_by(title=data['title']).count()
        if preview_count >= 1:
            flash('预告已经存在！', 'err')
            return render_template('admin/preview_add.html', form=form)

        file_logo = secure_filename(form.logo.data.filename)
        logo = change_filename(file_logo)
        form.logo.data.save(app.config['UP_DIR'] + logo)

        preview = Preview(
            title=data['title'],
            logo=logo
        )
        db.session.add(preview)
        db.session.commit()
        flash('添加预告成功！', 'ok')
        return redirect(url_for('admin.preview_add'))

    return render_template('admin/preview_add.html', form=form)


@admin.route("/preview/list/<int:id>/<int:page>", methods=['GET'])
@admin_login_req
@admin_auth
def preview_del(id=None, page=None):
    preview = Preview.query.get_or_404(int(id))
    db.session.delete(preview)
    db.session.commit()
    flash('删除预告成功！', 'ok')
    return redirect(url_for('admin.preview_list', page=page or 1))


@admin.route("/preview/list/<int:page>", methods=['GET'])
@admin_login_req
@admin_auth
def preview_list(page=None):
    if page is None:
        page = 1
    page_data = Preview.query.order_by(
        Preview.addtime.desc()
    ).paginate(page=page, per_page=2, error_out=False)
    # 没有数据的时候返回第一页
    if page == 1 or page_data.items:
        return render_template('admin/preview_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.preview_list', page=1))


@admin.route("/preview/edit/<int:id>/<int:page>/", methods=['GET', 'POST'])  # 编辑完要返回到列表相应页
@admin_login_req
@admin_auth
def preview_edit(id, page=None):
    form = PreviewForm()  # 点了提交才有数据传过来了，get请求是没有数据

    preview = Preview.query.get_or_404(int(id))

    if request.method == "GET":
        form.title.data = preview.title  # 令html标签有值

    form.logo.validators = []
    if form.validate_on_submit():  # 两个form一个是get带过来的，一个是sumbit带过来的
        data = form.data
        # filter_by只能用=，而不能用!=，没有filter灵活
        preview_count = Preview.query.filter(Preview.title == data['title'], Preview.id != id).count()

        if preview_count >= 1:
            flash('预告已经存在！', 'err')
            return render_template('admin/preview_edit.html', form=form, preview=preview)

        logo = form.logo.data.filename
        if logo:
            file_logo = secure_filename(logo)
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config['UP_DIR'] + preview.logo)
        preview.title = data['title']  # data数据库数据字典
        # 更新不用写额外的session操作
        db.session.commit()
        flash('修改预告成功！', 'ok')
        return redirect(url_for('admin.preview_list', page=page))

    return render_template('admin/preview_edit.html', form=form, preview=preview)  # 为了显示图片，form主要用于标签构造和标签名


@admin.route("/user/list/<int:page>", methods=['GET'])
@admin_login_req
@admin_auth
def user_list(page=None):
    if page is None:
        page = 1
    page_data = User.query.order_by(
        User.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)

    # 没有数据的时候返回第一页
    if page == 1 or page_data.items:
        return render_template('admin/user_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.user_list', page=1))


@admin.route("/user/list/<int:id>/<int:page>", methods=['GET'])
@admin_login_req
@admin_auth
def user_del(id=None, page=None):
    user = User.query.get_or_404(int(id))
    db.session.delete(user)
    db.session.commit()
    flash('删除用户成功！', 'ok')
    return redirect(url_for('admin.user_list', page=page))


@admin.route("/user/view/<int:id>/", methods=['GET'])
@admin_login_req
@admin_auth
def user_view(id=None):
    user = User.query.get_or_404(int(id))

    return render_template('admin/user_view.html', user=user)


@admin.route("/comment/list/<int:page>/")
@admin_login_req
@admin_auth
def comment_list(page=None):
    if page is None:
        page = 1
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == Comment.user_id
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)

    # 没有数据的时候返回第一页
    if page == 1 or page_data.items:
        return render_template('admin/comment_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.comment_list', page=1))


@admin.route("/comment/list/<int:id>/<int:page>", methods=['GET'])
@admin_login_req
@admin_auth
def comment_del(id=None, page=None):
    comment = Comment.query.get_or_404(int(id))
    db.session.delete(comment)
    db.session.commit()
    flash('删除评论成功！', 'ok')
    return redirect(url_for('admin.comment_list', page=page))


@admin.route("/moviecol/list/<int:page>", methods=['GET'])
@admin_login_req
@admin_auth
def moviecol_list(page=None):
    if page is None:
        page = 1
    page_data = Moviecol.query.join(
        User
    ).join(
        Movie
    ).filter(
        Moviecol.user_id == User.id,
        Moviecol.movie_id == Movie.id

    ).order_by(
        Moviecol.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)

    # 没有数据的时候返回第一页
    if page == 1 or page_data.items:
        return render_template('admin/moviecol_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.moviecol_list', page=1))


@admin.route("/moviecol/list/<int:id>/<int:page>", methods=['GET'])
@admin_login_req
@admin_auth
def moviecol_del(id=None, page=None):
    moviecol = Moviecol.query.get_or_404(int(id))
    db.session.delete(moviecol)
    db.session.commit()
    flash('删除评论成功！', 'ok')
    return redirect(url_for('admin.moviecol_list', page=page))


# 操作日志
@admin.route("/oplog/list/<int:page>", methods=['GET'])
@admin_login_req
@admin_auth
def oplog_list(page=None):
    if page is None:
        page = 1
    page_data = Oplog.query.join(
        Admin
    ).filter(
        Oplog.admin_id == Admin.id,
    ).order_by(
        Oplog.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)

    # 没有数据的时候返回第一页
    if page == 1 or page_data.items:
        return render_template('admin/oplog_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.oplog_list', page=1))


@admin.route("/adminloginlog/list/<int:page>")
@admin_login_req
@admin_auth
def adminloginlog_list(page=None):
    if page is None:
        page = 1
    page_data = Adminlog.query.join(
        Admin
    ).filter(
        Adminlog.admin_id == Admin.id,
    ).order_by(
        Adminlog.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)

    # 没有数据的时候返回第一页
    if page == 1 or page_data.items:
        return render_template('admin/adminloginlog_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.adminloginlog_list', page=1))


@admin.route("/userloginlog/list/<int:page>")
@admin_login_req
@admin_auth
def userloginlog_list(page=None):
    if page is None:
        page = 1
    page_data = Userlog.query.join(
        User
    ).filter(
        Userlog.user_id == User.id,
    ).order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)

    # 没有数据的时候返回第一页
    if page == 1 or page_data.items:
        return render_template('admin/userloginlog_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.userloginlog_list', page=1))

#权限添加
@admin.route("/auth/add/",methods=['GET','POST'])
@admin_login_req
@admin_auth
def auth_add():
    form = Authform()
    if form.validate_on_submit():
        data = form.data
        auth_count = Auth.query.filter_by(name=data['name']).count()
        if auth_count >= 1:
            flash('权限已经存在！', 'err')
            return render_template('admin/auth_add.html', form=form)

        auth = Auth(
            name=data['name'],
            url=data['url']
        )
        db.session.add(auth)
        db.session.commit()
        flash('添加权限成功！', 'ok')
        return redirect(url_for('admin.auth_add'))

    return render_template('admin/auth_add.html', form=form)



@admin.route("/auth/list/<int:page>")
@admin_login_req
@admin_auth
def auth_list(page=None):
    if page is None:
        page = 1
    page_data = Auth.query.order_by(
        Auth.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    # 没有数据的时候返回第一页
    if page == 1 or page_data.items:
        return render_template('admin/auth_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.auth_list', page=1))


@admin.route("/auth/del/<int:id>/<int:page>/", methods=['GET'])
@admin_login_req
@admin_auth
def auth_del(id=None, page=None):
    auth = Auth.query.filter_by(id=id).first_or_404()
    db.session.delete(auth)
    db.session.commit()

    flash('删除权限成功！', 'ok')

    return redirect(url_for('admin.auth_list', page=page or 1))#如果没有页码

@admin.route("/auth/edit/<int:id>/<int:page>/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def auth_edit(id, page=None):
    form = Authform()  # 点了提交才有数据传过来了，get请求是没有数据
    auth = Auth.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        # filter_by只能用=，而不能用!=，没有filter灵活
        auth_count = Auth.query.filter(Auth.name == data['name'], Auth.id != id).count()
        auth.name = data['name']
        auth.url = data['url']
        if auth_count >= 1:
            flash('名称已经存在！', 'err')
            return render_template('admin/auth_edit.html', form=form, auth=auth)

        # 更新不用写额外的session操作

        flash('修改权限成功！', 'ok')

        db.session.commit()
        return redirect(url_for('admin.auth_list', page=page))

    return render_template('admin/auth_edit.html', form=form, auth=auth)

@admin.route("/role/add/",methods=['GET','POST'])
@admin_login_req
@admin_auth
def role_add():
    form = Roleform()
    if form.validate_on_submit():
        data = form.data
        role_count = Role.query.filter_by(name=data['name']).count()
        if role_count >= 1:
            flash('角色已经存在！', 'err')
            return render_template('admin/role_add.html', form=form)
        # 多选返回的是数组，需要拼接成字符串
        role = Role(
            name=data['name'],
            #auths=str(data['auths'])[1:-1],
            auths=','.join(map(lambda v:str(v),data['auths'])),
        )
        db.session.add(role)
        db.session.commit()
        flash('添加角色成功！', 'ok')
        return redirect(url_for('admin.role_add'))
    return render_template('admin/role_add.html', form=form)


@admin.route("/role/list/<int:page>")
@admin_login_req
@admin_auth
def role_list(page=None):
    if page is None:
        page = 1
    page_data = Role.query.order_by(
        Role.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    # 没有数据的时候返回第一页
    if page == 1 or page_data.items:
        return render_template('admin/role_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.role_list', page=1))




@admin.route("/role/del/<int:id>/<int:page>/", methods=['GET'])
@admin_login_req
@admin_auth
def role_del(id=None, page=None):
    role = Role.query.filter_by(id=id).first_or_404()
    db.session.delete(role)
    db.session.commit()

    flash('删除角色成功！', 'ok')

    return redirect(url_for('admin.role_list', page=page or 1))#如果没有页码


@admin.route("/role/edit/<int:id>/<int:page>/", methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def role_edit(id, page=None):
    form = Roleform()  # 点了提交才有数据传过来了，get请求是没有数据
    role = Role.query.get_or_404(id)
    if request.method=="GET":
        # form.auths.data = list(map(lambda v:int(v),role.auths.split(',')))
        form.auths.data=eval('%s%s%s'%('[',role.auths,']'))
    if form.validate_on_submit():
        data = form.data
        # filter_by只能用=，而不能用!=，没有filter灵活
        role_count = Role.query.filter(Role.name == data['name'], Role.id != id).count()
        role.name = data['name']
        role.auths =str(data['auths'])[1:-1]
        if role_count >= 1:
            flash('角色已经存在！', 'err')
            return render_template('admin/role_edit.html', form=form, role=role)

        # 更新不用写额外的session操作

        flash('修改角色成功！', 'ok')

        db.session.commit()
        return redirect(url_for('admin.role_list', page=page))

    return render_template('admin/role_edit.html', form=form, role=role)

#添加管理员
@admin.route("/admin/add/",methods=['GET','POST'])
@admin_login_req
@admin_auth
def admin_add():
    form = Adminform()
    from werkzeug.security import generate_password_hash
    if form.validate_on_submit():
        data = form.data
        admin_count = Admin.query.filter_by(name=data['name']).count()
        if admin_count >= 1:
            flash('角色已经存在！', 'err')
            return render_template('admin/admin_add.html', form=form)
        # 多选返回的是数组，需要拼接成字符串
        admin = Admin(
            name=data['name'],
            # auths=str(data['auths'])[1:-1],
            pwd=generate_password_hash(data['pwd']),
            role_id=data['role_id'],
            is_super=1
        )
        db.session.add(admin)
        db.session.commit()
        flash('添加角色成功！', 'ok')
        return redirect(url_for('admin.admin_add'))
    return render_template('admin/admin_add.html', form=form)


#管理员列表
@admin.route("/admin/list/<int:page>")
@admin_login_req
@admin_auth
def admin_list(page=None):
    if page is None:
        page = 1
    page_data = Admin.query.join(Role).filter(
        Admin.role_id==Role.id
    ).order_by(
        Admin.addtime.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    # 没有数据的时候返回第一页
    if page == 1 or page_data.items:
        return render_template('admin/admin_list.html', page_data=page_data)
    elif not page_data.items:
        return redirect(url_for('admin.admin_list', page=1))

