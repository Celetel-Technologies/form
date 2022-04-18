import boto3


def conn(settings):
    resource = boto3.resource(
        'dynamodb',
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_default_region
    )

    return resource
