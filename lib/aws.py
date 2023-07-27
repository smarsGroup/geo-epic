import boto3
from utils import * 

class S3_Manager:
    def __init__(self) -> None:
        self.s3 = boto3.client('s3', region_name='us-east-1', 
            aws_access_key_id='AKIA3XDNLXQAYCFVE36A', 
            aws_secret_access_key='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')

        self.bucket = 'smarslab-files'
        self.prefix = 'nitrogen-recommendation-tool/epic-files/common-input-files'
    
    def upload_file(self, file_path, upload_folder):
        file_name = file_path.split('/')[-1]
        self.s3.upload_file(file_path, self.bucket, f'{self.prefix}/{upload_folder}/' + file_name)
    
    def download_file(self, folder, file):
        object_key = f'{self.prefix}/{folder}/{file}'
        self.s3.download_file(self.bucket, object_key, file)


