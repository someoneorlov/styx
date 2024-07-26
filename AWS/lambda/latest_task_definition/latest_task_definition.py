import boto3


def lambda_handler(event, context):
    ecs_client = boto3.client("ecs")
    task_def_name = event["task_def_name"]

    response = ecs_client.describe_task_definition(taskDefinition=task_def_name)

    latest_revision = response["taskDefinition"]["taskDefinitionArn"]

    return {"latest_revision": latest_revision}
