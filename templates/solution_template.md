# CET IaC Auto-Deploy — Solution Architecture Document

## 1. Purpose and Scope

This document describes the solution architecture for **CET IaC Auto-Deploy**, a standardized platform for building, pushing, and deploying containerized applications ("Standard Apps") to Amazon EKS.

It covers:

- Architecture design (logical and deployment views)
- Design decisions and trade-offs
- Core components and responsibilities
- Interfaces and integration patterns
- API specifications for the control plane
- Third-party dependencies and backing services

Out of scope:

- Detailed cluster platform internals outside this repository
- Organization-specific network/security controls not represented in code

---

## 2. Executive Summary

The platform provides two deployment modes:

1. **Local/Operator-driven mode**: Developers or operators run scripts/Terraform locally.
2. **Remote API-driven mode**: CI/CD or users call a deployment API that orchestrates build and deployment.

The architecture is layered:

- **Layer A: Build Infrastructure** (`terraform/01-buildkitd`) provisions a centralized BuildKit daemon.
- **Layer B: Control Plane** (`terraform/02-app-deploy`, `src/api-service`, `src/deploy`) hosts and runs orchestration APIs.
- **Layer C: Managed App Plane** (`terraform/03-managed-app`, `terraform/modules/app-deploy`, `charts/standard-app`) deploys application workloads with standardized Kubernetes resources.

This separation enables standardized deployments, reusable infrastructure patterns, and controlled security defaults while allowing application teams to configure runtime behavior through declarative input.

---

## 3. Architecture Design

## 3.0 System Diagram

