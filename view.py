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
    if json_path != '-':
        with open(json_path) as f:
            ocr = json.load(f)
    
        block_score_sum=0
        line_count=0
        for block in ocr['blocks']:
            drawBox(img,block['box'],(0,0,255),5)
            t,l,b,r = block['box']
            h=b-t
            w=r-l
            squareness = min(0.4,h/w)
            area_whole = h*w
            area_covered = 0 #we'll assume lines don't overlap
            num_lines=0
            print('block {}'.format(block['box']))
            for para in block['paragraphs']:
                print('para {}'.format(para['box']))
                drawBox(img,para['box'],(0,255,0),3)
                for line in para['lines']:
                    print(line['text'])
                    drawBox(img,line['box'],(255,0,0),3)
                    num_lines+=1
                    for word in line['words']:
                        top,left,bottom,right = word['box']
                        height = bottom-top
                        width = right-left
                        area_covered+=height*width
                print('=====')
            if num_lines>1:
                area_score = area_covered/area_whole
            else:
                area_score = 0
            total_score = area_score+squareness
            block_score_sum += total_score*num_lines
            line_count += num_lines

        print('Block score: {}'.format(block_score_sum/line_count))
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
    if len(sys.argv)>2:
        skip = int(sys.argv[2])
    else:
        skip=0
    for root,dirs,files in os.walk(start_dir):
        for file_name in files:
            if file_name.endswith('.png'):
                print('[[[[[[[[[[[[[[[[[[[')
                print(file_name)
                print(']]]]]]]]]]]]]]]]]]]')
                if skip>0:
                    skip-=1
                else:
                    image_path = os.path.join(root,file_name)
                    json_path = os.path.join(root,file_name.replace('.png','.json'))
                    view(image_path,json_path)
