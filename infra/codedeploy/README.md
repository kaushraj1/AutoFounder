# CodeDeploy blue/green (AF-022)

## Current state

- **CI** (`backend-ci.yml`, `lint.yml`, `terraform-validate.yml`) — ✅ done.
- **CD** (`deploy-staging.yml` → UAT, `deploy-prod.yml` → prod) — ✅ functional: builds + pushes the image to the shared ECR repo (`autofounder-ai/backend`) and does a **rolling ECS deploy** to the Terraform-created cluster/service (`autofounder-ai-{env}-cluster` / service `backend`). The ECS service's **deployment circuit breaker** (AF-013) auto-rolls-back a failed deploy.
- Names now match the Terraform resources (the old `autofounderai-*` hardcoding is gone), and the ECR registry is derived from the ECR-login step (no `ECR_REGISTRY` secret).

## Blue/green canary — activation steps (focused follow-up, needs an AWS apply-test)

The rolling deploy above is safe (auto-rollback). True CodeDeploy blue/green canary (deployment.md) is the enhancement. To activate:

1. **Terraform** — add a green target group per service in `modules/alb`, set the ECS service `deployment_controller { type = "CODE_DEPLOY" }` (drop the circuit breaker, add `lifecycle.ignore_changes = [task_definition, load_balancer, desired_count]`), and add a `codedeploy` module: `aws_codedeploy_app` (compute_platform ECS) + `aws_codedeploy_deployment_group` (blue/green, `CodeDeployDefault.ECSCanary10Percent5Minutes`, the prod listener + blue/green TG pair, auto-rollback) + the `AWSCodeDeployRoleForECS` IAM role. Gate behind `enable_blue_green` and set it in `env/production.tfvars`. **Apply-test in a real account** (the listener/TG swap can't be validated offline).
2. **Workflow** — switch `deploy-prod.yml`'s deploy step to the CodeDeploy inputs on `amazon-ecs-deploy-task-definition`:
   ```yaml
   codedeploy-appspec: infra/codedeploy/appspec.yaml
   codedeploy-application: autofounder-ai-production
   codedeploy-deployment-group: backend
   ```
3. Optionally wire `BeforeAllowTraffic`/`AfterAllowTraffic` smoke-test Lambdas in `appspec.yaml`.

## Files
- `appspec.yaml` — CodeDeploy ECS AppSpec (TargetService + LoadBalancerInfo).
- `taskdef.json` — task-definition template for the render step.
