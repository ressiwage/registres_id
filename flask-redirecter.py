# encoding: utf-8

from flask import Flask, render_template,  request, redirect, jsonify
import random, os, json, mysql.connector, datetime, re, hashlib, traceback, sys, shutil
from mysql.connector import Error
from main import main_function
from logger import get_logger
logger = get_logger('flask')

app=Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.route('/')
def index():
    return r"""отправьте get-запрос вида {имя сайта}/v1?id={id}"""

@app.route('/webhooks/copyfolder', methods=['GET'])
def selectall():
    id = request.args.get('id')
    
    process_id = random.randint(1000000,10000000)
    try:
        int(id)
    except:
        return render_template("error.html",msg='id должен быть числом')
    with main_function(int(id), process_id) as folder:
        logger.info('ID IS '+folder)

        if '[Error]' not in folder:
            return jsonify({'payment_request_pack_folder_url': r'https://drive.google.com/drive/folders/'+folder})
        else:
            return render_template("error.html",msg='folder')

@app.route('/v1/delete_file_folders', methods=['GET'])
def delete_trash():
    CURDIR = os.path.dirname(os.path.abspath(__file__))
    files = os.listdir(CURDIR)
    deleted=[]
    for i in files:
        if os.path.isdir(CURDIR+'\\'+i) and 'folder' in i:
            shutil.rmtree(CURDIR+'\\'+i)
            deleted.append(i)
    return f"deleted files: {', '.join(deleted)}"

if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0',  port=5000)







