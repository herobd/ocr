import json, sys, os

start_dir=sys.argv[1]
dest_dir=sys.argv[2]

with open(os.path.join(start_dir,'map.csv'), 'a+') as map_file:

    for root,dirs,files in os.walk(start_dir):
        #print(root) full path
        for file_name in files:
            if file_name.endswith('.tif'):
                id_file_name = file_name.replace('.tif','')
                new_file_name = file_name.replace('.tif','.png')
                check_file_name = file_name.replace('.tif','-0.png')
                new_file_name = os.path.join(dest_dir,new_file_name)
                check_file_name = os.path.join(dest_dir,check_file_name)
                if not os.path.exists(new_file_name) and not os.path.exists(check_file_name):
                    #don't want to replace rotated image
                    os.system('convert {} {}'.format(os.path.join(root,file_name),new_file_name))
                    map_file.write('{},{}\n'.format(id_file_name,os.path.join(root,file_name)))
