# Kubernetes GitHub Integration Setup

This guide explains how to deploy the demo application to Kubernetes with GitHub integration and automatic binary image conversion.

## 🔐 GitHub Token Secret Setup

### Method 1: Using kubectl (Recommended)

```bash
# 1. Generate GitHub Personal Access Token
# Go to: https://github.com/settings/tokens
# Scope needed: "repo" (full repository access)

# 2. Create the secret directly with kubectl
kubectl create secret generic github-secret \
  --from-literal=token="ghp_your_actual_token_here" \
  --namespace=default

# 3. Verify the secret was created
kubectl get secrets github-secret
kubectl describe secret github-secret
```

## 🚀 Deployment

### 1. Deploy the Application

```bash
# Apply the deployment with GitHub integration
kubectl apply -f kubernetes/demo.yaml

# Check deployment status
kubectl get deployments demo
kubectl get pods -l app=demo

# View logs to verify GitHub integration
kubectl logs -l app=demo --follow
```

### 2. Environment Variables Configured

The deployment automatically sets:

| Variable | Value | Purpose |
|----------|--------|---------|
| `GITHUB_MCP_SERVER_URL` | `http://agentgateway.mcp.svc.cluster.local:3000/mcp` | GitHub MCP server endpoint |
| `EVENT_NAME` | `apidays-paris-2025` | Default event name for branch/folder |
| `GITHUB_REPO` | `gen-ai-demo` | Target repository name |
| `GITHUB_TOKEN` | From `github-secret` | Authentication for binary conversion |

### 3. Customize Configuration (Optional)

Edit the deployment environment variables in `kubernetes/demo.yaml`:

```yaml
env:
  # Customize these values as needed
  - name: GITHUB_MCP_SERVER_URL
    value: "http://your-mcp-server:3000/mcp"
  - name: EVENT_NAME
    value: "your-event-name"
  - name: GITHUB_REPO
    value: "your-repo-name"
```

## 🔍 Verification

### 1. Check Application Health

```bash
# View application logs
kubectl logs -l app=demo

# Check if GitHub integration is working
kubectl logs -l app=demo | grep -i github

# Port-forward to test locally (optional)
kubectl port-forward service/demo 8080:80
# Then access: http://localhost:8080
```

### 2. Test GitHub Integration

1. Access the engagement analysis page in the app
2. Complete an image analysis
3. Check the logs for GitHub integration messages:
   ```
   ✅ GitHub MCP: Connected
   🔄 Converting to binary format
   ✅ Successfully converted to binary image
   ```

### 3. Verify Binary Conversion

After analysis completion:
- Check the GitHub repository for the new branch
- Verify images display properly (not as base64 text)
- Test raw image URLs load correctly

## 🛠️ Troubleshooting

### Secret Issues

```bash
# Check if secret exists
kubectl get secrets github-secret

# View secret details (base64 encoded)
kubectl get secret github-secret -o yaml

# Test token validity (decode and verify)
kubectl get secret github-secret -o jsonpath='{.data.token}' | base64 -d
```

### Deployment Issues

```bash
# Check deployment status
kubectl describe deployment demo

# Check pod events
kubectl describe pod -l app=demo

# View detailed logs
kubectl logs -l app=demo --previous  # Previous container logs
kubectl logs -l app=demo --follow    # Live logs
```

### GitHub Integration Issues

```bash
# Check for GitHub-related errors in logs
kubectl logs -l app=demo | grep -E "(github|GitHub|mcp)"

# Verify MCP server connectivity
kubectl exec -it deployment/demo -- curl -s http://agentgateway.mcp.svc.cluster.local:3000/health
```

## 🔄 Updates

### Update GitHub Token

```bash
# Method 1: Update existing secret
kubectl patch secret github-secret -p='{"data":{"token":"'$(echo -n "ghp_new_token_here" | base64)'"}}'
```

### Update Application

```bash
# Update deployment with new image version
kubectl set image deployment/demo demo=docker.io/linsun/demo:v5

# Or apply updated YAML
kubectl apply -f kubernetes/demo.yaml

# Check rollout status
kubectl rollout status deployment/demo
```

## 🔒 Security Best Practices

1. **Token Permissions:** Use minimum required GitHub token scopes (`repo` only)
2. **Secret Management:** Never commit secrets to version control
3. **Access Control:** Use Kubernetes RBAC to limit secret access
4. **Rotation:** Regularly rotate GitHub tokens
5. **Monitoring:** Monitor secret usage and access logs

## 📋 Complete Setup Checklist

- [ ] GitHub Personal Access Token created with `repo` scope
- [ ] Kubernetes secret `github-secret` created with token
- [ ] Environment variables configured in `demo.yaml`
- [ ] Application deployed successfully  
- [ ] GitHub MCP server accessible from cluster
- [ ] Binary image conversion tested and working
- [ ] Application logs show successful GitHub integration

Your Kubernetes deployment now supports automatic binary image conversion with secure token management! 🎉
