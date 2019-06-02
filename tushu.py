from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo, InputRequired

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:mysql@127.0.0.1:3306/test1'
# 动态追踪修改设置，如未设置只会提示警告
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 查询时会显示原始SQL语句
app.config['SQLALCHEMY_ECHO'] = False
app.secret_key = "afadfsad"
# False为关闭wtf攻击，True为开启
app.config['WTF_CSRF_ENABLED'] = True

db = SQLAlchemy(app)


class Auth(db.Model):
    __tablename__ = "auths"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    authors = db.relationship("Book", backref="auth")

    def __repr__(self):
        return "Role{}{}".format(self.id, self.name)


class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # 外键关联在多的一方中，使用db.ForeignKey(Auth.id)
    auth_id = db.Column(db.Integer, db.ForeignKey(Auth.id))

    def __repr__(self):
        return "Author {}{}".format(self.id, self.name)


@app.route("/")
def index():
    return "hello world"


# 只完成指定的渲染事情，不涉及表单和数据提交
@app.route("/demo1")
def demo1():
    author = Auth.query.all()
    return render_template("demo1.html", author=author)


# 制作一个form表单
class RegisterForm(FlaskForm):
    username = StringField("作者：", validators=[InputRequired("请输入作者")], render_kw={"placeholder": "请输入用户名"})
    bookname = StringField("书名：", validators=[InputRequired("请输入书名")], render_kw={"placeholder": "请输入书名"})
    submit = SubmitField("添加")


# 完成表单提交的事情和数据展示
@app.route("/demo2", methods=["GET", "POST"])
def demo2():
    # 初始化一个表单对象，传给模板即可显示
    regist_form = RegisterForm()
    if regist_form.validate_on_submit():
        # 从表单中获取作者和书名,到这里说明验证通过了
        username = request.form.get("username")
        bookname = request.form.get("bookname")
        # print(username, bookname)
        # 判断作者是否已经存在,存在的话，直接添加书到数据库
        if Auth.query.filter(Auth.name == username).first():
            # 还要判断书是否已经存在，存在的话，闪现消息
            if Book.query.filter(Book.name == bookname).first():
                flash("书籍已经存在了，请勿重复添加")
            # 如果判断不存在，再进行添加
            else:
                try:
                    author1 = Auth.query.filter(Auth.name == username).first().id
                    book1 = Book(name=bookname, auth_id=author1)
                    db.session.add(book1)
                    db.session.commit()
                    flash("提交成功")
                except Exception as e:
                    print(e)
                    db.session.rollback()
                    flash("提交失败")
        # 否则的话,添加作者到数据库，并添加书到数据库
        else:
            try:
                # 添加的时候，先添加作者，再添加书名，因为书有一个外键要设置为作者的id
                author1 = Auth(name=username)
                db.session.add(author1)
                db.session.commit()

                book1 = Book(name=bookname, auth_id=author1.id)
                db.session.add(book1)
                db.session.commit()
                flash("提交成功")
            except Exception as e:
                print(e)
                db.session.rollback()
                flash("提交失败")
    # 当输入内容为空的时候，闪现出一条提示消息
    else:
        # 判断请求方式：

        flash("请输入相应的内容")
    # 从数据库中查询作者信息，返回给模板，模板就可以渲染
    author = Auth.query.all()
    return render_template("demo2.html", author=author, form=regist_form)


# 定义一个删除书籍的函数,前端请求一个删除的请求函数，传递书的id进来
@app.route("/delbook/<bookid>")
def del_book(bookid):
    print(bookid)
    # 获取到书名之后，执行删除操作
    # Book.query.filter(Book.id == bookid).detete()
    book = Book.query.get(bookid)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for("demo2"))


# 定义一个删除作者的操作
@app.route("/delauth/<authid>")
def def_auth(authid):
    # print(authid)
    auth = Auth.query.get(authid)
    books = Auth.query.filter(Auth.id == auth.id).first().authors
    print(auth, books)
    # 删除先删书，再删除作者
    Book.query.filter(Book.auth_id == authid).delete()
    db.session.commit()
    # 再删除作者
    Auth.query.filter(Auth.id == authid).delete()
    # Auth.query.get(authid).delete()
    db.session.commit()
    return redirect(url_for("demo2"))


if __name__ == "__main__":
    db.drop_all()
    db.create_all()
    # 生成数据
    au1 = Auth(name='老王')
    au2 = Auth(name='老尹')
    au3 = Auth(name='老刘')
    # 把数据提交给用户会话
    db.session.add_all([au1, au2, au3])
    # 提交会话
    db.session.commit()
    bk1 = Book(name='老王回忆录', auth_id=au1.id)
    bk2 = Book(name='我读书少，你别骗我', auth_id=au1.id)
    bk3 = Book(name='如何才能让自己更骚', auth_id=au2.id)
    bk4 = Book(name='怎样征服美丽少女', auth_id=au3.id)
    bk5 = Book(name='如何征服英俊少男', auth_id=au3.id)
    # 把数据提交给用户会话
    db.session.add_all([bk1, bk2, bk3, bk4, bk5])
    # 提交会话
    db.session.commit()
    app.run(debug=True)