```text
  +-------------------------+            +------------------------------------------+
  | Developer / CI Pipeline |            |            Git Provider                   |
  | (manual or automated)   |            |             (HTTPS/SSH)                   |
  +------------+------------+            +-------------------+----------------------+
               |                                         ^
               | POST /build, /deploy (YAML)            | git clone
               v                                         |
  +------------+---------------------------------------------------------------+
  |                         Control Plane API                                   |
  |                       src/api-service/app.py                                |
  +------------+-------------------------------+--------------------------------+
               |                               |
               | build orchestration           | deploy orchestration
               v                               v
  +------------+------------+        +---------+-------------------------------+
  | BuildKit Service        |        | Deployment Logic                         |
  | terraform/01-buildkitd  |        | src/deploy/deploy.py                     |
  +------------+------------+        +---------+-------------------------------+
               |                               |
               | push image                    | terraform init/apply
               v                               v
  +------------+------------+        +---------+-------------------------------+
  | Amazon ECR              |        | Terraform Entry                          |
  | Container Registry      |        | terraform/03-managed-app                 |
  +------------+------------+        +---------+-------------------------------+
                                                |
                                                | module call
                                                v
                                    +-----------+--------------------------------+
                                    | app-deploy Terraform Module                |
                                    | terraform/modules/app-deploy               |
                                    +-----------+--------------------------------+
                                                |
                                                | helm release / k8s resources
                                                v
                                    +-----------+--------------------------------+
                                    | standard-app Helm Chart                    |
                                    | charts/standard-app                        |
                                    +-----------+--------------------------------+
                                                |
                                                v
                                    +-----------+--------------------------------+
                                    | Amazon EKS Cluster                         |
                                    | (managed application workloads)            |
                                    +-----------+--------------------------------+
                                                ^
                      external HTTP(S)          |
  +-------------------------+                   |
  | Ingress Controller      +-------------------+
  | (env-provided)          |
  +-------------------------+

  Supporting/Backing Services used by module and workloads:
  - AWS Secrets Manager (application secrets integration)
  - Amazon S3 (Terraform backend and optional app bucket)
  - AWS IAM (roles/policies for deploy and runtime access)

  Runtime relations:
  - EKS pulls container images from Amazon ECR.
  - EKS workloads consume secrets through configured secret integration.
  - EKS workloads may access S3 and IAM-protected AWS APIs based on role bindings.

## 3.1 Design Goals

- **Standardization**: enforce common deployment patterns for EKS workloads.
- **Self-service**: allow app teams to deploy with minimal Kubernetes/Terraform expertise.
- **Security-by-default**: run workloads as non-root, integrate with AWS secrets, use least privilege where possible.
- **Reusability**: centralize deployment logic in Terraform modules and Helm templates.
- **Automation-ready**: expose control-plane APIs for CI/CD integration.

## 3.2 Logical Architecture (High-Level)

1. **Client/Caller**
   - Developer workstation or CI pipeline.
   - Sends YAML-based deployment/build requests.

2. **Control Plane API Service**
   - Flask API (`src/api-service/app.py`).
   - Accepts `/build` and `/deploy` requests.
   - Clones source repositories and triggers orchestration commands.

3. **Build Subsystem**
   - BuildKit daemon (provisioned by Terraform in `01-buildkitd`).
   - Produces container images and pushes to ECR.

4. **Deployment Subsystem**
   - Deployment logic (`src/deploy/deploy.py`) + Terraform execution.
   - Uses app-specific config to generate tfvars/backend configuration.

5. **IaC Provisioning Layer**
   - Terraform entry point (`terraform/03-managed-app/main.tf`).
   - Reusable module (`terraform/modules/app-deploy`).
   - Helm chart (`charts/standard-app`) for Kubernetes manifests.

6. **Runtime Platform Services**
   - Amazon EKS (compute orchestration)
   - Amazon ECR (container registry)
   - AWS Secrets Manager (+ CSI/Secret sync path)
   - Amazon S3 (optional app storage + Terraform remote state backend)
   - IAM roles/policies for controlled access

## 3.3 Deployment Architecture (Environment View)

- **Control Namespace/Stack**
  - BuildKit service
  - API service deployment + ingress/service

- **Managed App Namespace(s)**
  - One or more standard app deployments
  - Optional PVC-backed storage
  - Optional ingress host routing
  - Secrets synchronized through configured secret provider path

## 3.4 Data and Control Flows

### Flow 1 — Build (`/build`)

1. Caller POSTs YAML build config.
2. API clones Git repository (branch-aware).
3. API invokes BuildKit build/push routine.
4. Image is pushed to ECR.
5. API returns deployment/build status.

### Flow 2 — Deploy (`/deploy`)

1. Caller POSTs YAML deploy config.
2. API validates payload and writes temporary working configuration.
3. Deployment logic generates Terraform variable and backend config.
4. Terraform init/apply executes against managed app stack.
5. Module renders Helm values and deploys standard app resources.
6. API returns deployment result.

### Flow 3 — Local Manual Deploy

1. Operator builds and pushes image via scripts in `terraform/03-managed-app`.
2. Operator generates `terraform.tfvars.json` from YAML.
3. Operator runs Terraform init/apply manually.

---

## 4. Key Design Decisions and Trade-offs

## 4.1 Centralized BuildKit

**Decision**: Use centralized BuildKit infrastructure instead of ad-hoc local builds.

**Rationale**:

- Consistent build behavior across teams/pipelines.
- Better cache reuse and faster repeated builds.
- Enables controlled build environment.

**Trade-offs**:

- Operational overhead of BuildKit lifecycle.
- Shared infrastructure introduces dependency for all builds.

## 4.2 Terraform + Helm Composition

**Decision**: Terraform orchestrates infrastructure and invokes Helm chart-based app deployment patterns.

**Rationale**:

- Terraform for cloud resources/stateful infra concerns.
- Helm for reusable Kubernetes object templating.
- Clear module boundaries and repeatable app provisioning.

**Trade-offs**:

- Two-layer abstraction can increase troubleshooting complexity.
- Requires careful version and schema compatibility management.

## 4.3 Standard App Contract

**Decision**: Define a constrained app contract (container image, env vars, secret mappings, resources, optional ingress/persistence).

**Rationale**:

- Enables low-code onboarding.
- Improves platform governance and supportability.

**Trade-offs**:

- Reduces flexibility for non-standard workloads.
- Complex apps may require extension patterns.

## 4.4 API-Driven Automation

**Decision**: Expose build/deploy orchestration over HTTP APIs.

**Rationale**:

- CI/CD-friendly integration.
- Central point for policy, logging, and orchestration.

**Trade-offs**:

- API service becomes high-value target and operational dependency.
- Must harden auth, input validation, and command execution paths.

## 4.5 Secrets via AWS Secrets Manager Integration

**Decision**: App secrets originate in AWS Secrets Manager and are consumed in Kubernetes through configured integration templates.

**Rationale**:

- Centralized secret lifecycle and auditing.
- Avoids storing plaintext secrets in manifests.

**Trade-offs**:

- Runtime dependency on secret provider components and IAM bindings.
- Failure modes require observability for secret sync/mount issues.

---

## 5. Components and Responsibilities

## 5.1 Repository Structure and Component Map

- `src/api-service/`
  - Flask control-plane API endpoints.
  - Request parsing, orchestration entry points, logging.

- `src/deploy/`
  - Deployment scripts and helper logic.
  - Build/deploy command execution and runtime integration.

- `terraform/01-buildkitd/`
  - BuildKit infrastructure provisioning.

- `terraform/02-app-deploy/`
  - Deploys control-plane application stack.

- `terraform/03-managed-app/`
  - Managed app deployment entrypoint.
  - Scripts (`gen_vars.sh`, `push_to_ecr.sh`) to support config generation/image publishing.

- `terraform/modules/app-deploy/`
  - Reusable Terraform module implementing standardized app deployment.
  - Includes IAM/secrets/S3 logic as needed.

- `charts/standard-app/`
  - Standardized Kubernetes deployment templates:
    - Deployment
    - Service
    - Ingress
    - ConfigMap
    - ServiceAccount
    - SecretProviderClass
    - PVC

## 5.2 Runtime Component Responsibilities

### Control Plane API

- Receives build/deploy requests.
- Clones source repository when needed.
- Initiates build and deployment subprocesses.
- Returns status/error response payloads.

### BuildKit Service

- Builds OCI images from provided Docker context and Dockerfile.
- Pushes images to Amazon ECR.

### Terraform Orchestrator

- Resolves backend state config.
- Applies module-driven infra changes.
- Tracks state and outputs.

### App Deploy Module

- Bridges app-level config to infrastructure resources.
- Configures IAM, secrets integration, optional S3, and Helm deployment.

### Standard App Helm Chart

- Materializes Kubernetes resources from values.
- Applies runtime security contexts, env sources, volume mounts, and exposure configuration.

---

## 6. Interfaces and Integration

## 6.1 Interface Categories

1. **Client ↔ API Service (HTTP)**
2. **API Service ↔ Git Provider (Git clone over HTTPS/SSH)**
3. **API Service ↔ BuildKit (CLI/command invocation path)**
4. **Deploy Logic ↔ Terraform (CLI orchestration)**
5. **Terraform ↔ AWS APIs (providers)**
6. **Terraform/Helm ↔ Kubernetes API Server**
7. **Pods ↔ Secrets/Storage services at runtime**

## 6.2 Integration Details

### Git Integration

- Supports HTTPS and SSH clone modes.
- HTTPS token injection mechanism is used when configured in environment.
- SSH mode currently allows non-interactive host verification bypass in command environment (requires hardening in production baselines).

### Build Integration

- Build requests carry image naming/tagging and source location details.
- Build subsystem is expected to authenticate to ECR and push artifacts.

### Deployment Integration

- Deploy requests provide application and infrastructure parameters.
- Terraform backend and variable files are generated from declarative YAML.
- Module deploys/updates Kubernetes objects through Helm templates.

### Secrets Integration

- Secret key references map app env variable names to secrets provider entries.
- Chart templates integrate with secret provider class and secret sync path.

### Persistence and Storage Integration

- Optional PVC provisioning for file-system persistence.
- Optional S3 bucket provisioning via module variables.

### Networking Integration

- Cluster-internal service always available for app port.
- Optional ingress host for external traffic routing.

---

## 7. API Specifications (Control Plane)

> Note: API behavior below is derived from repository implementation and examples. Treat this as the current implementation contract and align with code during changes.

## 7.1 Common API Characteristics

- Protocol: HTTP(S)
- Payload format: YAML request body (`Content-Type: application/yaml`)
- Response format: JSON
- Authentication: Basic auth shown in examples; exact enforcement is deployment-config dependent.
- Correlation: A short `deployment_id` is generated per request for log tracing.

## 7.2 `POST /build`

### Purpose

Build and push a container image from a source repository.

### Request (Representative)

```yaml
git_url: "https://git.example.com/org/repo.git"
git_branch: "main"
dockerfile_path: "Dockerfile"
build_context: "."
image_repository: "<account>.dkr.ecr.<region>.amazonaws.com/my-app"
image_tag: "v1.2.3"
platform: "amd64"
```

### Success Response

```json
{
  "status": "success",
  "deployment_id": "a1b2c3d4",
  "message": "Image built and pushed successfully"
}
```

### Error Behavior

- `400` when YAML body is missing/invalid.
- `500` when clone/build fails (details primarily in server logs).

## 7.3 `POST /deploy`

### Purpose

Deploy or update an application and its associated infrastructure through Terraform/module orchestration.

### Request (Representative)

```yaml
cluster_name: "eks-aiss-plfm-dev-eks-wb"
app_name: "iac-demo-app"
app_namespace: "iac-demo"
replica_count: 1
image_repository: "<account>.dkr.ecr.ap-southeast-1.amazonaws.com/iac-demo-app"
image_tag: "latest"
container_port: 8080
ingress_host: "iac-demo.eks-wb.aipo-imda.net"
env_file_path: "../demo-app/demo.env"
secrets:
  DB_PASSWORD: "app-db-password"
  API_KEY: "app-api-key"
