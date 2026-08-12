# Employee API — Production CI/CD on AWS

A production-style Flask REST API deployed on AWS using Docker, Amazon ECR, Amazon ECS on EC2, Application Load Balancer, Amazon RDS PostgreSQL, Terraform, GitHub Actions, and AWS Secrets Manager.

This project was built as a hands-on DevOps learning project covering application containerization, CI, security scanning, container image publishing, infrastructure as code, AWS networking, ECS deployment, load balancing, database connectivity, and production API testing.

---

## Architecture

```text
                         GitHub
                           |
                           | git push
                           v
                  GitHub Actions (CI)
                           |
             +-------------+-------------+
             |             |             |
           Flake8        Pytest        Bandit
             |             |             |
             +-------------+-------------+
                           |
                      Docker Build
                           |
                         Trivy
                           |
                           v
                  Amazon ECR Repository
                           |
                    Manual ECS Deploy
                           |
                           v
                 Amazon ECS Service
                           |
                     ECS EC2 Instance
                           |
                    Flask Container
                      port 5005
                           |
                           v
                Application Load Balancer
                           |
                    HTTP :80 /health
                           |
                           v
                   Internet / Client

Flask Container
       |
       | PostgreSQL :5432
       v
   Amazon RDS
   PostgreSQL
   Private DB subnets
```

### AWS network architecture

```text
                         Internet
                            |
                            v
                    Application Load Balancer
                         Public Subnets
                            |
                            | TCP 5005
                            v
                     ECS / EC2 Instances
                       Private App Subnets
                            |
                            | TCP 5432
                            v
                    RDS PostgreSQL
                    Private DB Subnets
```

The infrastructure is managed with Terraform. The project uses a VPC with public, private application, and private database subnets. Security groups restrict traffic between the ALB, ECS, and RDS layers.

---

## Technology Stack

| Area | Technology |
|---|---|
| Application | Python 3.12 |
| Framework | Flask |
| API | REST |
| ORM | Flask-SQLAlchemy / SQLAlchemy |
| Database | PostgreSQL |
| Containerization | Docker |
| Container Registry | Amazon ECR |
| Container Orchestration | Amazon ECS |
| ECS Launch Type | EC2 |
| Load Balancer | AWS Application Load Balancer |
| Infrastructure as Code | Terraform |
| CI | GitHub Actions |
| Testing | Pytest |
| Linting | Flake8 |
| Security | Bandit |
| Container Scanning | Trivy |
| Secrets | AWS Secrets Manager |
| Cloud | AWS |
| Region | us-east-1 |

---

## Project Structure

```text
python-flask-production-cicd/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── routes.py
│   ├── run.py
│   └── requirements.txt
│
├── tests/
│   └── ...
│
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── ...
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── requirements-dev.txt
├── .gitignore
└── README.md
```

---

# Application

The application is a Flask REST API for managing employees.

The API supports complete CRUD operations:

```text
CREATE  -> POST
READ    -> GET
UPDATE  -> PUT
DELETE  -> DELETE
```

## API Endpoints

### Health check

```http
GET /health
```

Example:

```json
{
  "service": "employee-api",
  "status": "healthy"
}
```

### Create employee

```http
POST /employees
Content-Type: application/json
```

Example:

```json
{
  "name": "Rahul Sharma",
  "email": "rahul@example.com",
  "department": "Engineering",
  "salary": 65000
}
```

### Get all employees

```http
GET /employees
```

### Get one employee

```http
GET /employees/<id>
```

### Update employee

```http
PUT /employees/<id>
Content-Type: application/json
```

### Delete employee

```http
DELETE /employees/<id>
```

---

# Local Development

## 1. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## 2. Install dependencies

```bash
pip install -r app/requirements.txt
pip install -r requirements-dev.txt
```

## 3. Configure environment variables

The application reads the database connection from:

```text
DATABASE_URL
```

Example for local PostgreSQL:

```text
DATABASE_URL=postgresql://postgres:<password>@localhost:5432/employees
```

Do not commit `.env` files or database credentials to Git.

## 4. Run Flask

```bash
python -m app.run
```

The application listens on:

```text
http://localhost:5005
```

---

# Docker

The root `Dockerfile` builds the production application image.

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 5005

CMD ["python", "app/run.py"]
```

Build:

```bash
docker build -t employee-api:ci .
```

Run locally:

```bash
docker run --rm \
  --env-file .env \
  -p 5005:5005 \
  employee-api:ci
