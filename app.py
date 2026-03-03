#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.storage_stack import StorageStack
from stacks.lambda_stack import LambdaStack

app = cdk.App()

storage = StorageStack(app, "StorageStack")
lambdas = LambdaStack(app, "LambdaStack",
    table=storage.table
)

app.synth()