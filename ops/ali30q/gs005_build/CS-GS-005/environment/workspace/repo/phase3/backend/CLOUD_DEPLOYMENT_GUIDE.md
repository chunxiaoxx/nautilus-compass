# 云服务部署指南

## 文档信息
- **版本**: 1.0.0
- **创建日期**: 2026-02-26
- **适用环境**: 生产环境
- **维护团队**: DevOps团队

---

## 1. 概述

本指南详细说明如何在主流云服务平台上部署 Nautilus Phase 3 Backend 系统，包括 AWS、Azure、GCP 和 DigitalOcean。

### 1.1 云平台选择

| 平台 | 优势 | 劣势 | 适用场景 | 推荐度 |
|------|------|------|----------|--------|
| AWS | 服务最全面，生态成熟 | 价格较高，学习曲线陡 | 大型企业，复杂架构 | ⭐⭐⭐⭐⭐ |
| Azure | 与微软产品集成好 | 文档较复杂 | 使用微软技术栈 | ⭐⭐⭐⭐ |
| GCP | 价格优惠，AI/ML强 | 服务相对较少 | 数据分析，AI应用 | ⭐⭐⭐⭐ |
| DigitalOcean | 简单易用，价格低 | 服务较基础 | 中小型项目，初创 | ⭐⭐⭐⭐ |

### 1.2 成本估算

**小型部署** (100 并发用户):
- AWS: $150-200/月
- Azure: $140-180/月
- GCP: $130-170/月
- DigitalOcean: $80-120/月

**中型部署** (1000 并发用户):
- AWS: $500-700/月
- Azure: $450-650/月
- GCP: $400-600/月
- DigitalOcean: $300-450/月

---

## 2. AWS 部署指南

### 2.1 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    Route 53 (DNS)                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              CloudFront (CDN)                            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│     Application Load Balancer (ALB)                      │
└────────┬───────────────────────────┬────────────────────┘
         │                           │
┌────────▼────────┐         ┌───────▼────────┐
│   ECS Fargate   │         │  ECS Fargate   │
│   (Container 1) │         │  (Container 2) │
└────────┬────────┘         └───────┬────────┘
         │                           │
         └───────────┬───────────────┘
                     │
         ┌───────────▼───────────┐
         │   RDS PostgreSQL      │
         │   (Multi-AZ)          │
         └───────────────────────┘
                     │
         ┌───────────▼───────────┐
         │   ElastiCache Redis   │
         │   (Cluster Mode)      │
         └───────────────────────┘
```

### 2.2 前置准备

#### 2.2.1 安装 AWS CLI

```bash
# Linux/macOS
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 验证安装
aws --version

# 配置 AWS CLI
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: us-east-1
# Default output format: json
```

#### 2.2.2 创建 IAM 用户

```bash
# 创建 IAM 用户
aws iam create-user --user-name nautilus-deploy

# 附加策略
aws iam attach-user-policy \
  --user-name nautilus-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess

aws iam attach-user-policy \
  --user-name nautilus-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonRDSFullAccess

# 创建访问密钥
aws iam create-access-key --user-name nautilus-deploy
```

### 2.3 网络配置

#### 2.3.1 创建 VPC

```bash
# 创建 VPC
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=nautilus-vpc}]'

# 记录 VPC ID
VPC_ID="vpc-xxxxxxxxx"

# 启用 DNS 主机名
aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames
```

#### 2.3.2 创建子网

```bash
# 公有子网 1 (us-east-1a)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=nautilus-public-1a}]'

# 公有子网 2 (us-east-1b)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=nautilus-public-1b}]'

# 私有子网 1 (us-east-1a)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=nautilus-private-1a}]'

# 私有子网 2 (us-east-1b)
aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=nautilus-private-1b}]'
```

#### 2.3.3 配置互联网网关

```bash
# 创建互联网网关
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=nautilus-igw}]'

IGW_ID="igw-xxxxxxxxx"

# 附加到 VPC
aws ec2 attach-internet-gateway \
  --vpc-id $VPC_ID \
  --internet-gateway-id $IGW_ID

# 创建路由表
aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=nautilus-public-rt}]'

RTB_ID="rtb-xxxxxxxxx"

# 添加路由
aws ec2 create-route \
  --route-table-id $RTB_ID \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id $IGW_ID

# 关联子网
aws ec2 associate-route-table \
  --subnet-id $PUBLIC_SUBNET_1_ID \
  --route-table-id $RTB_ID
```

### 2.4 RDS 数据库部署

#### 2.4.1 创建数据库子网组

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name nautilus-db-subnet \
  --db-subnet-group-description "Nautilus DB Subnet Group" \
  --subnet-ids $PRIVATE_SUBNET_1_ID $PRIVATE_SUBNET_2_ID \
  --tags Key=Name,Value=nautilus-db-subnet
```

#### 2.4.2 创建安全组

```bash
# 创建数据库安全组
aws ec2 create-security-group \
  --group-name nautilus-db-sg \
  --description "Nautilus Database Security Group" \
  --vpc-id $VPC_ID

DB_SG_ID="sg-xxxxxxxxx"

# 允许来自应用层的访问
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $APP_SG_ID
```

