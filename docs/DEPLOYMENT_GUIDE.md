# ECCRP Deployment Guide

## Local Development (Docker Compose)

```bash
# 1. Clone and configure
git clone https://github.com/your-org/eccrp.git
cd eccrp
cp backend/.env.example backend/.env
# Edit backend/.env — set OPENAI_API_KEY at minimum

# 2. Start all services
docker-compose up -d

# 3. Wait ~60s for services to initialize, then check
curl http://localhost:8000/health

# 4. Open frontend
open http://localhost:3000
# API docs
open http://localhost:8000/api/v1/docs
```

## Production Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.28+)
- cert-manager installed
- Nginx Ingress Controller
- PostgreSQL RDS or managed instance
- Redis Elasticache or managed instance
- OpenSearch managed cluster

### Deploy

```bash
# 1. Build and push images
docker build -t your-registry/eccrp-backend:v1.0.0 \
  -f infrastructure/docker/Dockerfile.backend backend/
docker push your-registry/eccrp-backend:v1.0.0

docker build -t your-registry/eccrp-frontend:v1.0.0 \
  -f infrastructure/docker/Dockerfile.frontend frontend/
docker push your-registry/eccrp-frontend:v1.0.0

# 2. Update image references in k8s manifests
sed -i 's|ghcr.io/eccrp/backend:latest|your-registry/eccrp-backend:v1.0.0|g' \
  infrastructure/k8s/base/deployment.yaml

# 3. Create namespace and secrets
kubectl create namespace eccrp
kubectl create secret generic eccrp-secrets -n eccrp \
  --from-literal=database-url="postgresql+asyncpg://user:pass@host:5432/eccrp" \
  --from-literal=redis-url="redis://host:6379/0" \
  --from-literal=jwt-secret-key="$(openssl rand -base64 64)" \
  --from-literal=openai-api-key="sk-your-key"

# 4. Apply manifests
kubectl apply -f infrastructure/k8s/base/deployment.yaml

# 5. Run migrations (one-time job)
kubectl run eccrp-migrate --image=your-registry/eccrp-backend:v1.0.0 \
  --restart=Never -n eccrp \
  --env="DATABASE_URL=postgresql+asyncpg://..." \
  -- alembic upgrade head

# 6. Verify
kubectl get pods -n eccrp
kubectl logs -f deployment/eccrp-backend -n eccrp
```

### Health Checks

```bash
# Backend
curl https://api.eccrp.in/health
curl https://api.eccrp.in/readiness

# Frontend
curl https://eccrp.in

# Database connectivity
kubectl exec -it deployment/eccrp-backend -n eccrp -- \
  python -c "from app.core.health import check_database; import asyncio; print(asyncio.run(check_database()))"
```

## Post-Deployment Setup

```bash
# Register admin user
curl -X POST https://api.eccrp.in/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@eccrp.in","password":"YourSecurePass@123","full_name":"Platform Admin","role":"super_admin"}'

# Get token
TOKEN=$(curl -s -X POST https://api.eccrp.in/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@eccrp.in","password":"YourSecurePass@123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Seed judgment database
curl -X POST https://api.eccrp.in/api/v1/admin/seed/judgments \
  -H "Authorization: Bearer $TOKEN"

# Initialize OpenSearch indices and ingest legal corpus
curl -X POST https://api.eccrp.in/api/v1/admin/ingest/legal-corpus \
  -H "Authorization: Bearer $TOKEN"
```

## Scaling

```bash
# Scale backend
kubectl scale deployment eccrp-backend --replicas=5 -n eccrp

# Check HPA status
kubectl get hpa -n eccrp
```

## Monitoring

- **Prometheus**: https://prometheus.eccrp.in
- **Grafana**: https://grafana.eccrp.in (admin / set in env)
- Key dashboards: API latency, DB connections, AI query performance, error rates

## Backup

```bash
# PostgreSQL backup
pg_dump -h your-rds-endpoint -U eccrp eccrp | gzip > eccrp_$(date +%Y%m%d).sql.gz

# Upload to S3
aws s3 cp eccrp_$(date +%Y%m%d).sql.gz s3://eccrp-backups/

# Automated: set up RDS automated backups (7-35 day retention)
```
