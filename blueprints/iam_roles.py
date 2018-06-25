from stacker.blueprints.base import Blueprint

from troposphere import (
    GetAtt,
    Output,
    Join,
    Ref,
    Sub,
    iam,
)

from awacs.aws import (
    Allow,
    Policy,
    Principal,
    Statement
)

from awacs import s3
from awacs import ec2

from awacs.helpers.trust import (
    get_default_assumerole_policy,
    get_lambda_assumerole_policy
)


class Roles(Blueprint):
    VARIABLES = {
        "Ec2Roles": {
            "type": list,
            "description": "names of ec2 roles to create",
            "default": [],
        },
        "LambdaRoles": {
            "type": list,
            "description": "names of lambda roles to create",
            "default": [],
        },
    }

    def __init__(self, *args, **kwargs):
        super(Roles, self).__init__(*args, **kwargs)
        self.roles = []
        self.policies = []

    def create_role(self, name, assumerole_policy):
        t = self.template

        role = t.add_resource(
            iam.Role(
                name,
                AssumeRolePolicyDocument=assumerole_policy,
            )
        )

        t.add_output(
            Output(name + "RoleName", Value=Ref(role))
        )
        t.add_output(
            Output(name + "RoleArn", Value=GetAtt(role.title, "Arn"))
        )

        self.roles.append(role)
        return role

    def create_ec2_role(self, name):
        return self.create_role(name, get_default_assumerole_policy())

    def create_lambda_role(self, name):
        return self.create_role(name, get_lambda_assumerole_policy())

    def generate_policy_statements(self):
        statements = []

        statements.append(
            Statement(
                Effect=Allow,
                Action=[
                    s3.GetObject,
                    s3.ListAllMyBuckets,
                ],
                Resource=["arn:aws:s3:::*"]
            )
        )

        statements.append(
            Statement(
                Effect=Allow,
                Action=[
                    ec2.DescribeInstances,
                    ec2.DescribeTags,
                    ec2.DescribeInstanceAttribute,
                    ec2.DescribeInstanceStatus
                ],
                Resource=["arn:aws:ec2:::*"]
            )
        )

        return statements

    def create_policy(self, name):
        statements = self.generate_policy_statements()
        if not statements:
            return

        t = self.template

        policy = t.add_resource(
            iam.PolicyType(
                "{}Policy".format(name),
                PolicyName=Sub("${AWS::StackName}-${Name}-policy", Name=name),
                PolicyDocument=Policy(
                    Statement=statements,
                ),
                Roles=[Ref(role) for role in self.roles],
            )
        )

        t.add_output(
            Output(name + "PolicyName", Value=Ref(policy))
        )

        self.policies.append(policy)

    def create_template(self):
        t = self.template
        variables = self.get_variables()

        for role in variables['Ec2Roles']:
            self.create_ec2_role(role)

        for role in variables['LambdaRoles']:
            self.create_lambda_role(role)

        self.create_policy('ec2readonly')

        if variables['Ec2Roles']:
            t.add_output(
                Output(
                    "Ec2Roles",
                    Value=Join(
                        ",",
                        [Ref(role) for role in variables['Ec2Roles']]
                    )
                )
            )
            Ec2instanceProfile = t.add_resource(
                iam.InstanceProfile(
                    "myInstanceProfileEc2",
                    Path='/',
                    Roles=[Join(
                        ",",
                        [Ref(role) for role in variables['Ec2Roles']]
                    )]
                )
            )
            t.add_output(
                Output(
                    "Ec2InstanceProfile",
                    Value=Ref(Ec2instanceProfile)
                )
            )

        if variables['LambdaRoles']:
            t.add_output(
                Output(
                    "LambdaRoles",
                    Value=Join(
                        ",",
                        [Ref(role) for role in variables['LambdaRoles']]
                    )
                )
            )
