from __future__ import print_function

import google.auth, mysql.connector, urllib, json, traceback, datetime, requests, zipfile, shutil, os, re, threading, sys, logging
from urllib.parse import urlencode
from mysql.connector import Error
from xlsxwriter.utility import xl_col_to_name
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from drive import Drive
from contextlib import contextmanager

from logger import get_logger



config = {
    "host": r"194.67.116.213",
    "port": "3306",
    "user": r"root",
    "password": r"zs$N7b*7F2Zq",
    "database": r""
}
config['user']=r"root"
config['password']=r"zs$N7b*7F2Zq"

CURDIR = os.path.dirname(os.path.abspath(__file__))

def check_link(link):
    #regex из джанго
    if link is None:
        return False
    regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(regex, link) is not None


def save_from_YD(link, process_id):
    global CURDIR, logger
    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
    public_key = link

    # Получаем загрузочную ссылку
    final_url = base_url + urlencode(dict(public_key=public_key))
    response = requests.get(final_url)
    download_url = response.json()['href']

    # Загружаем файл и сохраняем его
    download_response = requests.get(download_url)
    with open('downloaded_file.zip', 'wb') as f:   # Здесь укажите нужный путь к файлу
        f.write(download_response.content)

    #распаковка файла в папку downloaded_folder
    with zipfile.ZipFile('downloaded_file.zip', 'r') as zip_ref:
        zip_ref.extractall(f'folder {process_id}')

def save_from_GD(link, process_id):
    global CURDIR, logger
    __driver = Drive(logger)
    link = link.replace('?usp=sharing', '')
    id = link.split('/')[-1]
    
    dir = CURDIR+f"/folder {process_id}"
    if not os.path.exists(dir):
        os.mkdir(dir)

    for i in __driver.get_files_in_folder(id):
        if 'folder' in i['mimeType']:
            continue
        __driver.download(i['id'], CURDIR+f'/folder {process_id}/'+i['name'])



def db_connect(func):
    def execute_command(config, database,  *args, **kwargs):
        config_with_db = config
        config_with_db['database']=database
        result = []
        try:
            connection = mysql.connector.connect(**config_with_db)
            #print(config_with_db)
        except Error as e:
            return e 
        try:
            if connection.is_connected():
                db_Info = connection.get_server_info()
                #print("Connected to MySQL Server version ", db_Info)
                cursor = connection.cursor(buffered=True)
                result=func(config, database, *args, cursor=cursor, connection=connection, **kwargs)
        except Error as e:
            raise e
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                #print("MySQL connection is closed")
        return result
    return execute_command

@db_connect
def get_payment_request_packs(config, database, cursor=None, **kwargs): # [ ( i,,, ),,, ] -> [ { i:j,,, },,, ]
    cursor.execute(f"""SELECT * FROM {database}.payment_requests_packs WHERE id = {kwargs['packs_id']}""")
    columns = cursor.column_names
    code_id = cursor.fetchall()
    result = [{val:i[num] for num, val in enumerate(columns)} for i in code_id] #опасность: объединяются колонки с одинаковыми названиями
    return result

@db_connect
def get_payment_requests_by_pack(config, database, cursor=None, **kwargs): # [ ( i,,, ),,, ] -> [ { i:j,,, },,, ]
    cursor.execute(f"""SELECT * FROM {database}.payment_requests WHERE payment_requests_packs_id = {kwargs['payment_pack']}""")
    columns = cursor.column_names
    code_id = cursor.fetchall()
    result = [{val:i[num] for num, val in enumerate(columns)} for i in code_id] #опасность: объединяются колонки с одинаковыми названиями
    return result

@db_connect
def get_contract(config, database, cursor=None, **kwargs): # [ ( i,,, ),,, ] -> [ { i:j,,, },,, ]
    cursor.execute(f"SELECT * FROM {database}.contracts WHERE id = {kwargs['contracts_id']}")
    columns = cursor.column_names
    code_id = cursor.fetchall()
    result = [{val:i[num] for num, val in enumerate(columns)} for i in code_id] #опасность: объединяются колонки с одинаковыми названиями
    return result