#### 2.4.3 创建 RDS 实例

```bash
aws rds create-db-instance \
  --db-instance-identifier nautilus-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --master-username nautilus_admin \
  --master-user-password 'YourStrongPassword123!' \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --db-subnet-group-name nautilus-db-subnet \
  --vpc-security-group-ids $DB_SG_ID \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "mon:04:00-mon:05:00" \
  --multi-az \
  --publicly-accessible false \
  --tags Key=Name,Value=nautilus-db
```

### 2.5 ElastiCache Redis 部署

```bash
# 创建 Redis 子网组
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name nautilus-redis-subnet \
  --cache-subnet-group-description "Nautilus Redis Subnet Group" \
  --subnet-ids $PRIVATE_SUBNET_1_ID $PRIVATE_SUBNET_2_ID

# 创建 Redis 安全组
aws ec2 create-security-group \
  --group-name nautilus-redis-sg \
  --description "Nautilus Redis Security Group" \
  --vpc-id $VPC_ID

REDIS_SG_ID="sg-xxxxxxxxx"

# 允许来自应用层的访问
aws ec2 authorize-security-group-ingress \
  --group-id $REDIS_SG_ID \
  --protocol tcp \
  --port 6379 \
  --source-group $APP_SG_ID

# 创建 Redis 集群
aws elasticache create-replication-group \
  --replication-group-id nautilus-redis \
  --replication-group-description "Nautilus Redis Cluster" \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.medium \
  --num-cache-clusters 2 \
  --automatic-failover-enabled \
  --cache-subnet-group-name nautilus-redis-subnet \
  --security-group-ids $REDIS_SG_ID \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --auth-token "YourRedisAuthToken123!"
```

### 2.6 ECS Fargate 部署

#### 2.6.1 创建 ECR 仓库

```bash
# 创建 ECR 仓库
aws ecr create-repository \
  --repository-name nautilus-backend \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256

# 获取登录命令
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# 构建并推送镜像
docker build -t nautilus-backend .
docker tag nautilus-backend:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/nautilus-backend:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/nautilus-backend:latest
```

#### 2.6.2 创建 ECS 集群

```bash
aws ecs create-cluster \
  --cluster-name nautilus-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1 \
    capacityProvider=FARGATE_SPOT,weight=1
```

#### 2.6.3 创建任务定义

```json
{
  "family": "nautilus-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "nautilus-backend",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/nautilus-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:nautilus/db-url"
        },
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:nautilus/redis-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/nautilus-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

保存为 `task-definition.json`，然后注册：

```bash
aws ecs register-task-definition \
  --cli-input-json file://task-definition.json
```

#### 2.6.4 创建 Application Load Balancer

```bash
# 创建 ALB
aws elbv2 create-load-balancer \
  --name nautilus-alb \
  --subnets $PUBLIC_SUBNET_1_ID $PUBLIC_SUBNET_2_ID \
  --security-groups $ALB_SG_ID \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4

ALB_ARN="arn:aws:elasticloadbalancing:..."

# 创建目标组
aws elbv2 create-target-group \
  --name nautilus-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

TG_ARN="arn:aws:elasticloadbalancing:..."

# 创建监听器
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-east-1:123456789012:certificate/xxx \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

#### 2.6.5 创建 ECS 服务

```bash
aws ecs create-service \
  --cluster nautilus-cluster \
  --service-name nautilus-backend-service \
  --task-definition nautilus-backend:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNET_1_ID,$PRIVATE_SUBNET_2_ID],securityGroups=[$APP_SG_ID],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=nautilus-backend,containerPort=8000" \
  --health-check-grace-period-seconds 60 \
  --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100" \
  --enable-execute-command
```

### 2.7 使用 Terraform 自动化部署

创建 `main.tf`:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "nautilus-vpc"
  }
}

# 公有子网
resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "nautilus-public-${count.index + 1}"
  }
}

# 私有子网
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 11}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "nautilus-private-${count.index + 1}"
  }
}

# RDS 实例
resource "aws_db_instance" "main" {
  identifier             = "nautilus-db"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.t3.medium"
  allocated_storage      = 100
  storage_type           = "gp3"
  storage_encrypted      = true
  db_name                = "nautilus_production"
  username               = "nautilus_admin"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  multi_az               = true
  backup_retention_period = 7
  skip_final_snapshot    = false
  final_snapshot_identifier = "nautilus-db-final-snapshot"

  tags = {
    Name = "nautilus-db"
  }
}

