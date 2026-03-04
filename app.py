#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.storage_stack import StorageStack
from stacks.compute_stack import ComputeStack

app = cdk.App()

storage = StorageStack(app, "StorageStack")
compute = ComputeStack(app, "ComputeStack",
    table=storage.table
)

app.synth()