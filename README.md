# gen-ai-demo
Gen AI Demo with Kubernetes, Istio Ambient, Prometheus, Kiali etc

## Prerequisites

- A Kubernetes cluster, for example a [kind](https://kind.sigs.k8s.io/) cluster.
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)

## Startup

We have crafted a few scripts to make this demo run as quickly as possible on your machine once you've installed the prerequisites.

This script will:

- Create a kind cluster
- Install a simple curl client, an [ollama](https://ollama.com/) service and the demo service.
  - Ollama is a Language Model as a Service (LMaaS) that provides a RESTful API for interacting with large language models. It's a great way to get started with LLMs without having to worry about the infrastructure.

```sh
./startup.sh
```

## Pull the LLM models

The following two LLM models are used in the demo:
- LLaVa (Large Language and Vision Assistant)
- Llama (Large Language Model Meta AI) 3.2

Pull the two models:

```sh
kubectl exec -it deploy/client -- curl http://ollama.ollama:80/api/pull -d '{"name": "llama3.2"}'
kubectl exec -it deploy/client -- curl http://ollama.ollama:80/api/pull -d '{"name": "llava"}'
kubectl exec -it deploy/client -- curl http://ollama.ollama:80/api/pull -d '{"name": "deepseek-r1"}'
```

## Install Istio ambient and enroll all the apps to Istio ambient

We use [Istio](https://istio.io) to secure, observe and control the traffic among the microservices in the cluster.

```sh
./install-istio.sh
```

## Access the demo app

Use port-forwarding to help us access the demo app:

```sh
kubectl port-forward svc/demo 8001:8001
```

To access the demo app, open your browser and navigate to [http://localhost:8001](http://localhost:8001)

## Google Slides Integration 📊

Voice-activated presentation creation! Say "Create slides for Tokyo" in the Voice with Llama app.

- Configure your MCP server URL: `export MCP_SERVER_URL="http://agentgw.mcp.svc.cluster.local:3000/mcp"`
- See [GOOGLE_SLIDES_SETUP.md](GOOGLE_SLIDES_SETUP.md) for setup details

## Engagement Analysis GitHub Integration 📸

The Engagement Analysis app automatically stores analysis results and images to GitHub using the GitHub MCP server.

### Quick Setup
```bash
export EVENT_NAME="your-event-name"
export GITHUB_MCP_SERVER_URL="http://your-github-mcp-server:port/mcp"
export GITHUB_REPO="gen-ai-demo"
```

### Features
- 📷 **Dual Camera Analysis** - Compare engagement levels between two images
- 🤖 **AI-Powered Analysis** - Uses LLaVa for detailed engagement assessment  
- 🌿 **Auto Branch Creation** - Creates event-specific GitHub branches
- 📁 **Organized Storage** - Stores in `events/{EVENT_NAME}/` folder structure
- 📄 **Complete Reports** - Generates markdown analysis reports
- 🔗 **Direct Links** - Provides immediate GitHub links to results

See [ENGAGEMENT_ANALYSIS_GITHUB_SETUP.md](ENGAGEMENT_ANALYSIS_GITHUB_SETUP.md) for complete setup instructions.

### Kubernetes Deployment with GitHub Integration

For production Kubernetes deployments with secure GitHub token management:

```bash
# 1. Create GitHub secret (replace with your token)
kubectl create secret generic github-secret \
  --from-literal=token="ghp_your_github_token_here"

# 2. Deploy application with GitHub integration  
kubectl apply -f kubernetes/demo.yaml

# 3. Verify deployment
kubectl logs -l app=demo | grep -i github
```

See [KUBERNETES_GITHUB_SETUP.md](KUBERNETES_GITHUB_SETUP.md) for detailed Kubernetes setup with security best practices.

## Cleanup

To clean up the demo, run the following command:
```sh
./cleanup-istio.sh
./shutdown.sh
```

## Operating System Information

This demo has been tested on the following operating systems and will work if you have the prerequisites installed. You may need to build the demo app images yourself if you are on a different platform.

- macOS M2

## Credits
A portion of the demo in this repo was inspired by the [github.com/cncf/llm-in-action](github.com/cncf/llm-in-action) repo.

