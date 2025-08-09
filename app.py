from flask import Flask, redirect, request, jsonify
import os
import notes_ai as nai
import boto3
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

key= os.getenv('AWS_ACCESS_KEY')
access_key= os.getenv('AWS_SECRET_KEY')
bucket_name= "sheshya-ai-notes"

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.before_request
def before_request():
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = app.make_default_options_response()
    
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization,access-control-allow-origin')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Origin', '*')

        return response


def checkIfNotesExists(notes_path):
    s3 = boto3.client('s3', aws_access_key_id = key, aws_secret_access_key = access_key)
    try:
        s3.head_object(Bucket = bucket_name, Key = notes_path)
        return True
    except:
        return False

@app.route('/',methods=['GET'])
def welcome():
    return jsonify("working")


@app.route('/getNotes/',methods=['POST'])
def getnotes():
    data = request.get_json()
    clas = data['class']
    subject = data['subject']
    chapter = data['chapter']
    topic = data['topic']

    base_path = f"storageBuffer/notes/{clas}/{subject}/{chapter}"
    local_path = f"{base_path}/{topic}_notes.pdf"
    notes_path = f"{clas}_{subject}_{chapter}_{topic}.pdf"

    if checkIfNotesExists(notes_path):
        return jsonify(notes_path), 200
    
    os.makedirs(base_path, exist_ok = True)
    notes = nai.generateNotes(clas, subject, chapter, topic, local_path)

    if not notes:
        pth = base_path+'/output.pdf'
        if not os.path.exists(pth):
            return 'internal error',500
        else:
            local_path = pth


    s3 = boto3.client('s3', aws_access_key_id = key, aws_secret_access_key = access_key)
    s3.upload_file(local_path, bucket_name, notes_path)

    return jsonify(notes_path), 200


if __name__=="__main__":
    app.run(debug = True, port = 8000, host = '0.0.0.0')


