import pytesseract
from pytesseract import Output
from collections import defaultdict
import json, sys, os, time
from multiprocessing import Pool, TimeoutError
import subprocess
import img_f
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

def doOCR(img,out_path,Rotation=0):

    try:
        d = pytesseract.image_to_data(img, output_type=Output.DICT)
    except pytesseract.pytesseract.TesseractError as e:
        print('Tesseract failed to read: {}'.format(img))
        print(e)
        if not img.endswith('tmp'):
            #re-convert
            #~/compute/outA/A.B/A.B.C/image.png
            #~/compute/imagesA/A/B/C/map.csv
            _,orig_file_name = os.path.split(img)
            dash = orig_file_name.rfind('-')
            if dash>-1 and len(orig_file_name)-dash<9:
                id_file_name=orig_file_name[:dash]
                try:
                    page_num = int(orig_file_name[dash+1:-4])
                except ValueError:
                    dash = -1
                    id_file_name=orig_file_name[:-4]
                    page_num=0
            else:
                id_file_name=orig_file_name[:-4] #remove '.png'
                page_num=0
            A,B,C = img.split('/')[-2].split('.')
            map_file = os.path.join('..','compute','images{}'.format(A),A,B,C,'new_map.csv')
            #os.system('mkdir tmp{}{}{}'.format(A,B,C))
            with open(map_file) as f:
                lines = f.readlines()
            for line in  lines:
                file_name,path = line.split(',')
                if file_name == id_file_name:
                    break
            if file_name != id_file_name:
                #bad dash thing?
                if dash<=-1:
                    print('not dash issue? "{}" vs "{}"'.format(file_name,id_file_name))
                    print('not dash issue? "{}" vs "{}"'.format(file_name,id_file_name),file=sys.stderr)
                    with open('debug.log','a+') as f:
                        f.write('not dash issue? "{}" vs "{}"\n'.format(file_name,id_file_name))
                assert dash>-1
                if len(orig_file_name)-dash<9:
                    #read page num when we shou;dn't have
                    id_file_name=orig_file_name[:4]
                    page_num=0
                else:
                    #didn't read page num when we should have (1000 pages????)
                    id_file_name=orig_file_name[:dash]
                    page_num = int(orig_file_name[dash+1:-4])
                for line in  lines:
                    file_name,path = line.strip().split(',')
                    if file_name == id_file_name:
                        break
            assert file_name == id_file_name
            print('convert {}[{}] {}'.format(path.strip(),page_num,img))
            os.system('convert {}[{}] {}'.format(path.strip(),page_num,img)) #only convert with this page
            #os.system('convert {} tmp{}{}{}/{}.png'.format(path,A,B,C,if_file_name))
            #os.system('mv tmp{}{}{}/{} img'.format(A,B,C,orig_file_name,img))
            #os.system('rm -r tmp{}{}{}'.format(A,B,C))

        elif img.endswith('.90.tmp'):
            os.system('convert {} -rotate 90 {}'.format(img[:-7],img))
        elif img.endswith('.180.tmp'):
            os.system('convert {} -rotate 180 {}'.format(img[:-8],img))
        elif img.endswith('.270.tmp'):
            os.system('convert {} -rotate 270 {}'.format(img[:-8],img))
        try: 
            d = pytesseract.image_to_data(img, output_type=Output.DICT)
        except pytesseract.pytesseract.TesseractError as e:
            print('Tesseract failed to read a SECOND TIME: {}'.format(img))
            print(e)
            return 0, 0

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
    w_to_h_sum=0
    line_word_count = defaultdict(int)
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
            if len(text.replace('-','').replace(' ',''))>0:
                confs_sum += cnf
                confs_count += 1
                text = text.strip()
                w_to_h_sum += w/h if h>0 else w
                #print(text,cnf)
            if (int(cnf)>THRESHOLD or line_word_count[ln]>1) and len(text)>0 and len(text.replace('-','').replace(' ',''))>0: #confidence threshold, and more than just whitespace or line
                cur_line['words'].append({'box':bb, 'text':text})
                line_word_count[ln]+=1

    addLine(cur_line,cur_para)
    addPara(cur_para,cur_block)
    addBlock(cur_block,blocks)

            
    try:
        with open(out_path,'w') as f:
            json.dump({
                'height':image_h,
                'width':image_w,
                'blocks':blocks,
                'mean_conf': confs_sum/confs_count if confs_count>0 else 0,
                'rotation': Rotation
                },f,indent=2)
    except OSError:
        time.sleep(3)
        with open(out_path,'w') as f:
            json.dump({
                'height':image_h,
                'width':image_w,
                'blocks':blocks,
                'mean_conf': confs_sum/confs_count if confs_count>0 else 0,
                'rotation': Rotation
                },f,indent=2)
    #print((confs_sum/confs_count, w_to_h_sum/confs_count) if confs_count>0 else (0,None))
    return (confs_sum/confs_count, w_to_h_sum/confs_count) if confs_count>0 else (0,0.1)

