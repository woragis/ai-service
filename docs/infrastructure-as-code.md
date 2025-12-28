# Infrastructure as Code Guide

This guide explains Terraform configuration for AI Service infrastructure.

## Overview

Terraform manages Kubernetes infrastructure as code, enabling:
- Version-controlled infrastructure
- Reproducible deployments
- Environment consistency
- Easy rollbacks

## Configuration

**Location:** `terraform/`

**Files:**
- `main.tf` - Main configuration
- `variables.tf` - Variables
- `outputs.tf` - Outputs (if needed)

## Resources Managed

- Namespace
- ConfigMap
- Secret
- Deployment
- Service
- Horizontal Pod Autoscaler (HPA)

## Usage

### Initialize

```bash
cd terraform
terraform init
```

### Plan

```bash
terraform plan
```

### Apply

```bash
terraform apply
```

### Destroy

```bash
terraform destroy
```

## Variables

Customize via variables:

```bash
terraform apply \
  -var="replicas=5" \
  -var="image_tag=v1.2.0" \
  -var="environment=production"
```

Or use `.tfvars` files:

```bash
terraform apply -var-file=prod.tfvars
```

## Environment-Specific Configs

**terraform/prod.tfvars:**
```hcl
environment = "production"
replicas = 5
image_tag = "v1.2.0"
min_replicas = 3
max_replicas = 20
```

**terraform/dev.tfvars:**
```hcl
environment = "development"
replicas = 1
image_tag = "latest"
min_replicas = 1
max_replicas = 3
```

## State Management

### Local State (Default)

State stored in `terraform.tfstate` (not recommended for teams).

### Remote State (Recommended)

Use S3, GCS, or Azure Storage:

```hcl
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "ai-service/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Best Practices

1. **Version Control**: Keep Terraform files in Git
2. **Remote State**: Use remote state backend
3. **Secrets Management**: Use external secret management
4. **Modularity**: Break into modules for reusability
5. **Testing**: Test in dev/staging before production
6. **Documentation**: Document all variables and outputs

## Cloud Provider Specific

### AWS EKS

```hcl
data "aws_eks_cluster" "cluster" {
  name = var.cluster_name
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority.0.data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}
```

### GCP GKE

```hcl
provider "kubernetes" {
  host  = "https://${google_container_cluster.cluster.endpoint}"
  token = data.google_client_config.provider.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.cluster.master_auth[0].cluster_ca_certificate)
}
```

## Troubleshooting

### Authentication Issues

```bash
# Verify kubectl access
kubectl get nodes

# Check provider configuration
terraform providers
```

### Resource Conflicts

```bash
# Import existing resources
terraform import kubernetes_deployment.ai_service default/ai-service
```

## References

- [Terraform Kubernetes Provider](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)

