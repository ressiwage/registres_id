import io
import os, sys
import pickle
import shutil

from mimetypes import MimeTypes

import requests
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account


class Drive:
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    sys.setrecursionlimit = 1000
    def get_files(self):
        results = (
            self.service.files()
            .list(
                pageSize=1000,
                fields="files(id, name, mimeType, parents, trashed, fileExtension, owners)",
            )
            .execute()
        )
        items = [i for i in results.get("files", []) if i['trashed'] == False]
        return items

    def get_files_in_folder(self, folder_id):
        results = (
            self.service.files()
            .list(
                q=f"'{folder_id}' in parents and trashed=false",
                pageSize=100,
                fields="files(id, name, mimeType, parents, trashed, fileExtension, owners)",
            )
            .execute()
        )
        items = [i for i in results.get("files", []) if i['trashed'] == False]
        return items

    def __init__(self, logger):
        self.creds = None

        self.service = build("drive", "v3", credentials=service_account.Credentials.from_service_account_file('credentials.json'))
        self.logger=logger
        """print("All available files: \n")
        for i in self.get_files():
            print(i['name'], i['mimeType'], end=" |owners: ")
            for j in i['owners']:
                print(j['emailAddress'])"""
        # print(*self.get_files(), sep="\n")
        # print('\n\n')

    def download(self, file_id, file_name):
        mime = None
        files = self.get_files_in_folder(ID)
        mime = [i for i in files if i['id'] == file_id][0]['mimeType']
        name = [i for i in files if i['id'] == file_id][0]['name']
        self.logger.info(mime)
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()

        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        done = False

        try:
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)

            with open(file_name, "wb") as f:
                shutil.copyfileobj(fh, f)

            self.logger.info(f"{name} Downloaded")
            return True
        except Exception as e:
            self.logger.error(f"file named {name} was not downloaded. \ndetails: {e}\n")
            return False

    def upload(self, filepath, parent_id):
        name = filepath.split("\\")[-1]
        mimetype = MimeTypes().guess_type(name)[0]
        if mimetype is None:
            mimetype="none"
        file_metadata = {"name": name, "parents": [parent_id], 'mimeType': '*/*'}

        try:
            findFile = [i for i in self.get_files_in_folder(parent_id) if i['trashed']==False]
            findFileName = [i['name'] for i in findFile]
            if name not in findFileName:

                media = MediaFileUpload(filepath,  mimetype='*/*',
                                        resumable=True)

                file = (
                    self.service.files()
                    .create(body=file_metadata, media_body=media, fields="id")
                    .execute()
                )

                self.logger.info('File ID: ' + file.get('id'))

                self.logger.info(f"File Uploaded: {name}")
            else:
                self.delete_file(findFile['id'])
                self.logger.warning(f'deleted file {name}, mimetype: {mimetype}')
                self.upload(filepath, parent_id)

        except Exception as e:
            raise Exception(f"Can't Upload File {name}: {e}")

    def create_folder(self, name, parent_id):
        find_file_in_folder = [i for i in self.get_files_in_folder(parent_id) if i['name']==name and 'folder' in i['mimeType'] and i['trashed']!=True]
        
        if  len(find_file_in_folder)==0: 
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id],
            }
            folder_id = self.service.files().create(
                body=file_metadata, fields='id').execute().get('id')
        else:
            self.logger.warning(f'удаляется папка {name}')
            self.delete_file(find_file_in_folder[0]['id'])
            folder_id = self.create_folder(name, parent_id)
        return folder_id
    def delete_file(self, id):
        try:
            self.service.files().delete(fileId=id).execute()
        except Exception as e:
            self.logger.error ('An error occurred: %s' % e)
    def delete_file(self, id):
        try:
            self.service.files().delete(fileId=id).execute()
        except Exception as e:
            self.logger.error ('An error occurred: %s' % e)

ID = "1H2UH1Bny6FvGlL2Z65fPuoYF7pXQLZXn"
if __name__ == '__main__':
    a = Drive()
    #a.download('1E1mg14m4AJXDiAhIsRnwQ4iK7vlXFtsw', 'folder')
    a.upload('./creds.json', ID)
    print(*a.get_files_in_folder(ID), sep="\n")