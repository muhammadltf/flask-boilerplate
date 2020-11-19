#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request, jsonify, Response
# from flask.ext.sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from forms import *
import os
import requests, json
from werkzeug.exceptions import BadRequest
from flask_cors import CORS


#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
allowed_sites = os.getenv('allowed-sites')
CORS(app, origins=[allowed_sites])

app.config.from_object('config')
#db = SQLAlchemy(app)

# Automatically tear down SQLAlchemy.
'''
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()
'''

# Login required decorator.
'''
def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap
'''
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def home():
    return render_template('pages/placeholder.home.html')


@app.route('/about')
def about():
    return render_template('pages/placeholder.about.html')


@app.route('/login')
def login():
    form = LoginForm(request.form)
    return render_template('forms/login.html', form=form)


@app.route('/register')
def register():
    form = RegisterForm(request.form)
    return render_template('forms/register.html', form=form)


@app.route('/forgot')
def forgot():
    form = ForgotForm(request.form)
    return render_template('forms/forgot.html', form=form)

@app.route("/ask", methods=["POST"])
def ask():

    #check whether user sends form or json data
    try:
        req_data = request.get_json()
        query = req_data['query']
        command = req_data['command']
    except (TypeError, BadRequest, KeyError):
        query = request.form['query']
        command = request.form['command']

    for end_utterance in ["以上", "終わり"]:
        if end_utterance in query:
            query = "END"
            break

    for thanks_utterance in ["ありがとう", "どうも"]:
        if thanks_utterance in query:
            query = "THANKS"
            break
    
    #HOW TO READ
    read = ""
    #ADD ON
    suffix = ""

    if query == "START":
        response_text = "初めまして！ロココと申します。お問い合わせは何でしょう？"

        if command == "naisen":
            response_text = "初めまして！内線検索サービスです。検索したい社員の名前と部署をどうぞ！"

        state = "GREET"
    elif query == "END":
        response_text = "お問い合わせがないようなので、失礼させて頂きます。ありがとうございました。"
        state = "FINISH"
    elif query == "THANKS":
        response_text = "どういたしまして。お役に立てたならうれしいです。"
        state = "REPLY"
    else:
        url = 'https://chatbot-kokoro.azurewebsites.net/qnamaker/knowledgebases/f2a8edcd-2631-497b-98e4-918663e299d0/generateAnswer'
        
        data = "{}"
        if command == "default":
            data = "{'question': '"+query+"','strictFilters': [{'name':'category','value':'general_info'},{'name':'editorial','value':'chitchat'}], 'strictFiltersCompoundOperationType': 'OR'}"
        else:
            data = "{'question': '"+query+"','strictFilters': [{'name':'category','value':'"+command+"'}]}" 
            suffix = "スケジュールを確認しますか？"

        header = {'content-type': 'application/json', 'authorization': 'EndpointKey 30168be7-2ad2-4346-af8c-83fcc05069eb'}
        response = requests.post(url, data=data.encode("utf-8"), headers= header)       
        response_text = json.loads(response.text)["answers"][0]["answer"]
        
        if "￥" in response_text:
            resp_raw = response_text.split("￥")
            response_text = resp_raw[0] + suffix
            read = resp_raw[1] + suffix

        if "KB" in response_text:
            if command == "default":
                response_text = "申し訳ありません。私の勉強が足りないようです。私にはわかりません。"
            elif command == "naisen":
                response_text = "申し訳ありません。まだ登録されていないようです。"

        state = "REPLY"

    payload = json.dumps({
        'answer': response_text,
        'read': read,
        'state': state
    }, ensure_ascii=False)
    print(response_text)
    return payload


# Error handlers.


@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    # app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    # app.logger.addHandler(file_handler)
    # app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
