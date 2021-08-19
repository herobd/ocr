import layoutparser as lp
import img_f
import numpy as np
import sys, json, os
from collections import defaultdict

model1 = lp.Detectron2LayoutModel(
    'models/PubLayNet.yaml',
    'models/PubLayNet.pth',
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
    label_map={0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"},
    enforce_cpu=False)
model2 = lp.Detectron2LayoutModel(#'lp://PrimaLayout/mask_rcnn_R_50_FPN_3x/config',
    'models/PrimaLayout.yaml',
    'models/PrimaLayout.pth',
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
    label_map={1:"TextRegion", 2:"ImageRegion", 3:"TableRegion", 4:"MathsRegion", 5:"SeparatorRegion", 6:"OtherRegion"},
    enforce_cpu=False)


def computeIOU(bb1,bb2):
    a1 = (bb1[2]-bb1[0])*(bb1[3]-bb1[1])
    a2 = (bb2[2]-bb2[0])*(bb2[3]-bb2[1])
    w = -max(bb1[0],bb2[0])+min(bb1[2],bb2[2])
    if w<=0:
        return 0
    h = -max(bb1[1],bb2[1])+min(bb1[3],bb2[3])
    if h<=0:
        return 0
    i=h*w
    return i/(a1+a2-i)

def computeCovered(bb,bybb):
    a = (bb[2]-bb[0])*(bb[3]-bb[1])
    w = -max(bb[0],bybb[0])+min(bb[2],bybb[2])
    if w<=0:
        return 0
    h = -max(bb[1],bybb[1])+min(bb[3],bybb[3])
    if h<=0:
        return 0
    i=h*w
    return i/a


def redoLayout(image_path,draw=False,save=True):
    json_path = image_path.replace('.png','.ocr.json')
    out_path = image_path.replace('.png','.json')

    if os.path.exists(out_path):
        return

    image = img_f.imread(image_path)
    if draw:
        orig_image = image
    width = image.shape[1]
    scale = 600/width
    image = img_f.resize(image,fx=scale,fy=scale,dim=[0,0]).astype(np.uint8)
    if len(image.shape)==2:
        image = np.stack((image,image,image),axis=2)



    layout = model1.detect(image)
    primary_boxes=[]
    for thing in layout:
        x1 = thing.block.x_1
        y1 = thing.block.y_1
        x2 = thing.block.x_2
        y2 = thing.block.y_2
        #img_f.rectangle(image,(x1,y1),(x2,y2),color,2)
        primary_boxes.append((x1,y1,x2,y2))


    layout = model2.detect(image)
    secondary_boxes=[]
    for thing in layout:
        x1 = thing.block.x_1
        y1 = thing.block.y_1
        x2 = thing.block.x_2
        y2 = thing.block.y_2

        #overlap=False
        #remove=[]
        #for i,bb in enumerate(primary_boxes):
        #    iou = computeIOU((x1,y1,x2,y2),bb)
        #    if iou>0.2:
        #        if (x2-x1)*(y2-y1) > (bb[2]-bb[0])*(bb[3]-bb[1]):
        #            remove.append(i)
        #        else:
        #            overlap=True
        #            break
        ##img_f.rectangle(image,(x1,y1),(x2,y2),color,2)
        #if not overlap:
        secondary_boxes.append((x1,y1,x2,y2))
        #    remove.reverse()
            #for r in remove:
            #    del primary_boxes[r]

    boxes = primary_boxes+secondary_boxes
    boxes = np.array(boxes)
    boxes/=scale
    boxes = boxes.tolist()

    with open(json_path) as f:
        ocr = json.load(f)

    remove_boxes=[]
    ocr_lines = []
    for block in ocr['blocks']:
        boxes.append(block['box'])
        for para in block['paragraphs']:
            ocr_lines += para['lines']

        #for i,bb in enumerate(boxes):
        #    iou = computeIOU(block['box'],bb)
        #    if iou>0.2:
        #        x1,y1,x2,y2 = block['box']
        #        if (x2-x1)*(y2-y1) > (bb[2]-bb[0])*(bb[3]-bb[1]):
        #            remove_boxes.append(i)
        #        else:
        #            overlap=True
        #            break
        #if not overlap:
        #    remove.reverse()
        #    #for r in remove:
        #    #    del boxes[r]
        #    boxes.append(block['box'])

    boxes.sort(key=lambda bb:(bb[2]-bb[0])*(bb[3]-bb[1]), reverse=True)

    block_votes = defaultdict(int)
    for line in ocr_lines:
        added=False
        for i,bb in enumerate(boxes):
            covered = computeCovered(line['box'],bb)
            if covered>0.3:
                block_votes[i]+=1

    new_blocks = defaultdict(list)
    unadded=[]
    for line in ocr_lines:
        added=False
        #print(line['text'])
        best=-1
        best_votes=-1
        for i,bb in enumerate(boxes):
            covered = computeCovered(line['box'],bb)
            #print('{} c {} : {}'.format(line['box'],bb,covered))
            if covered>0.3:
                #new_blocks[i].append(line)
                #added=True
                #break
                if best_votes<block_votes[i]:
                    best_votes = block_votes[i]
                    best=i
        if best_votes==-1:
            
            #print('---not added')
            unadded.append(line)
        else:
            new_blocks[best].append(line)

    #assert len(unadded)==0
    if len(unadded)>0:
        print('{} had {} unadded'.format(image_path,len(unadded)))
    i=len(boxes)+1000
    for line in unadded:
        new_blocks[i].append(line)
        i+=1
    #import pdb;pdb.set_trace()
    if draw:
        image = orig_image
        if len(image.shape)==2:
            image = np.stack((image,image,image),axis=2)
        for i,bb in enumerate(boxes):
            x1,y1,x2,y2 = bb
            if i < len(primary_boxes):
                color = (0,255,0)
            elif i < len(secondary_boxes)+len(primary_boxes):
                color = (0,255,255)
            else:
                color = (255,255,0)
            img_f.rectangle(image,(x1,y1),(x2,y2),color,5)

    blocks=[]
    for lines in new_blocks.values():
        min_x,min_y,max_x,max_y = lines[0]['box']
        for line in lines[1:]:
            x1,y1,x2,y2 = line['box']
            min_x = min(min_x,x1)
            max_x = max(max_x,x2)
            min_y = min(min_y,y1)
            max_y = max(max_y,y2)
        if draw:
            img_f.rectangle(image,(min_x,min_y),(max_x,max_y),(0,0,255),5)

        blocks.append({
            'box':(min_x,min_y,max_x,max_y),
            'paragraphs':[{
                'box':(min_x,min_y,max_x,max_y),
                'lines':lines
                }]
            })
    ocr['blocks']=blocks
    if save:
        with open(out_path,'w') as f:
            json.dump(ocr,f,indent=2)

    #for line in unadded:
    #    x1,y1,x2,y2 = line['box']
    #    img_f.rectangle(image,(x1,y1),(x2,y2),(255,0,0),5)


    if draw:
        img_f.imshow('x',image)
        img_f.show()
######

start_dir=sys.argv[1]

if start_dir.endswith('.png'):
    redoLayout(start_dir,draw=True,save=False)
else:
    for root,dirs,files in os.walk(start_dir):
        for file_name in files:
            if file_name.endswith('.png'):
                image_path = os.path.join(root,file_name)
                redoLayout(image_path)
