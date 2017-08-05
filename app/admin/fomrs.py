# coding:utf8
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, ValidationError,EqualTo
from app.models import Admin, Tag, Auth,Role

tags = Tag.query.all()

role_list=Role.query.all()

class LoginForm(FlaskForm):
    """管理员登录"""
    account = StringField(
        label='账号',
        validators=[
            DataRequired('请输入账号')
        ],
        description='账号',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入账号！',
            'required': 'required'
        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired('请输入密码')
        ],
        description='密码',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入密码！',
            'required': 'required'
        }
    )
    submit = SubmitField(
        label="登录",
        render_kw={
            "class": "btn btn-primary btn-block btn-flat",
        }
    )

    def validate_account(self, field):
        account = field.data
        admin = Admin.query.filter_by(name=account).count()
        if admin == 0:
            raise ValidationError('账号不存在!')


class TagForm(FlaskForm):
    name = StringField(
        label="名称",
        validators=[
            DataRequired('请输入标签！')
        ],
        description='标签',
        render_kw=dict(
            class_="form-control",
            id="input_name",
            placeholder="请输入标签名称！",

        ),

    )
    submit = SubmitField(
        label="保存",
        render_kw={
            "class": "btn btn-primary",
        }
    )


class MovieForm(FlaskForm):
    title = StringField(
        label="片名",
        validators=[
            DataRequired('请输入片名！')
        ],
        description='片名',
        render_kw=dict(
            class_="form-control",
            id="input_title",
            placeholder="请输入片名！",

        ),

    )
    url = FileField(
        label="文件",
        validators=[
            DataRequired('请上传文件')
        ],
        description='文件',

    )
    info = TextAreaField(
        label="简介",
        validators=[
            DataRequired('请输入简介！')
        ],
        description='片名',
        render_kw=dict(
            class_="form-control",
            row=10
        ),

    )
    logo = FileField(
        label="封面",
        validators=[
            DataRequired('请上传封面')
        ],
        description='封面',

    )
    star = SelectField(
        label="星级",
        validators=[
            DataRequired('请选择星级！')
        ],
        description='星级',
        coerce=int,
        choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星'), ],

        render_kw=dict(
            class_="form-control",
        ),
    )
    tag_id = SelectField(
        label="标签",
        validators=[
            DataRequired('请选择标签！')
        ],
        description='标签',
        coerce=int,
        choices=[(v.id, v.name) for v in tags],

        render_kw=dict(
            class_="form-control",
        ),
    )
    area = StringField(
        label="地区",
        validators=[
            DataRequired('请输入地区！')
        ],
        description='地区',
        render_kw=dict(
            class_="form-control",
            placeholder="请输入地区！",

        ),

    )
    length = StringField(
        label="片长",
        validators=[
            DataRequired('请输入片长！')
        ],
        description='片长',
        render_kw=dict(
            class_="form-control",
            placeholder="请输入片长！",

        ),

    )
    release_time = StringField(
        label="上映时间",
        validators=[
            DataRequired('请输入上映时间！')
        ],
        description='上映时间',
        render_kw=dict(
            class_="form-control",
            placeholder="请输入上映时间！",
            id='input_release_time'
        ),

    )
    submit = SubmitField(
        label="保存",
        render_kw={
            "class": "btn btn-primary",
        }
    )


class PreviewForm(FlaskForm):
    title = StringField(
        label="预告标题",
        validators=[
            DataRequired('请输入预告标题！')
        ],
        description='预告标题',
        render_kw=dict(
            class_="form-control",
            placeholder="请输入预告标题！",

        ),

    )
    logo = FileField(  # 会生成type='file'
        label="预告封面",
        validators=[
            DataRequired('请上传预告封面')
        ],
        description='预告封面',
        render_kw=dict(
            onchange="preview(this)"

        ),

    )
    submit = SubmitField(
        label="保存",
        render_kw={
            "class": "btn btn-primary",
        }
    )


class PwdForm(FlaskForm):
    old_pwd = PasswordField(
        label="旧密码",
        validators=[
            DataRequired('请输入旧密码')
        ],
        description='旧密码',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入旧密码！',
        }
    )
    new_pwd = PasswordField(
        label="新密码",
        validators=[
            DataRequired('请输入新密码')
        ],
        description='新密码',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入新密码！',
        }
    )
    submit = SubmitField(
        label="保存",
        render_kw={
            "class": "btn btn-primary",
        }
    )

    # 会对输入框进行判断校验,validate_字段
    def validate_old_pwd(self, field):
        from flask import session
        pwd = field.data
        name = session['admin']
        admin = Admin.query.filter_by(
            name=name
        ).first()
        if not admin.check_pwd(pwd):
            raise ValidationError('旧密码错误')


class Authform(FlaskForm):
    name = StringField(
        label="权限名称",
        validators=[
            DataRequired('请输入权限名称')
        ],
        description='权限名称',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入权限名称！',
        }
    )
    url = StringField(
        label="权限地址",
        validators=[
            DataRequired('请输入权限地址')
        ],
        description='权限地址',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入权限地址！',
        }
    )
    submit = SubmitField(
        label="保存",
        render_kw={
            "class": "btn btn-primary",
        }
    )


class Roleform(FlaskForm):
    name = StringField(
        label="角色名称",
        validators=[
            DataRequired('请输入角色名称')
        ],
        description='角色名称',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入角色名称！',
        }
    )
    auth_list = Auth.query.all()
    auths = SelectMultipleField(
        label="权限列表",
        validators=[
            DataRequired('请选择权限')
        ],
        coerce=int,
        choices=[(v.id, v.name) for v in auth_list],
        description='权限列表',
        render_kw={
            "class": "form-control",
        }
    )
    submit = SubmitField(
        label="保存",
        render_kw={
            "class": "btn btn-primary",
        }
    )

class Adminform(FlaskForm):
    name = StringField(
        label='管理员名称',
        validators=[
            DataRequired('请输入管理员名称')
        ],
        description='管理员名称',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入管理员名称！',

        }
    )
    pwd = PasswordField(
        label="管理员密码",
        validators=[
            DataRequired('请输入管理员密码')
        ],
        description='管理员密码',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入管理员密码！',
        }
    )
    reppwd = PasswordField(
        label="管理员重复密码",
        validators=[
            DataRequired('请输入管理员重复密码'),
            EqualTo('pwd',message='两次密码不一致')#重复校验
        ],
        description='管理员重复密码',
        render_kw={
            "class": "form-control",
            "placeholder": '请输入管理员重复密码！',
        }
    )

    role_id=SelectField(
        label='所属角色',
        coerce=int,
        choices=[(v.id,v.name) for v in role_list],
        render_kw={
            "class": "form-control",
            "placeholder": '请输入管理员重复密码！',
        }
    )
    submit = SubmitField(
        label="保存",
        render_kw={
            "class": "btn btn-primary",
        }
    )