persistence_enabled: true
s3_bucket_create: true
s3_bucket_name: "my-app-storage"
cpu_request: "200m"
memory_request: "256Mi"
cpu_limit: "1000m"
memory_limit: "1024Mi"
```

### Success Response (Typical Pattern)

```json
{
  "status": "success",
  "deployment_id": "e5f6g7h8",
  "message": "Deployment completed successfully"
}
```

### Error Behavior

- `400` for missing/invalid YAML.
- `500` for orchestration/runtime failures.

## 7.4 Operational Logging Contract

- Logs are emitted with level + deployment identifier context.
- Sensitive token masking exists in selected error paths; full-path verification and hardening is recommended.

---

## 8. Third-Party and Backing Services

## 8.1 Cloud Platform Services (AWS)

- **Amazon EKS**: Kubernetes control/data plane for workloads.
- **Amazon ECR**: Image registry for built artifacts.
- **Amazon S3**:
  - Terraform backend state storage
  - Optional application object storage
- **AWS Secrets Manager**: Source-of-truth for application secrets.
- **AWS IAM**: Access controls for deployer, workloads, and integrations.

## 8.2 Kubernetes Ecosystem Services

- **Helm**: Application packaging and templating layer.
- **Secrets Store CSI driver integration** (via chart templates): secret materialization path to pods/K8s secret.
- **Ingress controller** (environment-provided): external HTTP routing when ingress enabled.

## 8.3 Tooling and Runtime Dependencies

- **Terraform** (IaC engine)
- **Python/Flask** (control plane services)
- **Git** (source retrieval)
- **BuildKit** (container build engine)
- **Docker/OCI tooling** (image format/runtime compatibility)

## 8.4 Source Control and CI/CD Providers

- Git repositories over HTTPS/SSH.
- CI/CD systems can call control-plane APIs for automated workflows.

---

## 9. Security Architecture Considerations

## 9.1 Security Controls Present

- Non-root pod execution baseline in deployment templates.
- Capability drop defaults unless privileged mode is explicitly enabled.
- Secret references externalized from manifest literals.
- Segregated service account and optional IAM integration patterns.

## 9.2 Security Risks and Mitigations

1. **Git auth/token handling in clone workflows**
   - Risk: credential exposure in command traces/errors.
   - Mitigation: enforce strict redaction, avoid URL-embedded tokens where possible, prefer short-lived credentials.

2. **SSH host key verification bypass**
   - Risk: MITM exposure during clone.
   - Mitigation: pre-seed known_hosts and enable strict checking in production.

3. **Broad deployment privileges**
   - Risk: compromise blast radius.
   - Mitigation: least-privilege IAM/K8s RBAC per environment and namespace.

4. **API endpoint exposure**
   - Risk: unauthorized deployment triggers.
   - Mitigation: strong authN/authZ, IP restrictions/private ingress, rate limiting, audit logging.

5. **Secrets sync/runtime failure visibility**
   - Risk: silent startup/runtime failures.
   - Mitigation: explicit readiness checks and alerts for secret mount/sync errors.

---

## 10. Reliability, Scalability, and Operations

## 10.1 Reliability Patterns

- Declarative, idempotent deployment semantics via Terraform/Helm.
- Stateful IaC through remote backend.
- Ephemeral work directories for API-initiated operations.

## 10.2 Scalability Considerations

- Build throughput tied to BuildKit capacity and shared usage patterns.
- API service may require horizontal scaling and queueing for concurrent deployments.
- Namespace/resource quotas recommended for multi-tenant managed app usage.

## 10.3 Observability and Auditability

- Deployment ID-based logs in API service.
- Terraform plan/apply outputs for change auditing.
- Cloud-native logging/metrics/alerting should be integrated at environment level.

## 10.4 Operational Runbook Anchors

- Control-plane provisioning order:
  1. BuildKit
  2. API image
  3. API service
- Managed app deployment options:
  - local scripts + Terraform
  - API-triggered remote orchestration

---

## 11. Configuration and Environment Model

## 11.1 Core Configuration Domains

- **Build config**: Git source, Dockerfile, context, image repo/tag/platform.
- **Deployment config**: namespace, replicas, ports, ingress host, resources.
- **Secrets config**: env var key → secret reference mapping.
- **Storage config**: PVC enablement/mount path, optional S3 bucket settings.
- **Terraform backend config**: state bucket/key/region/profile conventions per environment.

## 11.2 Environment Separation

- Backend files (`*.tfbackend`) and variable files (`*.tfvars`) provide environment-specific separation.
- Recommend clear dev/stage/prod isolation for:
  - state backends
  - namespaces/accounts
  - IAM roles
  - ingress domains/certificates

---

## 12. Known Constraints and Future Enhancements

## 12.1 Current Constraints

- API contract is YAML-over-HTTP; schema validation appears limited.
- Control-plane operations are command orchestration heavy and require strong runtime controls.
- Mixed legacy/supporting files can cause ambiguity for new adopters.

## 12.2 Recommended Enhancements

1. **Formal API schema**
   - Add OpenAPI spec and strict request validation.

2. **Security hardening**
   - Remove SSH host verification bypass.
   - Replace URL token patterns with safer credential helpers.

3. **Deployment workflow robustness**
   - Introduce async job model with status endpoint/webhooks.
   - Add retries/backoff/circuit-breaking around external dependencies.

4. **Policy and compliance controls**
   - Integrate policy checks (e.g., IaC/K8s admission policies) before apply.

5. **Observability maturity**
   - Structured logs, metrics, traces, and deployment SLO dashboards.

6. **Contracted extension model**
   - Define plugin/extensions for non-standard apps while preserving baseline controls.

---

## 13. Appendix A — Representative End-to-End Sequence

1. CI calls `POST /build` with repo/image metadata.
2. API clones repo and invokes BuildKit.
3. BuildKit pushes image to ECR.
4. CI calls `POST /deploy` with app + infra configuration.
5. API generates working deploy config and invokes deployment logic.
6. Terraform applies module resources and Helm chart.
7. EKS schedules pods; app reads env/secrets and serves traffic.
8. Ingress routes external requests when enabled.

---

## 14. Appendix B — Primary Repository Artifacts

- `README.md`
- `src/api-service/app.py`
- `src/deploy/deploy.py`
- `terraform/01-buildkitd/*`
- `terraform/02-app-deploy/*`
- `terraform/03-managed-app/*`
- `terraform/modules/app-deploy/*`
- `charts/standard-app/*`

These files should be treated as the implementation source of truth. Keep this document synchronized with code-level changes.
