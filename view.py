import img_f
import sys, json
import numpy as np
import os

def drawBox(img,bb,color,thickness):
    img_f.rectangle(img,bb[0:2],bb[2:],color,thickness=thickness)


def view(image_path,json_path):
    img = img_f.imread(image_path)
    if len(img.shape)==2:
        img = np.stack((img,img,img),axis=2)
    with open(json_path) as f:
        ocr = json.load(f)

    for block in ocr['blocks']:
        drawBox(img,block['box'],(0,0,255),5)
        print('block {}'.format(block['box']))
        for para in block['paragraphs']:
            print('para {}'.format(para['box']))
            drawBox(img,para['box'],(0,255,0),3)
            for line in para['lines']:
                print(line['text'])
                drawBox(img,line['box'],(255,0,0),3)
            print('=====')

    img_f.imshow('x',img)
    img_f.show()


image_path = sys.argv[1]
if image_path.endswith('.png'):
    image_path = sys.argv[1]
    if len(sys.argv)>2:
        json_path = sys.argv[2]
    else:
        json_path = image_path.replace('.png','.json')
    view(image_path,json_path)
else:
    start_dir = image_path
    for root,dirs,files in os.walk(start_dir):
        for file_name in files:
            if file_name.endswith('.png'):
                print('[[[[[[[[[[[[[[[[[[[')
                print(file_name)
                print(']]]]]]]]]]]]]]]]]]]')
                image_path = os.path.join(root,file_name)
                json_path = os.path.join(root,file_name.replace('.png','.json'))
                view(image_path,json_path)
