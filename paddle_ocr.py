import json

import requests
from PIL import Image
import base64
import io

ocr_result = ''

def img_to_base64(img_path):
    img = Image.open(img_path)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes = img_bytes.getvalue()
    img_b64 = base64.b64encode(img_bytes)
    return img_b64.decode('utf-8')


def ocr(file_path):
    global ocr_result
    img_b64 = img_to_base64(file_path)
    headers = {
        # Already added when you pass json=
        'Content-Type': 'application/json',
    }

    json_data = {
        'images': [
            img_b64
        ],
    }

    response = requests.post('http://127.0.0.1:19000/predict/ocr_system',
                             headers=headers, json=json_data)
    results = json.loads(response.text)  # 是你要处理的原始数据
    texts = []
    for result in results['results']:
        text = [item['text'] for item in result]
        texts.append(text)
    flattened_list = [item for sublist in texts for item in sublist]
    ocr_result = ' '.join(flattened_list)
    return response.text, texts

if __name__ == '__main__':
    img_path = "WechatIMG44.jpg"

