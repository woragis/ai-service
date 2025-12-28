# Terraform configuration for AI Service infrastructure
# This is a template - customize for your cloud provider

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

# Kubernetes provider configuration
# Update with your cluster details
provider "kubernetes" {
  # Configure based on your setup:
  # - Kubeconfig file
  # - Service account
  # - Cloud provider credentials
  config_path = "~/.kube/config"
}

# Namespace
resource "kubernetes_namespace" "ai_service" {
  metadata {
    name = "ai-service"
    labels = {
      app     = "ai-service"
      managed = "terraform"
    }
  }
}

# ConfigMap for environment variables
resource "kubernetes_config_map" "ai_service" {
  metadata {
    name      = "ai-service-config"
    namespace = kubernetes_namespace.ai_service.metadata[0].name
  }

  data = {
    ENV              = "production"
    CORS_ENABLED     = "true"
    CORS_ALLOWED_ORIGINS = "*"
    LOG_LEVEL        = "info"
  }
}

# Secret for API keys (use external secret management in production)
resource "kubernetes_secret" "ai_service" {
  metadata {
    name      = "ai-service-secrets"
    namespace = kubernetes_namespace.ai_service.metadata[0].name
  }

  type = "Opaque"

  # In production, use external secret management (e.g., AWS Secrets Manager, Vault)
  # This is just a template
  data = {
    # OPENAI_API_KEY = base64encode(var.openai_api_key)
    # ANTHROPIC_API_KEY = base64encode(var.anthropic_api_key)
  }
}

# Deployment
resource "kubernetes_deployment" "ai_service" {
  metadata {
    name      = "ai-service"
    namespace = kubernetes_namespace.ai_service.metadata[0].name
    labels = {
      app = "ai-service"
    }
  }

  spec {
    replicas = 3

    selector {
      match_labels = {
        app = "ai-service"
      }
    }

    template {
      metadata {
        labels = {
          app = "ai-service"
        }
      }

      spec {
        container {
          name  = "ai-service"
          image = "woragis/ai-service:latest"

          port {
            container_port = 8000
            name           = "http"
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.ai_service.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret.ai_service.metadata[0].name
            }
          }

          resources {
            requests = {
              cpu    = "500m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "1000m"
              memory = "1Gi"
            }
          }

          liveness_probe {
            http_get {
              path = "/healthz"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }

          readiness_probe {
            http_get {
              path = "/healthz"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds        = 5
          }
        }
      }
    }
  }
}

# Service
resource "kubernetes_service" "ai_service" {
  metadata {
    name      = "ai-service"
    namespace = kubernetes_namespace.ai_service.metadata[0].name
    labels = {
      app = "ai-service"
    }
  }

  spec {
    type = "ClusterIP"

    selector = {
      app = "ai-service"
    }

    port {
      port        = 80
      target_port = 8000
      protocol    = "TCP"
      name        = "http"
    }
  }
}

# Horizontal Pod Autoscaler
resource "kubernetes_horizontal_pod_autoscaler" "ai_service" {
  metadata {
    name      = "ai-service"
    namespace = kubernetes_namespace.ai_service.metadata[0].name
  }

  spec {
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.ai_service.metadata[0].name
    }

    min_replicas = 2
    max_replicas = 10

    target_cpu_utilization_percentage = 70
  }
}

# Outputs
output "namespace" {
  value = kubernetes_namespace.ai_service.metadata[0].name
}

output "service_name" {
  value = kubernetes_service.ai_service.metadata[0].name
}

