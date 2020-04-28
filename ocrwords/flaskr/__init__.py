import click

from flask import Flask, redirect, url_for


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')

    # 初始化数据库
    from . import db
    db.init_db(app)

    # 注册ocr蓝图
    from . import baidu_ai
    baidu_ai.init(app)
    app.register_blueprint(baidu_ai.bp)

    # 自定义Flask命令，查看相关配置
    @app.cli.command()
    def echo_config():
        click.echo("应用工厂")
        click.echo("自定义配置")
        click.echo("百度APP_ID:" + app.config['BAIDU_APP_ID'])
        click.echo("百度APP_KEY:" + app.config['BAIDU_APP_KEY'])
        click.echo("百度APP_SECRET_KEY:" + app.config['BAIDU_APP_SECRET_KEY'])
        click.echo("上传图片的存储路径:" + app.config['UPLOAD_FOLDER'])
        click.echo("数据库地址:" + app.config['SQLALCHEMY_DATABASE_URI'])

    @app.route('/')
    def index():
        return redirect(url_for('ai.ocr'))

    return app
