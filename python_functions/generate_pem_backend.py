from __future__ import print_function
import boto3
import io
from crhelper import CfnResource
from aws_lambda_powertools import Logger

logger = Logger()
helper = CfnResource()

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
apigw_client = boto3.client('apigateway')


def upload_truststore_s3(trust_store: str, bucket_name: str, object_key: str)-> dict:
    s3_client.upload_fileobj(
        io.BytesIO(trust_store.encode('utf-8')),
        bucket_name,
        object_key
    )
    response_data= {
        "ObjectVersion": s3.Object(bucket_name,object_key).version_id,
        "TrustStoreUri": f"s3://{bucket_name}/{object_key}"
    }

    return response_data


def get_trust_store_location(event):
    resource_properties = event.get('ResourceProperties')
    trust_store_bucket = resource_properties.get('TrustStoreBucket')
    trust_store_object_key = resource_properties.get('TrustStoreKey')
    return trust_store_bucket, trust_store_object_key


@helper.create
@helper.update
def update_trust_store(event, context):
    """
    Creates the trust store in S3, by getting the public cert from API Gateway.
    """
    trust_store_bucket, trust_store_object_key = get_trust_store_location(event)
    client_certificate_id = event.get('ResourceProperties').get('ClientCertificateId')
    client_public_cert_pem = apigw_client.get_client_certificate(
        clientCertificateId=client_certificate_id
        )['pemEncodedCertificate']
    
    response = upload_truststore_s3(
        trust_store=client_public_cert_pem,
        bucket_name= trust_store_bucket,
        object_key = trust_store_object_key)

    helper.Data.update(response)

    return None

@helper.delete
def delete_trust_store(event, context):
    trust_store_bucket, trust_store_object_key = get_trust_store_location(event)
    s3_client.delete_object(
        Bucket=trust_store_bucket,
        Key=trust_store_object_key,
    )
    return None


@logger.inject_lambda_context
def main(event, context):
    logger.info({"event": event})
    logger.info({"context": context})    
    helper(event, context)
