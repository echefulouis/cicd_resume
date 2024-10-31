from aws_cdk import (
    # Duration,
    Stack,
    aws_s3,
    aws_cloudfront,
    aws_cloudfront_origins,
    aws_s3_deployment,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct
import os


class CicdResumeStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deployment_bucket = aws_s3.Bucket(self, "WebDeplBucket")

        ui_dir = os.path.join(os.path.dirname(__file__), "..", 'website')
        if not os.path.exists(ui_dir):
            print("Ui dir not found: " + ui_dir)
            return

        hosted_zone = route53.HostedZone.from_lookup(self, "HostedZone", domain_name="echefulouis.com")

        certificate = acm.DnsValidatedCertificate(
            self,
            "SiteCertificate",
            domain_name="echefulouis.com",
            hosted_zone=hosted_zone,
            region="us-east-1"  # Must be in us-east-1 for CloudFront
        )

        origin_identity = aws_cloudfront.OriginAccessIdentity(
            self, "PyOriginAccessIdentity"
        )
        deployment_bucket.grant_read(origin_identity)

        distribution = aws_cloudfront.Distribution(
            self,
            "PyWebDeploymentDistribution",
            default_root_object="index.html",
            domain_names=["echefulouis.com"],
            certificate=certificate,
            default_behavior=aws_cloudfront.BehaviorOptions(
                origin = aws_cloudfront_origins.S3Origin(
                    deployment_bucket, origin_access_identity=origin_identity
                )
            ),
        )
        aws_s3_deployment.BucketDeployment(self, "PyWebDeployment",
                                           destination_bucket=deployment_bucket,
                                           sources=[aws_s3_deployment.Source.asset(ui_dir)],
                                           distribution=distribution
                                           )

        CfnOutput(self, "PyAppUrl",
                  value=distribution.distribution_domain_name)
