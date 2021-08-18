import json, sys, os

start_dir=sys.argv[1]
dest_dir=sys.argv[2]

for root,dirs,files in os.walk(start_dir):
    #print(root) full path
    for file_name in files:
        if file_name.endswith('.tif'):
            new_file_name = file_name.replace('.tif','.png')
            os.system('convert {} {}'.format(os.path.join(root,file_name),os.path.join(dest_dir,new_file_name)))
