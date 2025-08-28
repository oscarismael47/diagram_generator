from diagrams import Diagram
from diagrams import Cluster
from diagrams.aws.network import Route53, ELB, VPC, PrivateSubnet, PublicSubnet, NATGateway, InternetGateway
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import RDS, Dynamodb
from diagrams.aws.storage import S3
from diagrams.aws.analytics import Kinesis
from diagrams.aws.security import WAF, IAM
from diagrams.aws.management import Cloudwatch
from diagrams.aws.integration import SQS
graph_attr = {
    "bgcolor": "gray89",
    "margin":"-1.5, -2"
}

filename = "diagram_image"
with Diagram("Diagram", show=False,  filename=filename, outformat="png", graph_attr=graph_attr):
    route53 = Route53("Route53")
    waf = WAF("WAF")
    vpc = VPC("VPC")

    with vpc:
        igw = InternetGateway("Internet Gateway")
        nat = NATGateway("NAT Gateway")
        with PublicSubnet("Public Subnet"):
            alb = ELB("Application Load Balancer")
            ec2_public = EC2("Public EC2")
        with PrivateSubnet("Private Subnet"):
            ec2_private = EC2("Private EC2 1")
            ec2_private_2 = EC2("Private EC2 2")
            rds = RDS("RDS DB")
            dynamodb = Dynamodb("DynamoDB")

    lambda_func = Lambda("Lambda")
    s3 = S3("S3 Bucket")
    sqs = SQS("SQS Queue")
    kinesis = Kinesis("Kinesis Stream")
    iam = IAM("IAM")
    cloudwatch = Cloudwatch("CloudWatch")

    route53 >> waf >> alb >> ec2_public
    alb >> [ec2_private, ec2_private_2]
    ec2_private >> rds
    ec2_private_2 >> dynamodb
    lambda_func >> s3
    lambda_func >> sqs
    sqs >> lambda_func
    kinesis >> lambda_func
    iam >> [ec2_public, ec2_private, lambda_func]
    cloudwatch >> [ec2_public, ec2_private, rds, lambda_func]