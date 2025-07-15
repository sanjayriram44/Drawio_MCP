# Drawio_MCP

A modular client-server setup for generating **Draw.io diagrams** using natural language prompts. It uses **LangGraph**, **LangChain**, **Gemini 2.5**, and a **FastMCP**-based server to convert text into XML diagram code and serve it via a tool-based API.

---

## 🔧 Features

- Streamlit client for chatting with the tool.
- Server powered by FastMCP that:
  - Parses user prompt → instructions
  - Generates draw.io XML from instructions
  - Verifies XML
- Uses `gemini-2.5-flash-preview-05-20` for generation.
- Output is saved as `.drawio` in your `~/Downloads` folder.

---

## 🗂 Structure


├── client.py # Streamlit UI
├── server.py # FastMCP-based server
├── Dockerfile # Containerization setup
├── requirements.txt # Python dependencies
├── prompts/ # Prompt templates
├── LICENSE
├── README.md

---

## 🚀 Running Locally

### 1. Install Python deps

```bash
pip install -r requirements.txt
```

### 2. Set environment variables
Make sure .env includes:

GROQ_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here


### 3. Start the server

```bash
python server.py
```

### 4. Run the client

```bash
python client.py
```

### 5. Docker Support

```bash
docker build -t drawio_mcp .
docker run -p 8000:8000 --env-file .env drawio_mcp
```

### 6. ✍🏾 Prompt Example
Create a workflow showing user login, verification, and dashboard redirection.


