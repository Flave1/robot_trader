# TradeBot: Automated Multi-Asset Trading System

## Overview

**TradeBot** is a fully automated, modular trading platform with a human-in-the-loop mechanism, enabling real-time decision-making and seamless execution across stock, cryptocurrency, and forex markets. The system is designed for extensibility, reliability, and low-latency operation, supporting both automated and supervised trading workflows.

---

## Features

- **Modular System Architecture:**  
  Supervisor modular approach using Node.js, Python (LangGraph/LangChain), and event-driven design for scalable, real-time trading.
- **Real-Time Trading & Notifications:**  
  Event-driven system leveraging WebSockets, Redis Pub/Sub, and FastAPI for instant trade alerts and portfolio insights.
- **Next.js Frontend:**  
  Responsive dashboard for real-time data visualization, interactive trade execution, portfolio analytics, and trade logging.
- **Customizable Trading Strategies:**  
  Rule-based strategy engine with configurable risk profiles, trading signals, and user-defined parameters, stored in PostgreSQL and Firebase Firestore.
- **Multi-Broker Support:**  
  Integrations for OANDA, MetaTrader, and more.
- **Human-in-the-Loop:**  
  Supervisor can approve, modify, or reject trades before execution.
- **Long-Term Memory:**  
  Uses Chroma vector store for semantic conversation and trade history, keyed by thread/session ID.

---

## Directory Structure

```
.
├── .env                  # Environment variables
├── pyproject.toml        # Python project dependencies
├── requirements.txt      # Additional dependencies
├── server.py             # FastAPI server entrypoint
├── metaapi_mcp.py        # MetaTrader MCP integration
├── oandaapi_mcp.py       # OANDA MCP integration
├── src/
│   ├── application/
│   │   └── services/     # Trading app service logic (OANDA, MetaTrader)
│   ├── bot/
│   │   └── tools/        # Trading tools, strategy nodes, memory, etc.
│   ├── domain/
│   │   ├── entities/     # Core trading entities (e.g., Trade)
│   │   └── interfaces/   # Service interfaces
│   ├── infrastructure/
│   │   ├── meta_api/     # MetaTrader API integration
│   │   └── oanda_api/    # OANDA API integration
│   └── model_types/      # Common data models
└── ...
```

---

## Quick Start

### 1. **Clone the Backend Repository**
```bash
git clone https://github.com/Flave1/robot_trader
cd robot_trader
```



### 2. **Install Python Dependencies**
```bash
uv pip install -r pyproject.toml
```

### 3. **Set Up Environment Variables**
Copy `.env.example` to `.env` and fill in your API keys and configuration.

### 4. **Run the Backend**
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 5. **Clone the Frontend Repository**
```bash
git clone https://github.com/Flave1/stemrobot_ui
cd stemrobot_ui

```
See the `/stemrobot_ui` or Next.js directory for setup instructions.
---

## Usage

- **API Endpoints:**  
  - `/agent` — Main agent endpoint for trade execution and supervision.
  - `/state` — Get current graph state and conversation history.
  - `/history` — Retrieve full state and conversation history for a session.

- **Trading Tools:**  
  - Place trades, monitor markets, fetch active positions, and more via MCP tools and API.

- **Strategy Customization:**  
  - Define and update trading strategies, risk profiles, and signals in the database.

---

## Technologies

- **Backend:** Python, FastAPI, LangGraph, LangChain, ChromaDB, Redis, PostgreSQL, Firebase
- **Frontend:** Next.js, WebSockets
- **Brokers:** OANDA, MetaTrader (MetaApi)
- **Messaging:** Redis Pub/Sub, WebSockets

---

## Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a pull request

---

## License

[MIT](LICENSE)

---

## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain)
- [ChromaDB](https://www.trychroma.com/)
- [OANDA API](https://developer.oanda.com/rest-live-v20/introduction/)
- [MetaApi](https://metaapi.cloud/)

---

> For more details, see the code and comments in each module, or open an issue for help!
