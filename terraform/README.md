# Infrastructure as Code (Terraform)

This directory contains Terraform configuration for deploying AI Service infrastructure.

## Overview

Terraform manages the Kubernetes infrastructure for AI Service, including:
- Namespace
- ConfigMap
- Secrets
- Deployment
- Service
- Horizontal Pod Autoscaler (HPA)

## Prerequisites

1. **Terraform** >= 1.0
2. **Kubernetes cluster** access
3. **kubectl** configured

## Usage

### Initialize Terraform

```bash
cd terraform
terraform init
```

### Plan Changes

```bash
terraform plan
```

### Apply Configuration

```bash
terraform apply
```

### Destroy Infrastructure

```bash
terraform destroy
```

## Customization

### Update Variables

Edit `variables.tf` or use `-var` flags:

```bash
terraform apply -var="replicas=5" -var="image_tag=v1.2.0"
```

### Environment-Specific Configs

Create separate `.tfvars` files:

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

Apply with:
```bash
terraform apply -var-file=prod.tfvars
```

## Cloud Provider Specific

### AWS EKS

```hcl
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

### Azure AKS

```hcl
provider "kubernetes" {
  host                = azurerm_kubernetes_cluster.cluster.kube_config.0.host
  client_certificate = base64decode(azurerm_kubernetes_cluster.cluster.kube_config.0.client_certificate)
  client_key         = base64decode(azurerm_kubernetes_cluster.cluster.kube_config.0.client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.cluster.kube_config.0.cluster_ca_certificate)
}
```

## Best Practices

1. **Version Control**: Keep Terraform files in Git
2. **State Management**: Use remote state (S3, GCS, Azure Storage)
3. **Secrets Management**: Use external secret management
4. **Modularity**: Break into modules for reusability
5. **Testing**: Test in dev/staging before production

## State Management

### Remote State (Recommended)

```hcl
terraform {
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "ai-service/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Outputs

After applying, get outputs:

```bash
terraform output
```

Available outputs:
- `namespace` - Kubernetes namespace
- `service_name` - Service name

## Troubleshooting

### Authentication Issues

```bash
# Verify kubectl access
kubectl get nodes

# Check Terraform provider config
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

