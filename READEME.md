# 📈 ChainFeed

**ChainFeed** is a robust, modular options chain ingestion and inspection system. Designed to support live, historical, and synthetic data providers, it's built for reliability, extensibility, and integration with FatTail strategies.

## ⚡ Quick Start

```bash
git clone https://github.com/yourorg/ChainFeed.git
cd ChainFeed
make test
```

---

## 🧩 Project Structure
<pre lang="text"><code>````text
ChainFeed/
├── cli/                    # Command-line interfaces (e.g., expiration tools)
├── core/
│   └── providers/          # Snapshot providers (live, historical, synthetic)
├── data/                   # Local JSON chain files (e.g., formatted.json)
├── test/                   # Unit and integration tests
├── utils/                  # Support modules (e.g., expiration inspector)
├── requirements.txt        # Python dependencies
├── README.md               # You're here
````</code></pre>

---

## ⚙️ Setup

### 1. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
### 3. Set environment variables
```bash
export POLYGON_API_KEY=your_api_key_here
```
For convenience, you can place this in your .zshrc, .bashrc, or use a .env loader.

⸻

## 🚀 Usage

### Expiration Summary CLI
```bash
PYTHONPATH=. python3 cli/expiration_cli.py --symbol SPX --summary
```
Additional CLI tools are located in the cli/ directory.

⸻

## 🧪 Running Tests

From the project root:
```bash
PYTHONPATH=. pytest test
```

This runs the full test suite, validating:
- Expiration logic
- Chain normalization
- Provider behavior (live, historical, synthetic)

No assumptions. No special scripts. Just Python.

⸻

## 📦 Providers

ChainFeed supports pluggable snapshot sources:

- ✅ **LiveSnapshotProvider** – fetches current options chains from Polygon  
- ✅ **HistoricalSnapshotProvider** – uses Polygon’s `as_of` parameter  
- ✅ **SyntheticSnapshotProvider** – generates mock options for development/testing

To extend with new providers, implement the ChainSnapshotProvider interface in core/providers/.

⸻

## 🔒 Reliability

ChainFeed includes:

- 🧠 **Expiration inspection and validation**  
- ⏱️ **Hourly chain validation** *(planned)*  
- 📡 **Heartbeat and system status** *(planned)*  
- 🌐 **REST control interface for admin apps** *(planned)*

Built for high-integrity environments where correctness matters.

⸻

## 🧠 Authors & Credits
- Ernie — system design, implementation, testing  
- OpenAI ChatGPT — architectural assistance and code generation

## 📅 Roadmap
- Real-time heartbeat service  
- REST control and monitoring API  
- Long-dated expiration strategies  
- Archival ingestion and storage  


⸻

🧩 Project Structure
```text
ChainFeed/
├── core/
│   ├── chain_ingestor.py              # Normalization engine
│   ├── chain_normalizer.py            # Canonical schema enforcement
│   ├── historical_feed_manager.py     # Group orchestration and heartbeat control
│   └── providers/                     # Snapshot providers (live, historical, synthetic)
│
├── utils/
│   ├── redis_client.py                # Redis connection manager
│   ├── redis_inspect.py               # Inspect current feed and heartbeat data
│   ├── heartbeat_watcher.py           # Monitor live feed TTL and activity
│   └── expiration_utils.py            # Option expiration helpers
│
├── config/
│   ├── groups.yaml                    # Defines correlated complexes (SPX, NDX, etc.)
│   ├── chainfeed_constants.py         # Shared constants and Redis key formats
│   └── variant_config.yaml            # Alternate configs for dev/test
│
├── test/                              # Unit and integration tests
│   ├── test_historical_provider.py
│   ├── test_historical_ingest.py
│   ├── test_normalize_snapshot.py
│   └── test_snapshot_inspect.py
│
├── data/                              # Local JSON files (e.g., formatted_SPX.json)
├── notebooks/                         # Analysis and visualization notebooks
│   └── notebook_heartbeat_analysis.py
├── requirements.txt
└── README.md
```