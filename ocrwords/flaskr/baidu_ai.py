import os
import hashlib

from aip import AipOcr, AipNlp
from flask import Blueprint
from flask import request, redirect, render_template, flash

from .db import OCRModel, NLPModel

bp = Blueprint('ai', __name__, url_prefix='/ai')


def init(app):
    APP_ID = app.config['BAIDU_APP_ID']
    APP_KEY = app.config['BAIDU_APP_KEY']
    APP_SECRET_KEY = app.config['BAIDU_APP_SECRET_KEY']
    # 百度AI OCR 文字识别
    global ocr_client
    global nlp_client
    ocr_client = AipOcr(APP_ID, APP_KEY, APP_SECRET_KEY)
    nlp_client = AipNlp(APP_ID, APP_KEY, APP_SECRET_KEY)
    # 上传图片存储路径
    global UPLOAD_FOLDER
    UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']


def str_is_nlp(str):
    if str is None:
        return True
    return True if str.lower() == 'true' else False


@bp.route('/ocr', methods=['POST', 'GET'])
def ocr():
    if request.method == 'GET':
        return render_template('upload.html')
    if 'photo' not in request.files or request.files['photo'].filename == '':
        flash('请选择图片后再点击上传按钮！')
        return redirect(request.url)
    image = request.files['photo']

    # 是否进行自然语言分析
    is_nlp = str_is_nlp(request.form.get('is_nlp'))
    is_nlp = False

    # 根据文件的MD5值进行保存
    data = image.read()
    name = hashlib.md5(data).hexdigest()
    path = os.path.join(UPLOAD_FOLDER, name)

    # 如果文件存在，则表明之前已经识别过，直接从数据库获取即可
    if os.path.exists(path) and is_nlp:
        nlp = NLPModel.query.join(OCRModel).filter(OCRModel.image.like('%{}%'.format(name))).first()
        if nlp is not None:
            return wrapper('成功', content=nlp.result)

    ocr = OCRModel.query.filter_by(image=name).first()
    if ocr is not None:
        if is_nlp:
            return baidu_nlp(ocr.text, ocr.id)
        return wrapper('成功', content=ocr.text)

    # 保存图片
    with open(path, 'wb') as f:
        f.write(data)

    # 获取百度OCR识别结果
    ocr_model = baidu_ocr(data, name)
    if isinstance(ocr_model, dict):
        return ocr_model
    if not is_nlp:
        return wrapper('成功', content=ocr_model.text)
    return baidu_nlp(ocr_model.text, ocr_model.id)


def baidu_ocr(data, name):
    result = ocr_client.accurate(data)

    if 'error_code' in result or 'error_msg' in result:
        return wrapper(result.get('error_msg'), result.get('error_code'))

    words_result = result.get('words_result')
    text = ''
    for word in words_result:
        text += word.get('words')
    # 写入数据库
    ocr_model = OCRModel(name, str(result), text)
    ocr_model.save()
    return ocr_model


@bp.route('/nlp', methods=['POST', 'GET'])
def nlp():
    if request.method == 'GET':
        text = request.args.get('text', type=str)
    else:
        text = request.form.get('text', type=str)
    return baidu_nlp(text)


def baidu_nlp(text, orc_id=None):
    if text is None:
        return wrapper('请输入需要处理的文本', status=1)
    # 如果数据库中有记录，则直接返回
    m = hashlib.md5()
    m.update(text.encode(encoding='utf8'))
    md5 = m.hexdigest()
    nlp = NLPModel.query.filter_by(md5=md5).first()
    if nlp is not None:
        return wrapper('成功', content=nlp.result)

    result = nlp_client.lexer(text)

    if 'error_code' in result or 'error_msg' in result:
        return wrapper(result.get('error_msg'), result.get('error_code'))

    items = result.get('items')

    words = dict()
    for item in items:
        key = item.get('item')
        pos = item.get('pos')
        count_dict = words.get(key)
        if count_dict is None:
            count_dict = dict()
        if count_dict.get(pos) is None:
            count_dict[pos] = 1
        else:
            count_dict[pos] += 1
        words[key] = count_dict

    nlp_model = NLPModel(text, str(result), str(words), orc_id)
    nlp_model.save()
    return wrapper('成功', content=str(words))


def wrapper(msg, status=200, content=None):
    if content is None:
        return {'msg': msg, 'status': status}
    return {'msg': msg, 'status': status, 'content': content}
