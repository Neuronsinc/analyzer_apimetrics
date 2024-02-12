import boto3




#collection y api pueden ser variables para el constructor
class S3Manager:
    def __init__(self):
        self.b = boto3.resource('s3'
                , region_name='us-east-1'
                , aws_access_key_id='AKIA5DCHBSHBGAJ64FO2'
                , aws_secret_access_key='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')

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