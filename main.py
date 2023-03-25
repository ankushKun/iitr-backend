from flask import Flask, request
import cv2
import qrcode
import numpy as np
from deepface import DeepFace
app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello from Flask!'
  
@app.route('/api/regiter', methods=["POST"])
def acc_reg():
    data  = request.get_json(force=True)
    cogniid = data['cogni_id']
    email = data['email']
    file = request.files['image']
    file.save(cogniid+'.png')
    img=cv2.imread(cogniid+'.png')
    face_cascade = cv2.CascadeClassifier('face.xml')
    face_img = img.copy()
    face_rect = face_cascade.detectMultiScale(face_img,scaleFactor = 1.2,minNeighbors = 5)
    for (x, y, w, h) in face_rect:
        cv2.rectangle(face_img, (x, y),(x + w, y + h), (255, 255, 255), 10)
        faces = img[y:y + h, x:x + w]
    cv2.imwrite(cogniid+'.png', faces)
    img = qrcode.make(cogniid)
    img.save(cogniid+email+".png")  
    return "ok",200


app.run(host='0.0.0.0', port=81)