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
Install [ollama](https://ollama.com/) on your local machine. Ollama is a Language Model as a Service (LMaaS) that provides a RESTful API for interacting with large language models. It's a great way to get started with LLMs without having to worry about the infrastructure.



## Pull the LLM models

The following two LLM models are used in the demo:
- LLaVa (Large Language and Vision Assistant)
- Llama (Large Language Model Meta AI) 3.2

Pull the two models using the ollama cli:

```sh
ollama pull llama3.2
ollama pull llava
```

## Install Istio ambient and enroll all the apps to Istio ambient

We use [Istio](https://istio.io) to secure, observe and control the traffic among the microservices in the cluster.

```sh
./install-istio.sh
```

## Deploy all Istio policies

```sh
kubectl apply -f policy/
```

## Access the demo app

Use port-forwarding to help us access the demo app via Istio ingress gateway:

```sh
kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80
```

To access the demo app, open your browser and navigate to [http://localhost:8080](http://localhost:8080)

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