```

For local Docker testing with a PostgreSQL container, Docker Compose can be used separately. It is not part of the AWS production deployment path.

---

# CI Pipeline

GitHub Actions performs continuous integration when code is pushed to `main` or a pull request targets `main`.

Current CI flow:

```text
GitHub Push / Pull Request
            |
            v
       Checkout code
            |
            v
       Setup Python 3.12
            |
            v
     Install dependencies
            |
            v
          Flake8
            |
            v
     Pytest + 80% coverage
            |
            v
          Bandit
            |
            v
       Docker build
            |
            v
          Trivy
            |
            v
     Configure AWS via OIDC
            |
            v
         ECR login
            |
            v
       Docker tag
            |
            v
       Push image to ECR
```

The pipeline uses GitHub Actions OIDC to assume an AWS IAM role instead of storing long-lived AWS access keys in GitHub.

Images are tagged with both:

```text
<git-sha>
latest
```

The Git SHA tag provides an immutable reference to a particular source revision.

---

# Manual Production Deployment

The current project intentionally keeps ECS deployment manual.

GitHub Actions pushes the image to ECR, but ECS is not automatically updated by the workflow.

After a successful CI/ECR run, trigger a new ECS deployment manually:

```bash
aws ecs update-service \
  --cluster employee-api-cluster \
  --service employee-api-service \
  --force-new-deployment \
  --region us-east-1
```

This tells the ECS service to start a new deployment using the task definition and container image configuration.

Check service status:

```bash
aws ecs describe-services \
  --cluster employee-api-cluster \
  --services employee-api-service \
  --region us-east-1 \
  --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount,status:status,taskDefinition:taskDefinition}'
```

List running tasks:

```bash
aws ecs list-tasks \
  --cluster employee-api-cluster \
  --service-name employee-api-service \
  --region us-east-1
```

Inspect a task:

```bash
aws ecs describe-tasks \
  --cluster employee-api-cluster \
  --tasks <TASK_ID> \
  --region us-east-1
```

---

# ECS

The ECS service runs with the EC2 launch type.

The task definition specifies:

```text
Family: employee-api-task
Container: employee-api
Container port: 5005
CPU: 256
Memory: 512 MiB
Network mode: awsvpc
```

The ECS service maintains the desired number of application tasks.

Conceptually:

```text
Task Definition
      |
      | blueprint
      v
     Task
      |
      | actual running workload
      v
Container
```

The ECS service is responsible for maintaining the desired task count and registering tasks with the ALB target group.

---

# Amazon ECR

The Docker image is stored in Amazon ECR.

Example repository:

```text
employee-api
```

Build:

```bash
docker build -t employee-api:ci .
```

Tag:

```bash
docker tag employee-api:ci \
  <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/employee-api:latest
```

Push:

```bash
docker push \
  <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/employee-api:latest
```

For production deployments, the image can also be referenced by its Git SHA tag.

---

# Application Load Balancer

The ALB provides the public entry point to the application.

Traffic flow:

```text
Client
  |
  | HTTP :80
  v
ALB
  |
  | forward to target group
  v
ECS task :5005
```

The target group performs health checks against:

```text
/health
```

Expected HTTP status:

```text
200
```

A healthy target means the ALB can successfully reach the Flask container.

---

# Database

Production uses Amazon RDS PostgreSQL.

The database is placed in private database subnets.

The application connects to PostgreSQL using a database URL similar to:

```text
postgresql://<username>:<password>@<rds-endpoint>:5432/<database>
```

The production database URL is stored using AWS Secrets Manager rather than being hard-coded into the container image.

The ECS task execution role is granted permission to retrieve the required secret.

Database traffic is restricted to PostgreSQL port:

```text
5432
```

from the ECS security group.

---

# Terraform

Terraform provisions the AWS infrastructure.

The project includes infrastructure for:

```text
VPC
├── Public subnets
├── Private application subnets
├── Private database subnets
├── Internet Gateway
├── NAT Gateway
└── Route tables

Security
├── ALB security group
├── ECS security group
└── RDS security group

Compute
├── ECS cluster
├── EC2 capacity
├── Auto Scaling Group
└── ECS task definition
    └── ECS service

Networking
├── Application Load Balancer
├── Target Group
└── Listener

Database
├── RDS PostgreSQL
└── DB subnet group

