import os
import sys
import flask_api
import pugsql
from flask import request, jsonify, Response
from flask_api import status, exceptions
from flask_cors import CORS, cross_origin
from werkzeug.security import generate_password_hash, check_password_hash
import paramiko
from scp import SCPClient

app = flask_api.FlaskAPI(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

def crawl(pwd='/'):
    crawl_cmd = 'du -a -h --time --max-depth=1 ' + pwd + ' 2>/dev/null'
    directory_list = []
    directory = os.popen(crawl_cmd).read().split('\n')
    for i in range(0, len(directory) - 2):
        size, time, path = directory[i].split('\t')
        split_path = path.split('/')
        name = split_path[len(split_path) - 1]
        path = pwd + name
        if os.path.isfile(path):
            file_type = 0
        elif os.path.isdir(path):
            file_type = 1
        else:
            file_type = 2
        directory_list.append([name, size, file_type, time, path])
    return directory_list

@app.route('/', methods=['GET'])
@cross_origin()
def home():
    return crawl(pwd='.')

@app.route('/api/v1/cloud/employee/crawl', methods=['POST', 'GET'])
@cross_origin()
def crawl_cloud():
    if request.method=='GET':
        return crawl(pwd='.')
    elif request.method=='POST':
        return crawl_cloud_post()

def crawl_cloud_post():
    crawl_data = request.data
    required_fields = ['path']
    if not all([field in crawl_data for field in required_fields]):
        raise exceptions.ParseError()
    try:
        path = crawl_data['path']
        result = crawl(path)
    except Exception as e:
        return { 'Error': str(e) }, status.HTTP_409_CONFLICT
    return result

@app.route('/api/v1/cloud/employee/copy', methods=['POST', 'GET'])
@cross_origin()
def copy_cloud():
    if request.method=='GET':
        return {}
    elif request.method=='POST':
        return copy_cloud_post()

@app.route('/api/v1/cloud/employee/delete', methods=['POST', 'GET'])
@cross_origin()
def del_cloud():
    if request.method=='GET':
        return {}
    elif request.method=='POST':
        return del_cloud_post()

def copy_cloud_post():
    copy_data = request.data
    required_fields = ['sourcePath', 'destinationIP', 'destinationUser', 'destinationPath', 'recursive', 'private_key', 'copy_or_transfer']
    if not all([field in copy_data for field in required_fields]):
        raise exceptions.ParseError()
    try:
        source_path = copy_data['sourcePath']
        recursive = copy_data['recursive']
        destination_path = copy_data['destinationPath']
        destination_ip = copy_data['destinationIP']
        destination_user = copy_data['destinationUser']
        priv_key = copy_data['private_key']
        copy_or_transfer = copy_data['copy_or_transfer']	
        command = "python3 utility.py " + str(source_path) + " " + str(destination_path) + " " + str(destination_ip) + " " +  str(destination_user) + " " +  str(recursive) + " " + str(priv_key) + " " + str(copy_or_transfer)
        os.system(command)
        data = copy_data
    except Exception as e:
        return { 'Error': str(e) }, status.HTTP_409_CONFLICT
    return data

def del_cloud_post():
    del_data = request.data
    required_fields = ['sourcePath', 'recursive']
    if not all([field in del_data for field in required_fields]):
        raise exceptions.ParseError()
    try:
        source_path = del_data['sourcePath']
        recursive = del_data['recursive']
        command = "python3 utility.py " + str(source_path) + " " + str(recursive)
        os.system(command)
        data = del_data
    except Exception as e:
        return { 'Error': str(e) }, status.HTTP_409_CONFLICT
    return data
