import boto3
import io
import cfnresponse
from aws_lambda_powertools import Logger

logger = Logger()
s3 = boto3.resource('s3')
client = boto3.client('s3')

def cfn_response(event, context, response_data={}) -> None:
    cfnresponse.send(
        event=event,
        context=context, 
        responseStatus=cfnresponse.SUCCESS,
        responseData=response_data
    )

@logger.inject_lambda_context
def main(event, context):

    logger.info({"event": event})
    logger.info({"context": context})
    
    try:
        resource_properties = event.get('ResourceProperties')
        trust_store_bucket = resource_properties.get('TrustStoreBucket')
        trust_store_object_key = resource_properties.get('TrustStoreKey')
        concatenated_cert = "\n".join(resource_properties.get('Certs'))
        logger.info({"cert_data": concatenated_cert})

        client.upload_fileobj(
            io.BytesIO(concatenated_cert.encode('utf-8')),
            trust_store_bucket,
            trust_store_object_key
        )
        response_data= {
            "ObjectVersion": s3.Object(trust_store_bucket,trust_store_object_key).version_id,
            "TrustStoreUri": f"s3://{trust_store_bucket}/{trust_store_object_key}"
        }
    except:  # we really need to catch all exceptions, otherwise CF will stall for a looooong time
        logger.error("Unknown Error")
        response_data = {}

    cfn_response(event, context, response_data)

    return None