def doFull(x):
    MAIN_THRESH=55
    image_path,json_path=x
    if os.path.exists(json_path):
        #check if it has score
        with open(json_path) as f:
            try:
                done_ocr = json.load(f)
            except json.decoder.JSONDecodeError:
                done_ocr = {}
            if 'mean_conf' in done_ocr:
                #is the score high enough
                if done_ocr['mean_conf']>=MAIN_THRESH:
                    #does ocr match image rotation?
                    oheight = done_ocr['height']
                    owidth = done_ocr['width']
                    #get PNG dimensions using less (easy read to header info)
                    res = subprocess.run(['less',image_path], stdout=subprocess.PIPE)
                    try:
                        res = res.stdout.decode("utf-8").split(' ')[2].split('x')
                        iheight = int(res[1])
                        iwidth = int(res[0])
                    except IndexError:
                        print('PNG header read failed for {}  :  {}'.format(image_path,res))
                        iimg = img_f.imread(image_path)
                        iheight = iimg.shape[0]
                        iwidth = iimg.shape[1]
                    if iheight==oheight and iwidth==owidth:
                        #now see it this is an image needing rotated
                        word_height = 0
                        word_width = 0
                        #word_count = 1
                        for block in done_ocr['blocks']:
                            for para in block['paragraphs']:
                                for line in para['lines']:
                                    for word in line['words']:
                                        l,t,r,b = word['box']
                                        word_height += b-t
                                        word_width += r-l
                                        #word_count +=1
                        w_to_h = word_width/word_height if word_height>0 else -1
                        if w_to_h>=1:
                            #this ocr file is fine
                            #print('pass on {}'.format(image_path))
                            return done_ocr['mean_conf']
    #print('doing {}'.format(image_path))

    conf,w_to_h=doOCR(image_path,json_path)
    #print('{} conf: {}'.format(file_name,conf))
    if conf<80 or w_to_h<1: # we probably have a rotated image on our hands

        #try rotating 90, 270, and 180
        conf180=conf270=-1
        w_to_h90=.1
        w_to_h180=.1
        w_to_h270=.1
        os.system('convert {} -rotate 90 {}'.format(image_path,image_path+'.90.tmp'))
        if not os.path.exists(image_path+'.90.tmp'):
            os.system('convert {} -rotate 90 {}'.format(image_path,image_path+'.90.tmp'))
        assert os.path.exists(image_path+'.90.tmp')
        conf90,w_to_h90=doOCR(image_path+'.90.tmp',json_path+'.90.tmp',90)
        assert os.path.exists(json_path+'.90.tmp')
        if conf90<80 or w_to_h90<1: #cut short if hight enough conf (speed)
            os.system('convert {} -rotate 270 {}'.format(image_path,image_path+'.270.tmp'))
            assert os.path.exists(image_path+'.270.tmp')
            conf270,w_to_h270=doOCR(image_path+'.270.tmp',json_path+'.270.tmp',270)
            assert os.path.exists(json_path+'.270.tmp')
            if conf270<80 or w_to_h270<1:
                os.system('convert {} -rotate 180 {}'.format(image_path,image_path+'.180.tmp'))
                assert os.path.exists(image_path+'.180.tmp')
                conf180,w_to_h180=doOCR(image_path+'.180.tmp',json_path+'.180.tmp',180)
                assert os.path.exists(json_path+'.180.tmp')

        #print('{} 90 conf: {}'.format(file_name,conf90))

        conf *= min(1,w_to_h)
        conf90 *= min(1,w_to_h90)
        conf180 *= min(1,w_to_h180)
        conf270 *= min(1,w_to_h270)

        best = max(conf,conf90,conf180,conf270) #select best rotation
        #then move the tmp files to the permenats, (replace json and png)
        if best<MAIN_THRESH: #remove low confidence images (also no words)
            os.system('rm {}'.format(image_path))
            os.system('rm {}'.format(json_path))
            best=-1

        elif best==conf90:
            assert os.path.exists(json_path+'.90.tmp')
            assert os.path.exists(image_path+'.90.tmp')
            os.system('mv {} {}'.format(json_path+'.90.tmp',json_path))
            os.system('mv {} {}'.format(image_path+'.90.tmp',image_path))
        elif best==conf180:
            assert os.path.exists(json_path+'.180.tmp')
            assert os.path.exists(image_path+'.180.tmp')
            os.system('mv {} {}'.format(json_path+'.180.tmp',json_path))
            os.system('mv {} {}'.format(image_path+'.180.tmp',image_path))
        elif best==conf270:
            assert os.path.exists(json_path+'.270.tmp')
            assert os.path.exists(image_path+'.270.tmp')
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
        conf=best

    return conf



start_dir=sys.argv[1]
if start_dir.endswith('.png'):
    json_path = sys.argv[2]
    score,w2h = doOCR(start_dir,json_path)
    print(score)
else:
    if len(sys.argv)>2:
        N = int(sys.argv[2])
    else:
        N=20

    todo=[]
    for root,dirs,files in os.walk(start_dir):
        for file_name in files:
            if file_name.endswith('.png'):
                image_path = os.path.join(root,file_name)
                json_path = os.path.join(root,file_name.replace('.png','.ocr.json'))
                #if not os.path.exists(json_path):
                todo.append((image_path,json_path))

    pool = Pool(processes=N)
    chunk = 5
    created = pool.imap_unordered(doFull, todo, chunksize=chunk)
    for score in created:
        pass
