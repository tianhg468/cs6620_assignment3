from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigw,
)
from constructs import Construct


class ComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *,
                 table: dynamodb.Table, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket
        self.bucket = s3.Bucket(
            self, "TestBucket",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # Matplotlib layer (public ARN – us-east-1; change region if needed)
        matplotlib_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "MatplotlibLayer",
            layer_version_arn="arn:aws:lambda:us-west-1:130618649622:layer:matplotlib-layer-py312:1"
        )

        # --- Size-Tracking Lambda ---
        self.size_tracking_lambda = _lambda.Function(
            self, "SizeTrackingLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="size_tracking.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "TABLE_NAME": table.table_name,
                "BUCKET_NAME": self.bucket.bucket_name,
            },
        )

        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, s3n.LambdaDestination(self.size_tracking_lambda)
        )
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED, s3n.LambdaDestination(self.size_tracking_lambda)
        )

        self.bucket.grant_read(self.size_tracking_lambda)
        table.grant_write_data(self.size_tracking_lambda)

        # --- Plotting Lambda ---
        self.plotting_lambda = _lambda.Function(
            self, "PlottingLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="plotting.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            memory_size=256,
            layers=[matplotlib_layer],
            environment={
                "TABLE_NAME": table.table_name,
                "BUCKET_NAME": self.bucket.bucket_name,
                "SIZE_INDEX_NAME": "size-index",
            },
        )

        table.grant_read_data(self.plotting_lambda)
        self.bucket.grant_write(self.plotting_lambda)

        # --- REST API for Plotting Lambda ---
        api = apigw.RestApi(
            self, "PlottingApi",
            rest_api_name="PlottingService",
        )

        plot_resource = api.root.add_resource("plot")
        plot_resource.add_method(
            "GET",
            apigw.LambdaIntegration(self.plotting_lambda),
        )

        api_url = api.url_for_path("/plot")

        CfnOutput(self, "ApiEndpoint", value=api_url)

        # --- Driver Lambda ---
        self.driver_lambda = _lambda.Function(
            self, "DriverLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="driver.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(60),
            environment={
                "BUCKET_NAME": self.bucket.bucket_name,
                "API_URL": api_url,
            },
        )

        self.bucket.grant_write(self.driver_lambda)