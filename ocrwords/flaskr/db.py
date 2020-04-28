import click
from flask_sqlalchemy import SQLAlchemy
from flask.cli import with_appcontext

db = SQLAlchemy()


def init_db(app):
    db.init_app(app)
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_commond)


def close_db(e=None):
    db.close_all_sessions()


@click.command('init-db')
@click.option('--drop', is_flag=True, help='Create after drop.')
@with_appcontext
def init_db_commond(drop):
    """Initialize the database."""
    if drop:
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')


class OCRModel(db.Model):
    __tablename__ = 'ocr'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image = db.Column(db.String(255))
    result = db.Column(db.Text)
    text = db.Column(db.Text)

    def __init__(self, image, original_result, text):
        self.image = image
        self.result = original_result
        self.text = text

    def __repr__(self):
        return "<Note (image='%s', result='%s', text='%s')>" % (self.image, self.result, self.text)

    def save(self):
        db.session.add(self)
        db.session.commit()


class NLPModel(db.Model):
    __tablename__ = 'nlp'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    md5 = db.Column(db.String(50))
    text = db.Column(db.Text)
    original_result = db.Column(db.Text)
    result = db.Column(db.Text)
    orc_id = db.Column(db.Integer, db.ForeignKey('ocr.id'))

    def __init__(self, text, original_result, result, ocr_id=None):
        import hashlib
        m = hashlib.md5()
        m.update(text.encode(encoding='utf8'))
        self.md5 = m.hexdigest()
        self.text = text
        self.original_result = original_result
        self.result = result
        self.orc_id = ocr_id

    def __repr__(self):
        return "<Note (text='%s',nlp_result='%s',result='%s',ocr_id='%d')>" % (
            self.text, self.original_result, self.result, self.orc_id)

    def save(self):
        db.session.add(self)
        db.session.commit()
