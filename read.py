import pytesseract
from pytesseract import Output
from collections import defaultdict
import json, sys, os
PAGE_LEVEL=1
BLOCK_LEVEL=2
PARA_LEVEL=3
LINE_LEVEL=4
WORD_LEVEL=5

THRESHOLD=45

def addBlock(cur_block,blocks):
    if len(cur_block['paragraphs'])>0:
        blocks.append(cur_block)
        #print('add block {}'.format(cur_block['box']))
def addPara(cur_para,cur_block):
    if len(cur_para['lines'])>0:
        cur_block['paragraphs'].append(cur_para)
        #print('add para {}'.format(cur_para['box']))
def addLine(cur_line,cur_para):
    if len(cur_line['words'])>0:
        line_text=' '.join([w['text'] for w in cur_line['words']])
        cur_line['text']=line_text
        #print(line_text)
        cur_para['lines'].append(cur_line)

def doOCR(img,out_path):

    d = pytesseract.image_to_data(img, output_type=Output.DICT)

    keys=['level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']

    blocks=[]
    cur_block={'paragraphs':[]}
    cur_para={'lines':[]}
    cur_line={'words':[]}
    block_num=-1
    para_num=-1
    line_num=-1
    confs_sum=0
    confs_count=0
    for level,pg,blk,par,ln,wn,l,t,w,h,cnf,text in zip(*[d[k] for k in keys]):
        #print('{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}'.format(lev,pg,blk,par,ln,wn,l,t,w,h,cnf,text))
        assert pg==1

        l=int(l)
        t=int(t)
        w=int(w)
        h=int(h)
        bb = [l,t,l+w-1,t+h-1]
        if level==PAGE_LEVEL:
            assert l==0 and t==0
            image_h=h
            image_w=w
        elif level==BLOCK_LEVEL:
            addLine(cur_line,cur_para)
            cur_line={'box':bb, 'words':[]}
            addPara(cur_para,cur_block)
            cur_para={'box':bb, 'lines':[]}
            addBlock(cur_block,blocks)
            cur_block={'box':bb, 'paragraphs':[]}
            assert blk>block_num
            block_num=blk
            para_num=-1
        elif level==PARA_LEVEL:
            addLine(cur_line,cur_para)
            addPara(cur_para,cur_block)
            cur_para={'box':bb, 'lines':[]}
            assert par>para_num
            para_num=par
            line_num=-1
        elif level==LINE_LEVEL:
            addLine(cur_line,cur_para)
            cur_line={'box':bb, 'words':[]}
            assert ln>line_num
            line_num=ln
        
        
        if level==WORD_LEVEL: 
            confs_sum += cnf
            confs_count += 1
            text = text.strip()
            if int(cnf)>THRESHOLD and len(text)>0 and len(text.replace('-',''))>0: #confidence threshold, and more than just whitespace or line
                cur_line['words'].append({'box':bb, 'text':text})

    addLine(cur_line,cur_para)
    addPara(cur_para,cur_block)
    addBlock(cur_block,blocks)

            

    with open(out_path,'w') as f:
        json.dump({'height':image_h,'width':image_w,'blocks':blocks},f,indent=2)
    return confs_sum/confs_count if confs_count>0 else 0


start_dir=sys.argv[1]

for root,dirs,files in os.walk(start_dir):
    for file_name in files:
        if file_name.endswith('.png'):
            image_path = os.path.join(root,file_name)
            json_path = os.path.join(root,file_name.replace('.png','.ocr.json'))
            if not os.path.exists(json_path):
                conf=doOCR(image_path,json_path)
                #print('{} conf: {}'.format(file_name,conf))
                if conf<55: # we probably have a rotated image on our hands

                    #try rotating 90, 270, and 180
                    conf180=conf270=-1
                    os.system('convert {} -rotate 90 {}'.format(image_path,image_path+'.90.tmp'))
                    conf90=doOCR(image_path+'.90.tmp',json_path+'.90.tmp')
                    if conf90<80: #cut short if hight enough conf (speed)
                        os.system('convert {} -rotate 270 {}'.format(image_path,image_path+'.270.tmp'))
                        conf270=doOCR(image_path+'.270.tmp',json_path+'.270.tmp')
                        if conf270<80:
                            os.system('convert {} -rotate 180 {}'.format(image_path,image_path+'.180.tmp'))
                            conf180=doOCR(image_path+'.180.tmp',json_path+'.180.tmp')

                    #print('{} 90 conf: {}'.format(file_name,conf90))

                    best = max(conf,conf90,conf180,conf270) #select best rotation
                    #then move the tmp files to the permenats, (replace json and png)
                    if best==conf90:
                        os.system('mv {} {}'.format(json_path+'.90.tmp',json_path))
                        os.system('mv {} {}'.format(image_path+'.90.tmp',image_path))
                    elif best==conf180:
                        os.system('mv {} {}'.format(json_path+'.180.tmp',json_path))
                        os.system('mv {} {}'.format(image_path+'.180.tmp',image_path))
                    elif best==conf270:
                        os.system('mv {} {}'.format(json_path+'.270.tmp',json_path))
                        os.system('mv {} {}'.format(image_path+'.270.tmp',image_path))
                    ##print('do rm? not ({} and {} and {})'.format(best==conf90,conf180==-1 ,conf270==-1))
                    toremove=[]
                    if best!=conf90:
                        toremove+=[json_path+'.90.tmp',image_path+'.90.tmp']
                    if best!=conf180 and conf180!=-1:
                        toremove+=[json_path+'.180.tmp',image_path+'.180.tmp']
                    if best!=conf270 and conf270!=-1:
                        toremove+=[json_path+'.270.tmp',image_path+'.270.tmp']
                        
                    #    #print('rm {}/*tmp'.format(root))
                    #    os.system('rm {}'.format(os.path.join(root,'*tar'))) #clean up
                    for tr in toremove:
                         os.system('rm {}'.format(tr))


