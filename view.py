import img_f
import sys, json
import numpy as np

def drawBox(img,bb,color,thickness):
    img_f.rectangle(img,bb[0:2],bb[2:],color,thickness=thickness)

if len(sys.argv)>1:
    name = sys.argv[1]
else:
    name = 'test'


img = img_f.imread(name+'.png')
if len(img.shape)==2:
    img = np.stack((img,img,img),axis=2)
with open(name+'.json') as f:
    ocr = json.load(f)

for block in ocr['blocks']:
    drawBox(img,block['box'],(0,0,255),4)
    print('block {}'.format(block['box']))
    for para in block['paragraphs']:
        print('para {}'.format(para['box']))
        drawBox(img,para['box'],(0,255,0),2)
        for line in para['lines']:
            print(line['text'])
        #    drawBox(img,line['box'],(255,0,0),2)
        print('=====')

img_f.imshow('x',img)
img_f.show()
