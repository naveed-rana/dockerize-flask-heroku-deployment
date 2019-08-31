import os
import io
from flask import Flask, request
from google.oauth2 import service_account
from google.cloud import vision

credentials = service_account.Credentials.from_service_account_file('./autouploader-a34fa34e5fab.json')

app = Flask(__name__)


valuesText = ["Total", "Total Payable", "Net", "Net Amount", "Amount", "Total Bill", "Payable", "Bill", "Payment", "Total:"]
secondParam = ["Payable", "Amount", "Bill"]
nValues = ["Paid"]

def replaceCols(textValue):
    textValue = textValue.replace(":", "")
    textValue = textValue.replace(";", "")
    textValue = textValue.replace(".", "")
    return textValue


def detect_text(path):
    """Detects text in the file."""

    client = vision.ImageAnnotatorClient(credentials=credentials)
    # [START vision_python_migration_text_detection]
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    values = []
    for annotation in texts:
        verteces = []
        textValue = annotation.description.title()
        for vertex in annotation.bounding_poly.vertices:
                verteces.append([vertex.x, vertex.y])
        values.append([[verteces[0][0], verteces[1][1], verteces[2][0], verteces[3][1]], textValue])
    newVal = []
    for i, value in enumerate(values):
        textValue = value[1]
        textValue = replaceCols(textValue)
        if textValue.strip() in valuesText:
            cords = value[0]
            for val in values:
                ncords = val[0]
                diff = cords[1] - ncords[1]
                if diff < 0:
                    diff = -1 * diff
                if diff < 8:
                    if val[1] != value[1]:
                        nval = replaceCols(val[1])
                        if nval not in nValues:
                            if cords[0] < val[0][0]:
                                billVal = val[1]
                                billVal = billVal.replace("$", "")
                                billVal = billVal.replace(".", "")
                                if billVal.isdigit():
                                    newVal.append(val)
    print(newVal)
    if len(newVal) > 0:
        return newVal[0][1]
    else:
        return 0


@app.route("/get-receipt", methods=['POST','PUT'])
def receipt():
    file1 = request.files['filedata']
    # filename=werkzeug.utils.secure_filename(file1.filename)
    file1.save("new/current.jpg")
    imgPath = "new/current.jpg"
    val = detect_text(imgPath)
    return val


@app.route("/test")
def test():
    imgPath = "new/14.png"
    val = detect_text(imgPath)
    return val

@app.route('/')
def hello():
    return 'Receipt OCR App is working'

if __name__ == '__main__':
    app.run(host='0.0.0.0')