Security / Configuration
├── IAM roles
└── AWS Secrets Manager
```

Useful commands:

```bash
cd terraform
```

Initialize:

```bash
terraform init
```

Format:

```bash
terraform fmt
```

Validate:

```bash
terraform validate
```

Plan:

```bash
terraform plan
```

Apply:

```bash
terraform apply
```

View outputs:

```bash
terraform output
```

---

# Security

The project includes multiple security controls in the CI pipeline:

### Flake8

Checks Python code quality and style.

### Pytest

Runs automated tests and enforces a minimum coverage threshold of 80%.

### Bandit

Scans Python source code for common security issues.

### Trivy

Scans the Docker image for HIGH and CRITICAL vulnerabilities.

### AWS OIDC

GitHub Actions uses an IAM role through OIDC instead of storing long-lived AWS credentials in GitHub Actions secrets.

### Secrets Manager

Production database credentials are not baked into the Docker image.

---

# Production Verification

The deployment was verified end-to-end.

Health check:

```bash
curl http://<ALB_DNS_NAME>/health
```

Expected:

```json
{
  "service": "employee-api",
  "status": "healthy"
}
```

The production CRUD API was also tested successfully:

```text
POST   /employees       CREATE
GET    /employees       READ ALL
GET    /employees/<id>  READ ONE
PUT    /employees/<id>  UPDATE
DELETE /employees/<id>  DELETE
```

This verifies the complete request path:

```text
Internet
   |
   v
ALB
   |
   v
ECS / Flask
   |
   v
SQLAlchemy
   |
   v
RDS PostgreSQL
```

---

# Troubleshooting Lessons

During development, the project encountered and resolved several realistic production issues.

## Docker architecture mismatch

The development machine is Apple Silicon (`arm64`) while the ECS EC2 capacity expects `linux/amd64`.

An incompatible image can produce:

```text
CannotPullContainerError:
no matching manifest for linux/amd64
```

The production image must include a compatible `linux/amd64` image.

## Database connection

A container cannot use `localhost` to reach a PostgreSQL service running in another container.

For Docker networking, use the service/container DNS name.

For AWS production, the Flask container connects to the private RDS endpoint.

## ECS memory

ECS schedules tasks based on available CPU and memory on the EC2 container instance.

If insufficient memory is available, ECS can report:

```text
no container instance met all of its requirements
```

This project used a task definition requesting:

```text
512 MiB
```

while the ECS instance had limited remaining memory.

---

# CI vs CD in This Project

The current project separates CI from manual production deployment.

### Continuous Integration

Automated:

```text
Code
 ↓
Tests
 ↓
Lint
 ↓
Security scans
 ↓
Docker build
 ↓
ECR push
```

### Production Deployment

Manual:

```text
ECR
 ↓
aws ecs update-service
 ↓
ECS deployment
 ↓
ALB health check
 ↓
Production
```

This is intentional so the production deployment remains under manual control.

---

# What This Project Demonstrates

This project is designed as a practical DevOps portfolio project covering:

- Git and GitHub
- GitHub Actions
- CI pipelines
- Python Flask
- REST APIs
- Automated testing
- Code coverage
- Docker
- Docker images and containers
- Amazon ECR
- AWS IAM
- GitHub OIDC
- Amazon ECS
- ECS EC2 launch type
- ECS Task Definitions
- ECS Services
- Application Load Balancer
- Target groups and health checks
- VPC networking
- Public and private subnets
- Security groups
- NAT Gateway
- Amazon RDS PostgreSQL
- AWS Secrets Manager
- Terraform
- Infrastructure as Code
- Container security scanning
- Production troubleshooting

---

# Future Improvements

Possible next steps for this project:

- Automatic ECS deployment from GitHub Actions
- Immutable ECS image deployment using Git SHA tags
- ECS deployment verification
- Automatic rollback
- CloudWatch logs and metrics
- Application monitoring with Prometheus and Grafana
- HTTPS with ACM
- Custom domain
- ECS service auto scaling
- Blue/green deployment
- Canary deployment
- Kubernetes migration
- GitOps with Argo CD

---

## Learning Path

This project is part of a broader DevOps learning path covering Linux, networking, Git, Python, AWS, Docker, CI/CD, Kubernetes, networking services, configuration management, Terraform, and monitoring. The roadmap identifies Docker/containerization, CI/CD, Kubernetes, Terraform, and monitoring as major DevOps learning areas. 
