# Law Vector Service

Micro-serviço para ingestão, vetorização e sumarização de documentos legais (por exemplo, resoluções de emendas de leis) usando LangChain e PostgreSQL/pgvector.

---

## 📝 Descrição

Este projeto fornece uma API RESTful para:

* **Ingestão de documentos** (PDF, TXT).
* **Divisão** dos documentos em *chunks* (configuráveis).
* **Geração de embeddings** via OpenAI e armazenamento em PostgreSQL com extensão `pgvector`.
* **Busca semântica** por similaridade de embeddings.
* **Sumarização** de documentos completos usando cadeias *map-reduce* do LangChain.

Ideal para sistemas de Retrieval-Augmented Generation (RAG) e análise de grandes documentos jurídicos.

---

## 🚀 Funcionalidades

* **Upload e indexação**: endpoint `POST /api/upload` recebe arquivo e indexa seus *chunks*.
* **Busca semântica**: endpoint `GET /api/search?query=...&k=...` retorna os *chunks* mais relevantes.
* **Sumarização**: endpoint `GET /api/summarize` gera e devolve o resumo de todos os *chunks* indexados.
* **Configuração via ENV**: todas as variáveis (chave OpenAI, conexão com o banco, tamanhos de *chunk*) são definidas em `.env`.
* **Containerização**: suporte a Docker e Docker Compose para rápido deploy local.

---

## 📂 Estrutura do Projeto

```
my-law-vector-service/
├── README.md
├── pyproject.toml          # Dependências e metadata do projeto
├── .env.example            # Variáveis de ambiente de exemplo
├── Dockerfile              # Definição da imagem Docker
├── docker-compose.yml      # Compose para app + Postgres/pgvector
│
├── config/
│   └── default.json        # Configurações padrão (chunk size, etc.)
│
├── src/
│   └── app/
│       ├── main.py         # Entrypoint FastAPI
│       ├── api/
│       │   └── routes.py   # Definição dos endpoints
│       ├── core/
│       │   ├── config.py   # Leitura de ENV/config
│       │   └── logger.py   # Configuração de logs
│       ├── db/
│       │   ├── session.py  # Session factory SQLAlchemy
│       │   └── models.py   # Models do pgvector
│       ├── ingestion/
│       │   ├── loader.py   # Carregamento de arquivos
│       │   └── splitter.py # Divisão de texto em chunks
│       ├── vectorization/
│       │   └── vector_store.py  # Integração LangChain + PGVector
│       └── summarization/
│           └── summarizer.py    # Cadeias de sumarização
│
├── scripts/
│   ├── init_db.py          # Cria extensão e tabelas iniciais
│   ├── seed_data.py        # Insere dados de exemplo
│   └── clean_collections.py# Limpa coleções vetoriais
│
├── tests/                  # Testes unitários e de integração
│   └── ...
└── scripts/
    ├── run_local.sh        # Script para rodar localmente
    └── migrate.sh          # Rodar migrações (Alembic)
```

---

## ⚙️ Instalação

1. Clone o repositório:

   ```bash
   git clone https://github.com/seu-usuario/my-law-vector-service.git
   cd my-law-vector-service
   ```
2. Crie o arquivo de variáveis de ambiente:

   ```bash
   cp .env.example .env
   ```

   Preencha `OPENAI_API_KEY`, `DATABASE_URL`, `VECTOR_COLLECTION_NAME`, `CHUNK_SIZE` e `CHUNK_OVERLAP`.
3. Instale dependências:

   ```bash
   pip install -r requirements.txt
   ```
4. Suba serviços com Docker Compose:

   ```bash
   docker-compose up -d
   ```
5. Inicialize o banco de dados:

   ```bash
   python src/app/scripts/init_db.py
   ```
6. Execute localmente:

   ```bash
   bash scripts/run_local.sh
   ```
7. Acesse a documentação interativa em `http://localhost:8000/docs`.

---

## 🧪 Testes

Execute todos os testes com:

```bash
pytest --cov=src
```

---

## 🚢 Deploy

Para produção, ajuste `DATABASE_URL` para seu Postgres gerenciado (Supabase, RDS etc.), habilite SSL e configure variáveis de ambiente seguras.

---

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
