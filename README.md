# kGPT

**A modern multi-agent documentation assistant for Kafka and Confluent**

kGPT is an AI-powered chatbot that helps you navigate Kafka and Confluent documentation, with the ability to connect to your live Kafka clusters for context-aware answers.

## Features

- **Multi-Agent Architecture**: Uses LangGraph to orchestrate specialized agents for routing, retrieval, validation, and synthesis
- **Multiple LLM Providers**: Support for OpenRouter, OpenAI, Anthropic, and Ollama (local) via LiteLLM
- **Bring Your Own Docs**: Index custom documentation from sitemaps, GitHub repos, URLs, or file uploads
- **Kafka Cluster Integration**: Connect to your clusters for context-aware answers about topics, configs, and consumer groups
- **Demo Mode**: Optional demo Kafka cluster with sample topics and events
- **Modern Stack**: FastAPI backend + Svelte 5 frontend with Tailwind CSS

## Quick Start

### Option 1: Docker (Production)

```bash
git clone https://github.com/mvfolino68/kGPT.git
cd kGPT
docker compose up
```

Open <http://localhost:3000> and configure your LLM provider in Settings.

### Option 2: Development Mode (Recommended for Contributors)

```bash
git clone https://github.com/mvfolino68/kGPT.git
cd kGPT

# Install dependencies
make install

# Start development environment (hot-reload enabled)
make dev
```

Open <http://localhost:5173> (frontend) and <http://localhost:8000/docs> (API).

**Development mode is much faster** - code changes reload instantly without rebuilding Docker images.

### Docker Options

| Command | What Starts | Use Case |
|---------|-------------|----------|
| `docker compose up` | Frontend + Backend + Qdrant | Quick start with cloud LLM |
| `docker compose --profile ollama up` | + Ollama | Local LLM, no API key |
| `docker compose --profile demo up` | + Kafka demo | Test Kafka features |
| `docker compose --profile ollama --profile demo up` | Everything | Full demo experience |

### Make Commands (Development)

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies |
| `make dev` | Start full dev environment with hot-reload |
| `make dev-infra` | Start only infrastructure (Qdrant) |
| `make dev-backend` | Start backend with hot-reload |
| `make dev-frontend` | Start frontend with hot-reload |
| `make lint` | Run linters |
| `make test` | Run tests |
| `make build` | Build Docker images |

Run `make help` for the full list.

### Access Points

| Mode | Frontend | API Docs |
|------|----------|----------|
| **Development** | <http://localhost:5173> | <http://localhost:8000/docs> |
| **Docker** | <http://localhost:3000> | <http://localhost:8000/docs> |

## Usage

### First-Time Setup

1. **Start the app** (either `make dev` or `docker compose up`)
2. **Open the frontend** in your browser
3. **Go to Settings** and configure your LLM provider:
   - Enter your API key (OpenAI, Anthropic, or OpenRouter)
   - Or select Ollama for local inference
4. **Start chatting!**

### Adding Documentation Sources

1. Go to the **Documents** page
2. Use quick presets (Confluent Docs, Apache Kafka Docs) or add custom sources:
   - Sitemap URL (e.g., `https://docs.confluent.io/home/sitemap.xml`)
   - GitHub repository URL
3. Click **Start Indexing** and watch the progress

**Note**: Large documentation sites (like Confluent) can take 10-30 minutes to fully index. You'll see real-time progress including:

- Current stage (fetching, loading, chunking, embedding)
- Pages loaded and chunks created
- Elapsed time

### Connecting a Kafka Cluster

#### Demo Mode

If you started with `--profile demo`:

1. Go to the **Cluster** page
2. Click **"Connect Demo Cluster"**
3. Explore demo topics: `orders`, `users`, `inventory`, `payments`, `notifications`

#### Your Own Cluster

1. Go to the **Cluster** page
2. Enter your cluster details:
   - Bootstrap servers, Security protocol
   - SASL credentials (if required)
3. Click **"Connect"**

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Svelte 5 Frontend                         │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐      │
│  │  Chat   │  │Documents │  │ Cluster │  │ Settings │      │
│  └────┬────┘  └────┬─────┘  └────┬────┘  └────┬─────┘      │
└───────┼────────────┼─────────────┼────────────┼─────────────┘
        │            │             │            │
        ▼            ▼             ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  /api/chat    /api/documents   /api/cluster   /api/settings │
└───────┼────────────┼─────────────┼────────────┼─────────────┘
        │            │             │            │
        ▼            │             │            │
┌─────────────────────────────────────────────────────────────┐
│                Multi-Agent System (LangGraph)                │
│  ┌────────┐   ┌───────────┐   ┌────────────┐   ┌─────────┐ │
│  │ Router │──▶│ Retrieval │──▶│ Validation │──▶│Synthesis│ │
│  └────┬───┘   └───────────┘   └────────────┘   └─────────┘ │
│       │                                              ▲      │
│       ▼                                              │      │
│  ┌─────────────┐                                     │      │
│  │ Kafka Agent │─────────────────────────────────────┘      │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
        │                                       │
        ▼                                       ▼
┌───────────────┐                     ┌────────────────┐
│    Qdrant     │                     │  LLM Provider  │
│ (Vector Store)│                     │ OpenAI/Claude/ │
└───────────────┘                     │    Ollama      │
                                      └────────────────┘
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider: `openai`, `anthropic`, `openrouter`, `ollama` |
| `LLM_MODEL` | `gpt-4o` | Default LLM model |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `OPENROUTER_API_KEY` | - | OpenRouter API key (access all models) |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant server URL |
| `EMBEDDING_PROVIDER` | `fastembed` | Embedding provider: `fastembed`, `openai`, `ollama`, `cohere` |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model name |

See [`.env.example`](.env.example) for all available options.

### UI Configuration

All settings can be configured through the **Settings** page in the UI - no environment variables required!

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed setup, testing, and contribution guidelines.

### Quick Reference

```bash
# Install everything
make install

# Start dev environment (hot-reload)
make dev

# Run linters
make lint
make lint-fix

# Run tests
make test

# Build Docker images
make build
```

## Project Structure

```
kgpt/
├── Makefile                 # Development commands
├── docker-compose.yml       # Production Docker stack
├── docker-compose.dev.yml   # Development infrastructure
├── pyproject.toml           # Backend dependencies
├── frontend/                # Svelte 5 + Tailwind CSS
│   └── src/
│       ├── routes/          # Pages (chat, documents, cluster, settings)
│       └── lib/api.ts       # Backend API client
└── src/kgpt/
    ├── api/                 # FastAPI routes
    ├── agents/              # LangGraph multi-agent system
    ├── ingestion/           # Document loaders (sitemap, github)
    ├── vectorstore/         # Qdrant integration
    ├── llm/                 # LLM providers
    └── db/                  # SQLite persistence
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built with [LangChain](https://langchain.com/), [LangGraph](https://langchain-ai.github.io/langgraph/), [FastAPI](https://fastapi.tiangolo.com/), and [SvelteKit](https://kit.svelte.dev/)
- UI powered by [Tailwind CSS](https://tailwindcss.com/)
- Vector search powered by [Qdrant](https://qdrant.tech/)
- Local LLM support via [Ollama](https://ollama.ai/)

---

**Made by [Michael Folino](https://www.linkedin.com/in/mfolino/)** | [Twitter](https://twitter.com/mvfolino68) | [GitHub](https://github.com/mvfolino68/kGPT)