# ECS 集群
resource "aws_ecs_cluster" "main" {
  name = "nautilus-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECS 服务
resource "aws_ecs_service" "main" {
  name            = "nautilus-backend-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "nautilus-backend"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.https]
}
```

部署：

```bash
terraform init
terraform plan
terraform apply
```

### 2.8 监控和日志

#### 2.8.1 CloudWatch 日志

```bash
# 创建日志组
aws logs create-log-group \
  --log-group-name /ecs/nautilus-backend

# 设置保留期
aws logs put-retention-policy \
  --log-group-name /ecs/nautilus-backend \
  --retention-in-days 30
```

#### 2.8.2 CloudWatch 告警

```bash
# CPU 使用率告警
aws cloudwatch put-metric-alarm \
  --alarm-name nautilus-high-cpu \
  --alarm-description "CPU utilization exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ServiceName,Value=nautilus-backend-service \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:nautilus-alerts
```

### 2.9 成本优化

1. **使用 Savings Plans**: 节省 30-50% 成本
2. **使用 Spot Instances**: ECS Fargate Spot 节省 70%
3. **使用 Reserved Instances**: RDS 预留实例节省 40-60%
4. **启用 S3 生命周期策略**: 自动归档旧数据
5. **使用 CloudFront**: 减少数据传输成本
6. **定期审查资源**: 删除未使用的资源

---

## 3. Azure 部署指南

### 3.1 架构设计

```
Azure Front Door → Application Gateway → AKS/Container Instances
                                      ↓
                            Azure Database for PostgreSQL
                                      ↓
                            Azure Cache for Redis
```

### 3.2 前置准备

```bash
# 安装 Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 登录
az login

# 设置订阅
az account set --subscription "Your-Subscription-ID"
```

### 3.3 创建资源组

```bash
az group create \
  --name nautilus-rg \
  --location eastus
```

### 3.4 创建虚拟网络

```bash
az network vnet create \
  --resource-group nautilus-rg \
  --name nautilus-vnet \
  --address-prefix 10.0.0.0/16 \
  --subnet-name app-subnet \
  --subnet-prefix 10.0.1.0/24
```

### 3.5 部署 PostgreSQL

```bash
az postgres flexible-server create \
  --resource-group nautilus-rg \
  --name nautilus-db \
  --location eastus \
  --admin-user nautilus_admin \
  --admin-password 'YourStrongPassword123!' \
  --sku-name Standard_D2s_v3 \
  --tier GeneralPurpose \
  --storage-size 128 \
  --version 15 \
  --high-availability Enabled \
  --backup-retention 7
```

### 3.6 部署 Redis

```bash
az redis create \
  --resource-group nautilus-rg \
  --name nautilus-redis \
  --location eastus \
  --sku Standard \
  --vm-size c1 \
  --enable-non-ssl-port false \
  --minimum-tls-version 1.2
```

### 3.7 部署容器实例

```bash
az container create \
  --resource-group nautilus-rg \
  --name nautilus-backend \
  --image youracr.azurecr.io/nautilus-backend:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables \
    ENVIRONMENT=production \
  --secure-environment-variables \
    DATABASE_URL=$DB_URL \
    REDIS_URL=$REDIS_URL \
  --restart-policy Always
```

---

## 4. GCP 部署指南

### 4.1 前置准备

```bash
# 安装 gcloud CLI
curl https://sdk.cloud.google.com | bash

# 初始化
gcloud init

# 设置项目
gcloud config set project nautilus-project
```

### 4.2 创建 GKE 集群

```bash
gcloud container clusters create nautilus-cluster \
  --zone us-central1-a \
  --num-nodes 2 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10
```

### 4.3 部署 Cloud SQL

```bash
gcloud sql instances create nautilus-db \
  --database-version=POSTGRES_15 \
  --tier=db-n1-standard-2 \
  --region=us-central1 \
  --availability-type=REGIONAL \
  --backup-start-time=03:00
```

### 4.4 部署 Memorystore Redis

```bash
gcloud redis instances create nautilus-redis \
  --size=5 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=standard
```

---

## 5. DigitalOcean 部署指南

### 5.1 前置准备

```bash
# 安装 doctl
snap install doctl

# 认证
doctl auth init
```

### 5.2 创建 Droplet

```bash
doctl compute droplet create nautilus-app \
  --size s-2vcpu-4gb \
  --image ubuntu-22-04-x64 \
  --region nyc1 \
  --ssh-keys your-ssh-key-id
```

### 5.3 创建托管数据库

```bash
doctl databases create nautilus-db \
  --engine pg \
  --version 15 \
  --size db-s-2vcpu-4gb \
  --region nyc1 \
  --num-nodes 2
```

### 5.4 创建 Redis 集群

```bash
doctl databases create nautilus-redis \
  --engine redis \
  --version 7 \
  --size db-s-1vcpu-2gb \
  --region nyc1
```

### 5.5 部署应用

```bash
# SSH 到 Droplet
doctl compute ssh nautilus-app

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 拉取并运行容器
docker run -d \
  --name nautilus-backend \
  --restart always \
  -p 8000:8000 \
  -e DATABASE_URL=$DB_URL \
  -e REDIS_URL=$REDIS_URL \
  your-registry/nautilus-backend:latest
```

---

## 6. 相关文档

- [生产环境部署计划](PRODUCTION_DEPLOYMENT_PLAN.md)
- [生产环境检查清单](PRODUCTION_READINESS_CHECKLIST.md)
- [数据库生产配置](PRODUCTION_DATABASE_GUIDE.md)

---

**文档结束**