@db_connect
def get_contractor(config, database, cursor=None, **kwargs): # [ ( i,,, ),,, ] -> [ { i:j,,, },,, ]
    cursor.execute(f"SELECT * FROM {database}.contractors WHERE id = {kwargs['contractors_id']}")
    columns = cursor.column_names
    code_id = cursor.fetchall()
    result = [{val:i[num] for num, val in enumerate(columns)} for i in code_id] #опасность: объединяются колонки с одинаковыми названиями
    return result

@contextmanager
def main_function(id, process_id):
    logger = get_logger(str(process_id))
    rows = get_payment_request_packs(config, 'spv_UU', packs_id=id)
    driver = Drive(logger)
    root_folder = "1zonjISjMuuHhBXvKLmWrzd-_COA0mnP3" #папка Файлы для отправки в банк
    # в случае новой папки необходимо будет найти её с помощью driver.get_files, а в возвращённом массиве словарей найти по критериям отсуствия родителей и по владельцам
    if len(rows)!=0:
        row=rows[0]
    else:
        yield "[Error] 1: there is no such records in db"
        return

    folder_1st_level = f"№{row['number']} от {row['date'].strftime('%d-%m-%Y')} | {row['id']}"
    
    if row['date'] is not None and row['id'] is not None:
        folder_1st_level_id = driver.create_folder(folder_1st_level, root_folder)
    else:
        yield "[Error] 2: date is none or id is none"
        return

    yield folder_1st_level_id #ВОЗВРАЩАЕТСЯ ID ПАПКИ, КОД НИЖЕ ВЫПОЛНЯЕТСЯ ПОСЛЕ ВЫХОДА ИЗ ПОЛЯ WITH

    rows_in_pack = get_payment_requests_by_pack(config, 'spv_UU', payment_pack = row['id'])
    if len(rows_in_pack)==0:
        yield "[Error] 3: no requests for pack"
        return
    def async_part():
        for packn, pack_row in enumerate(rows_in_pack):
            
            contract_id = pack_row['contracts_id']
            contract = get_contract(config, 'spv_UU', contracts_id = contract_id)[0]
            contractor = get_contractor(config, 'spv_UU', contractors_id = contract['contractors_id'])[0]
            folder_2nd_level = f"{packn+1} {contractor['name']}" #МОЖНО УБРАТЬ +1

            logger.info(contract['link'])
            logger.info(f"\n folder 1:{folder_1st_level}, folder 2:{folder_2nd_level}, \n")

            folder_2nd_level_id = driver.create_folder(folder_2nd_level, folder_1st_level_id)
            if check_link(contract['link']):
                if "yandex" in contract['link']:
                    save_from_YD(contract['link'], process_id)
                elif "google" in contract['link']:
                    save_from_GD(contract['link'], process_id)
                else:
                    save_from_YD(contract['link'], process_id)

            # folder path
            dir_path = CURDIR+f'/folder {process_id}/'            
            
            # upload files recursive
            def recursive_upload(dir_path, folder_id):
                files = os.listdir(dir_path)
                for i in files:
                    if os.path.isfile(dir_path+'/'+i):
                        driver.upload(dir_path+'/'+i,folder_id)
                    elif os.path.isdir(dir_path+'/'+i):
                        recursive_upload(dir_path+'/'+i, driver.create_folder(i,folder_id))

            recursive_upload(dir_path,folder_2nd_level_id)

            #kill folder
            shutil.rmtree(dir_path)
    
    t = threading.Thread(target=async_part, name=str(process_id))
    t.start()
    logger.info(f'started {process_id}')

if __name__ == '__main__':
    print('данный скрипт запускается из flask-redirecter')