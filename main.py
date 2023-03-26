from flask import Flask, request
import cv2
import qrcode
import numpy as np
from deepface import DeepFace
import json
import requests
import os
from jsonrpcclient import request as req, parse, Ok
from flask_cors import CORS


app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

DB = {}

QN_ENDP = "https://falling-broken-glade.solana-devnet.discover.quiknode.pro/1c32aed1b5093f00f58b940bbccdc99391b867ea/"
NFTPORT_API = "de920a38-a922-42ac-a3da-c037d5fe76b3"


def write_db():
    global DB
    with open("db.json", "w") as outfile:
        json.dump(DB, outfile)


def read_db():
    global DB
    with open("db.json", "r") as outfile:
        DB = json.load(outfile)


@app.route("/")
def index():
    return "Hello from Flask!"


@app.route("/api/register", methods=["POST"])
def register():
    data = request.form

    name = data["name"]
    cogniid = data["cogni_id"]
    email = data["email"]
    address = data["address"]

    file = request.files["file"]
    file.save(cogniid + ".png")

    img = cv2.imread(cogniid + ".png")
    face_cascade = cv2.CascadeClassifier("face.xml")
    face_img = img.copy()
    face_rect = face_cascade.detectMultiScale(face_img, scaleFactor=1.2, minNeighbors=5)
    for x, y, w, h in face_rect:
        # cv2.rectangle(face_img, (x, y), (x + w, y + h), (255, 255, 255), 10)
        faces = img[y : y + h, x : x + w]
    cv2.imwrite(cogniid + ".cropped.png", faces)
    img = qrcode.make(cogniid)
    img.save(cogniid + ".qr.png")

    file = open(cogniid + ".cropped.png", "rb")
    fileqr = open(cogniid + ".qr.png", "rb")
    # file = open("image.png", "rb")

    response = requests.post(
        "https://api.nftport.xyz/v0/files",
        headers={"Authorization": NFTPORT_API},
        files={"file": file},
    )
    pid = response.json()["ipfs_url"].split("/")[-1]

    response2 = requests.post(
        "https://api.nftport.xyz/v0/files",
        headers={"Authorization": NFTPORT_API},
        files={"file": fileqr},
    )
    pidqr = response2.json()["ipfs_url"].split("/")[-1]

    DB[cogniid] = {
        "pid": pid,
        "pidqr": pidqr,
        "img_url": f"https://{pid}.ipfs.dweb.link/",
        "name": name,
        "email": email,
        "cogni_id": cogniid,
        "address": address,
    }

    metadata = {
        "name": "IIT Cognizance '23 Ticket",
        "description": "for " + name,
        "image": f"https://{pidqr}.ipfs.dweb.link/",
    }

    print(metadata)
    response = requests.post(
        "https://falling-broken-glade.solana-devnet.discover.quiknode.pro/1c32aed1b5093f00f58b940bbccdc99391b867ea/",
        json=req("cm_mintNFT", ["default-solana", "solana:" + address, metadata]),
    )
    print(response.text)

    # delete file
    os.remove(cogniid + ".png")
    os.remove(cogniid + ".cropped.png")
    os.remove(cogniid + ".qr.png")

    write_db()
    return "OK", 200


@app.route("/api/verify", methods=["POST"])
def verify():
    data = request.form

    cogniid = data["cogni_id"]

    verifier_img_path = cogniid + ".verify.png"
    if cogniid not in DB:
        return "Not Found", 404
    else:
        img_url = DB[cogniid]["img_url"]
        # save image from url
        r = requests.get(img_url, allow_redirects=True)
        open(verifier_img_path, "wb").write(r.content)

    file = request.files["file"]

    file.save(cogniid + ".cropped.png")
    img = cv2.imread(cogniid + ".cropped.png")
    face_cascade = cv2.CascadeClassifier("face.xml")
    face_img = img.copy()
    face_rect = face_cascade.detectMultiScale(face_img, scaleFactor=1.2, minNeighbors=5)
    for x, y, w, h in face_rect:
        # cv2.rectangle(face_img, (x, y), (x + w, y + h), (255, 255, 255), 10)
        faces = img[y : y + h, x : x + w]
    cv2.imwrite(cogniid + ".cropped.png", faces)

    obj = DeepFace.verify(faces, img2_path=verifier_img_path, enforce_detection=False)

    verified = 1 if obj["verified"] else 0

    os.remove(cogniid + ".png")
    os.remove(cogniid + ".cropped.png")
    os.remove(cogniid + ".verify.png")

    return {"verified": verified}, 200
    # return obj['verified'], "ok", 200


if __name__ == "__main__":
    read_db()
    app.run(port=8080, debug=True)
