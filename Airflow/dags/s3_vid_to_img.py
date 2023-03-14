### DAG um videos von S3 Speicher zu laden und in Bilder aller 60fps zu speichern ###

from datetime import datetime
from airflow import DAG
from airflow.decorators import task

import boto3
from PIL import Image 
import cv2
import time
import os
from os.path import exists
from botocore.client import Config
import requests
import json
import hashlib

# Create client with access key and secret key with specific region.


s3_load = boto3.resource('s3',
                    #endpoint_url='http://10.151.246.229:9000',
                    aws_access_key_id='',
                    aws_secret_access_key='',
                    verify= False,
                    #config=Config(signature_version='s3v4'),
                    region_name='eu-central-1'
                     )
s3_write = boto3.client('s3',
                    #endpoint_url='http://10.151.246.229:9000',
                    aws_access_key_id='',
                    aws_secret_access_key='',
                    verify= False,
                    #config=Config(signature_version='s3v4'),
                    region_name='eu-central-1'
                     )

#def first_5chars(x):
#    return(x[0:5])

#def sort():
#    sorted(output_loc, key = first_5chars)

with DAG("s3_s3_manifest", # Dag id
    start_date=datetime(2021, 1 ,1), # start date, the 1st of January 2021 
    schedule_interval='@yearly',  # Cron expression, here it is a preset of Airflow, @daily means once every day.
    #catchup=False, # Catchup
) as dag:
    

    @task
    def load_from_storage():
        object_to_load = []
        #for bucket in s3_load.buckets.all():
        bucket_name = 'bucket_name' # setzte Bucket Name ein
        print('Bucket name: {}'.format(bucket_name))
        my_bucket = s3_load.Bucket(format(bucket_name))
        for my_bucket_object in my_bucket.objects.filter(Prefix='raw/video/2022.08.25'):
            if my_bucket_object.key.endswith(".MOV") or my_bucket_object.key.endswith(".MP4"):
                print(my_bucket_object.key)
                object_to_load.append(my_bucket_object.key)
        return object_to_load


    @task.virtualenv(
        task_id="convert_video_to_image", system_site_packages=True
    )
    #requirements=["boto3 Pillow opencv-python"]
    def video_to_frames(s3_objects):  
        import boto3
        from PIL import Image 
        import cv2
        import time
        import os
        from os.path import exists
        from botocore.client import Config
        import requests
        import hashlib
        import json
        
        manifest_entries = []
        
        s3_load = boto3.resource('s3',
                    #endpoint_url='http://10.151.246.229:9000',
                    aws_access_key_id='',
                    aws_secret_access_key='',
                    verify= False,
                    #config=Config(signature_version='s3v4'),
                    region_name='eu-central-1'
                     )
        s3_write = boto3.client('s3',
                    #endpoint_url='http://10.151.246.229:9000',
                    aws_access_key_id='',
                    aws_secret_access_key='',
                    verify= False,
                    #config=Config(signature_version='s3v4'),
                    region_name='eu-central-1'
                     )
        
        #exrect filename for temp path
        filename = s3_objects.split("/",-1)[-1][:-4]
        filepath = s3_objects
        tempfilename = s3_objects.split("/",-1)[-1]
        pwd = os.getcwd()
        temp_path = pwd + '/data/dataset/video/' + filename + '/' + tempfilename
        temp_video = pwd + '/data/dataset/video/' + filename
        temp_image = pwd + '/data/dataset/video/' + filename + '/temp'
        
        entry = {"version":"1.0"}
        manifest_entries.append(entry)
        entry = {"type":"images"}
        manifest_entries.append(entry)
        
        #for bucket in s3_load.buckets.all():
        #    bucket_name = bucket.name
        s3_bucket_name = 'hslu-dolphin'
        
        try:
            os.mkdir(temp_video)
            print('Erstelle: ' + temp_video)
        except OSError:
            print('Fehler beim erstellen des Ordnes' + temp_video)
            pass
        try:
            os.mkdir(temp_image)
            print('Erstelle: ' + temp_image)
        except OSError:
            print('Fehler beim erstellen des Ordnes' + temp_image)
            pass
        
        if exists(temp_path):
            print('file ' + temp_path + ' exist, skip download')
        else:
        #download video to temp path
            print('download: ' + filepath)
            s3_write.download_file(s3_bucket_name, s3_objects, temp_path)
        # Log the time
        time_start = time.time()
        # Start capturing the feed
        cap = cv2.VideoCapture(temp_path)
        # Find the number of frames
        video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        print ("Number of frames: ", video_length)
        count = 0
        print ("Converting video..\n")
        # Start converting the video
        while cap.isOpened():
            # Extract the frame
            ret, frame = cap.read()
            frame = cv2.resize(frame, (1280, 720), Image.LANCZOS) # resize
            if not ret:
                continue
            path_to_tempimage = temp_image + "/%#05d.jpg" % (count)
            # save image to buffer
            #buffer = cv2.imencode('.jpg', frame)
            cv2.imwrite(path_to_tempimage, frame)
            
            #manifest für cvat
            #checksum = hashlib.md5(open(path_to_tempimage, 'rb').read()).hexdigest()
            with open(path_to_tempimage, 'rb') as f:
                checksum = hashlib.md5(f.read()).hexdigest()
            
            # write buffer to s3 imagefile
            #Bucket=my_bucket, Key = 'resize/images/' + filename + (filename +"%#05d.jpg" % (count))
            #Key = 'resize/images/' + filename + (filename +"%#05d.jpg" % (count))
            Key = 'processed/images/' + filename + '/' + filename +"%#05d.jpg" % (count)
            #path_to_tempimage = temp_image + "/%#05d.jpg" % (count)
            entry = {
                "name": Key,
                "extension":".jpg",
                "width":1280,
                "higth":720,
                "meta":{"related_images":[]},
                "checksum":checksum,
            }
            
            #client_write.put_object(Bucket=my_bucket, Key = 'resize/images/' + filename + (filename +"%#05d.jpg" % (count)), Body = io.BytesIO(buffer).read(), ContentType= 'image/jpeg')
            s3_write.upload_file(path_to_tempimage, s3_bucket_name, Key)#, ContentType= 'image/jpeg')
            #erstelle manifest datei für cvat
            manifest_entries.append(entry)
            try :
                os.remove(Key)
            except OSError:
                pass
            #print(bytes(frame))
            # set framecount 
            count = count + 60
            cap.set(cv2.CAP_PROP_POS_FRAMES, count) # springe x frames weiter
            # If there are no more frames left
            if (count > (video_length-1)):
                # Log the time again
                time_end = time.time()
                # Release the feed
                cap.release()
                # Print stats
                print ("Done extracting frames.\n%d frames extracted" % count)
                print ("It took %d seconds forconversion." % (time_end-time_start))
                break

        try :
            os.remove(temp_path)
        except OSError:
            pass
        with open(filename + '.jsonl', 'w') as f:
            for item in manifest_entries:
                f.write(json.dumps("%s" % item, indent=2))
        s3_write.upload_file(filename + '.jsonl', s3_bucket_name, 'manifest/' + filename + '.jsonl')
        print("Manifest erstellt und in S3 gespeichert")
            
    #filenames = load_minio(filenames = name_list)
    #video_to_frames.expand(filenames)
    
    video_to_frames.partial().expand(s3_objects=load_from_storage())
