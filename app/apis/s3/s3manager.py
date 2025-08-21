import os
import boto3

from dotenv import load_dotenv

load_dotenv("app\.env", override=False)
AWS_KEY = os.environ.get("AWS_KEY")
AWS_SECRET = os.environ.get("AWS_SECRET")


#collection y api pueden ser variables para el constructor
class S3Manager:
    def __init__(self):
        self.b = boto3.resource('s3'
                , region_name='us-east-1'
                , aws_access_key_id=AWS_KEY
                , aws_secret_access_key=AWS_SECRET)

        self.bucket = self.b.Bucket('geotec-dev')


    def s3_list_files(self, collection: str):
        filters = lambda f: (f'dataset/Stimuli/{collection}' in f) & (f'maps' not in f)
        l = filter(lambda l : filters(l.key) , self.bucket.objects.all())
        return list(l)


    def s3_save_object(self, collection: str, api:str, name: str, filename:str, file):
        try:
            object_location = f'dataset/Stimuli/{collection}/{name}_{api}_maps/{filename}'
            print(f'en esta localizacion {object_location}')
            self.b.Object('geotec-dev', object_location).put(Body=file)
            print(f'se subio')
        except Exception as ex:
            print('se murio en el envio al s3')
            raise ex