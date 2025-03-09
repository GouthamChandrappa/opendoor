# Project Structure
```bash
door_installation_assistant/
├── config/
│   ├── __init__.py
│   ├── app_config.py          # Main configuration settings
│   ├── logging_config.py      # Logging configuration
│   └── model_config.py        # LLM and embedding model configurations
├── data_processing/
│   ├── __init__.py
│   ├── document_processor.py  # Document processing and extraction
│   ├── chunking_strategies.py # Different chunking approaches
│   └── embedding_generator.py # Generate embeddings for documents
├── vector_storage/
│   ├── __init__.py
│   ├── qdrant_store.py        # Qdrant implementation
├── retrieval/
│   ├── __init__.py
│   ├── retrieval_pipeline.py  # Orchestrates the retrieval process
│   ├── bm25_retriever.py      # BM25 sparse retrieval
│   ├── vector_retriever.py    # Dense vector retrieval
│   └── reranker.py            # Reranking logic
├── llm_integration/
│   ├── __init__.py
│   ├── llm_manager.py         # LLM interaction management
│   ├── prompt_templates.py    # Prompt engineering
│   └── response_formatter.py  # Format LLM responses
├── agent_system/
│   ├── __init__.py
│   ├── agent_factory.py       # Creates specific agents
│   ├── agent_orchestrator.py  # Manages agent collaboration
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py      # Base agent class
│   │   ├── door_identifier.py # Identifies door type
│   │   ├── procedure_agent.py # Provides installation steps
│   │   ├── tool_agent.py      # Tool and component recommendations
│   │   ├── troubleshoot_agent.py # Troubleshooting assistance
│   │   └── safety_agent.py    # Safety guidance
│   └── memory/
│       ├── __init__.py
│       └── conversation_memory.py # Maintains conversation context
├── evaluation/
│   ├── __init__.py
│   ├── evaluator.py           # Evaluation orchestration
│   ├── metrics.py             # Custom evaluation metrics
│   └── synthetic_scenarios.py # Test case generation
├── api/
│   ├── __init__.py
│   ├── main.py                # FastAPI entry point
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat endpoints
│   │   ├── search.py          # Search endpoints
│   │   └── feedback.py        # Feedback collection
│   └── middleware/
│       ├── __init__.py
│       └── auth.py            # Authentication middleware
├── utils/
│   ├── __init__.py
│   ├── file_utils.py          # File handling utilities
│   ├── text_utils.py          # Text processing utilities
│   └── logging_utils.py       # Logging utilities
├── scripts/
│   ├── ingest_documents.py    # Document ingestion script
│   ├── evaluate_system.py     # Run evaluation tests
│   └── setup_vector_store.py  # Initialize vector store
├── main.py                    # Application entry point
├── requirements.txt           # Dependencies
├── docker-compose.yml         # Docker setup
├── Dockerfile                 # Docker image definition
└── README.md                  # Project documentation
├── web_ui/
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   ├── chat.css
│   │   │   └── components.css
│   │   ├── js/
│   │   │   ├── api.js
│   │   │   ├── chat.js
│   │   │   ├── search.js
│   │   │   ├── upload.js
│   │   │   └── utils.js
│   │   └── img/
│   │       ├── logo.svg
│   │       ├── icon-door.svg
│   │       ├── icon-tool.svg
│   │       └── icon-safety.svg
│   ├── templates/
│   │   ├── index.html
│   │   ├── chat.html
│   │   ├── search.html
│   │   └── components/
│   │       ├── header.html
│   │       ├── footer.html
│   │       ├── chat-window.html
│   │       ├── search-results.html
│   │       └── upload-form.html
│   └── server.py  # Simple server to serve the UI (using Flask)
```
# Architecture
```bash
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Installation   │────▶│  Vector         │────▶│  Field Support  │
│  Document       │     │  Storage        │     │  Agent          │
│  Processing     │     │                 │     │  Orchestration  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                      │
        │                        │                      │
        ▼                        ▼                      ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Installation   │◀───▶│  LLM            │◀───▶│  Field Support  │
│  Retrieval      │     │  Integration    │     │  Evaluation     │
│  Pipeline       │     │                 │     │  Framework      │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                │
                                ▼
                        ┌─────────────────┐
                        │                 │
                        │  Mobile-First   │
                        │  Field          │
                        │  Interface      │
                        │                 │
                        └─────────────────┘

```