# Local PDF QA MCP Server

This project is a small local Python application for a take-home assignment. It ingests PDF files from `pdfs/`, extracts and chunks their text, builds a local FAISS vector index, and exposes two MCP tools:

- `query_documents(question: str)` to answer questions using the indexed PDFs with source attribution
- `list_documents()` to list the indexed PDF files

## What This Project Does

- Reads all PDFs from the local `pdfs/` folder
- Extracts text page by page with PyMuPDF
- Chunks text into retrieval-friendly pieces
- Stores chunk metadata including document name and page number
- Creates embeddings with `sentence-transformers`
- Persists a local FAISS index plus chunk metadata on disk
- Exposes MCP tools through FastMCP
- Returns grounded answers with citations

## Project Structure

```text
project/
  README.md
  requirements.txt
  .env.example
  pdfs/
  src/
    __init__.py
    client.py
    server.py
    ingest.py
    parser.py
    chunking.py
    embeddings.py
    retriever.py
    qa.py
    models.py
    utils.py
```

## Assumptions Made

1. The source data folder contained 200+ files, so I selected 4 PDFs from it to use as the working document set for this local take-home implementation.
2. PDFs are ingested on demand through the ingestion step and are not automatically indexed when the MCP server starts.

## Architecture Overview

The design is intentionally simple and modular:

1. `parser.py`
   Extracts PDF text page by page and returns structured page objects.

2. `chunking.py`
   Splits each page into overlapping chunks so retrieval is more precise than using whole pages.

3. `embeddings.py`
   Wraps the embedding model so ingestion and querying both use the same interface.

4. `retriever.py`
   Builds, saves, loads, and searches a local FAISS vector index.

5. `qa.py`
   Generates the final answer from retrieved chunks. It supports:
   - an OpenAI-compatible grounded answer if `OPENAI_API_KEY` is set
   - a local extractive fallback if no API key is provided

6. `server.py`
   Exposes the MCP tools:
   - `query_documents(question: str)`
   - `list_documents()`

7. `client.py`
   A small MCP client used to test the server end to end over the MCP protocol.

## Design Choices And Tradeoffs

- **FastMCP over the official MCP Python SDK:**
  I chose FastMCP because it provides a higher-level, more ergonomic abstraction for building MCP servers in Python. FastMCP automatically handles tool schemas, validation, documentation, transport negotiation, and parts of the protocol lifecycle, which let me focus on the document ingestion and retrieval logic rather than lower-level MCP plumbing. The FastMCP project also notes that FastMCP 1.0 was incorporated into the official MCP Python SDK in 2024, so using FastMCP still aligns with the broader MCP ecosystem while giving a simpler developer experience.

- **FAISS over Chroma:**
  FAISS was chosen to keep the dependency surface smaller and the retrieval path easier to reason about. Since the dataset is small and runs locally, an in-memory vector index is sufficient and avoids introducing additional database infrastructure.

- **Character-based chunking:**
  Chunking is character-based rather than token-based to keep the ingestion pipeline model-agnostic and avoid introducing tokenizer dependencies. Since retrieval operates on embeddings and the prompt only includes a small number of chunks, approximate character-length segmentation provides a good balance between simplicity and retrieval quality.

- **Pluggable answer generation layer:**
  The answer generation layer is designed to be pluggable so the system can run locally without requiring cloud credentials. This allows switching between local models and hosted APIs without changing the retrieval pipeline.

- **Minimum similarity threshold:**
  A minimum similarity score filter is used to prevent unsupported answers. If no retrieved chunks exceed the threshold, the tool returns that the documents do not contain sufficient information.

- **Metadata preservation for source attribution:**
  Document name and page number metadata are preserved throughout the parsing and chunking pipeline so answers can include precise source citations.

- **Separation of ingestion and querying logic:**
  Document parsing, embedding generation, retrieval, and answer generation are implemented as separate modules. This keeps responsibilities clear and makes the system easier to extend or debug.

## Setup

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the environment template:

```bash
cp .env.example .env
```

4. Add `OPENAI_API_KEY` to `.env` if you want LLM-based answer synthesis. If you leave it blank, the server uses a local extractive fallback. I have sent this key in the submission email.

## Build The Index

Run the ingestion step once to parse the PDFs and create the local vector index:

```bash
python3 -m src.ingest
```

This creates:

- `data/vector.index`
- `data/chunks.json`

## Start The MCP Server

After indexing, start the server with:

```bash
python3 -m src.server
```

The server exposes MCP tools over the default FastMCP transport.

## Small Python MCP Client

This project also includes a tiny MCP client in [`client.py`](/Users/ketakigokhale/take-home-nexla/src/client.py). It starts the local server over `stdio`, initializes an MCP session, and calls the `query_documents` tool through the protocol.

Run a query like this:

```bash
python3 -m src.client query "What is NER?"
```

To test the `list_documents` tool through the same client:

```bash
python3 -m src.client list
```

## MCP Tools

### `query_documents(question: str) -> dict`

Retrieves the most relevant chunks, generates a grounded answer, and returns structured citations.

### `list_documents() -> dict`

Returns the list of indexed PDF filenames.

## Sample List

```json
{
  "documents": [
    "C18-1182.pdf",
    "D18-1003.pdf",
    "P19-1598.pdf",
    "W18-4401.pdf"
  ]
}
```

## Sample Questions And Answers

Note: these sample responses are shown in the same structured JSON-style format
returned by the tool.

### Question

`What are two different NLP tasks that involve detecting entities or information in text, and how are they evaluated?`

### Response

```json
{
  "answer": "Two such tasks are:\n\n1. Named Entity Recognition (NER): detects named entities in text, such as people, companies, facilities, bands, sports teams, movies, and TV shows. The provided context describes the task and its challenges, but does not state how it is evaluated.\n\n2. Entity Linking: identifies entity mentions in text and links them to entities such as Wikipedia articles. The context describes annotating documents with entity mentions and links, but does not state how it is evaluated.",
  "sources": [
    {
      "document": "C18-1182.pdf",
      "page": 3
    },
    {
      "document": "C18-1182.pdf",
      "page": 10
    },
    {
      "document": "P19-1598.pdf",
      "page": 4
    },
    {
      "document": "P19-1598.pdf",
      "page": 8
    },
    {
      "document": "D18-1003.pdf",
      "page": 10
    }
  ]
}
```

### Question

`How do neural architectures reduce the need for manual feature engineering in NLP tasks? Give examples from two different models.`

### Response

```json
{
  "answer": "Neural architectures reduce manual feature engineering by learning useful representations directly from data instead of relying on hand-crafted features such as gazetteers, orthographic rules, or in-domain knowledge. In NER, the survey contrasts classic feature-engineered systems with neural models based on minimal feature engineering and notes that neural systems improved results without any external resources or feature engineering.\n\nTwo examples:\n1. Word-level RNN model: words in a sentence are fed into a recurrent neural network, and each word is represented by its word embedding. This lets the model learn task-relevant word features automatically from embeddings and sequence context rather than manually designed features.\n2. Character+word hybrid neural models: these use both word representations and character or other sub-word units. The survey concludes that these feature-inferring neural network models generally outperform feature-engineered models, because they can infer morphological and sub-word patterns automatically instead of requiring hand-built affix or orthographic features.",
  "sources": [
    {
      "document": "C18-1182.pdf",
      "page": 1
    },
    {
      "document": "P19-1598.pdf",
      "page": 10
    },
    {
      "document": "C18-1182.pdf",
      "page": 5
    },
    {
      "document": "C18-1182.pdf",
      "page": 10
    }
  ]
}
```

### Question

`How do datasets differ across tasks like Named Entity Recognition, fake news detection, and aggression detection?`

### Response

```json
{
  "answer": "The datasets differ by task in label structure, size, language, and context:\n\n- Named Entity Recognition: the provided context does not contain information about NER datasets, so this is not supported.\n- Fake news detection: the context mentions a benchmark dataset for fake news detection (LIAR) and also a rumor-related setup with two subtasks: a closed variant using only the questionable tweet, and an open variant using the tweet plus extra context such as retrieved sources, a Wikipedia snapshot, news articles, and preceding tweets. The development and test sets are small, with 25/28 source tweets and 256/1021 reply tweets.\n- Aggression detection: the dataset is labeled into three classes: Overtly Aggressive (OAG), Covertly Aggressive (CAG), and Non-Aggressive (NAG). It includes multilingual data (English and Hindi), with 916 English and 970 Hindi test comments, plus surprise Twitter sets of 1,257 English and 1,194 Hindi tweets. It also has noted issues such as code-mixed and other-language content, and some systems augmented it with external toxicity or hate-speech data.",
  "sources": [
    {
      "document": "W18-4401.pdf",
      "page": 3
    },
    {
      "document": "W18-4401.pdf",
      "page": 5
    },
    {
      "document": "D18-1003.pdf",
      "page": 11
    },
    {
      "document": "W18-4401.pdf",
      "page": 6
    },
    {
      "document": "D18-1003.pdf",
      "page": 5
    }
  ]
}
```

## Other Ways To Test The Query Tool

Once the MCP server is running, connect with an MCP-compatible client such as Claude Desktop, Cursor, or MCP Inspector and call:

```json
{
  "tool": "query_documents",
  "arguments": {
    "question": "What is NER?"
  }
}
```

You can also test the retrieval and answer path directly from Python:

```bash
python3 - <<'PY'
from src.server import query_documents
print(query_documents("What is NER?"))
PY
```

## AI Tools Experience

### Which AI coding tool(s) did you use and how?

I used ChatGPT and OpenAI Codex with GPT 5.4 in my IDE as coding assistants during development. I first used ChatGPT to help draft a detailed prompt for Codex based on my understanding of the assignment and the architecture I wanted to build. I then used Codex to generate much of the implementation after providing design instructions, including the ingestion pipeline, chunking, retrieval, and the FastMCP server. I also used Codex to help explain parts of the generated code as I reviewed it.

I tested the system using my own questions across multiple documents to verify that answers were grounded and source citations were correct. I also used Codex occasionally for small fixes and iterations. AI definitely helped accelerate implementation, but I made the key design decisions myself and kept the architecture intentionally simple and aligned with the assignment requirements.

### How did you prompt or direct the AI? What worked, and what did not?

I found that giving the AI clear and structured instructions worked much better than open-ended prompts. Using ChatGPT to first help create a structured prompt for Codex was particularly helpful. In that prompt, I described the intended pipeline: reading PDFs from a folder, extracting text page by page, chunking the text while preserving document and page metadata, creating embeddings for those chunks, storing them in a local vector index, retrieving the most relevant chunks for a question, and exposing a single MCP tool that returns an answer with source citations.

Breaking the problem into smaller prompts also worked well, such as generating the ingestion logic, the retrieval layer, and the MCP server separately. This made it easier to review and refine each component.

There were a few cases where I had to refine the prompts. The initial response format generated by Codex was not structured JSON, which caused parsing errors, so I updated the prompt to explicitly require a structured JSON response with `answer` and `sources` fields. The model also initially generated answers that included follow-up questions, which is common for conversational LLM outputs but not ideal for this tool interface. I adjusted the prompt to ensure the response was a direct answer without additional conversational content.

### Where did you lean on the AI vs. where did you override or correct it?

I leaned on AI primarily for scaffolding and implementation speed. After defining the architecture I wanted, I used Codex to generate much of the initial code for components such as PDF parsing, chunking logic, embeddings, and the FastMCP server setup. I also used it to iterate on smaller helper functions and minor fixes during development.

I reviewed all AI-generated code and corrected several areas where it was either overly complex or not aligned with the assignment goals. For example, the AI initially suggested adding features such as incremental indexing and filesystem watchers for detecting new documents. I removed these to keep the implementation simpler and focused on the core requirements of the assignment.

I also adjusted the response format to return structured JSON with `answer` and `sources` fields, since the initial implementation produced free-form text that caused parsing issues. The generated answers also initially included follow-up questions, which are common in conversational LLM outputs but not ideal for this tool interface, so I modified the prompting to ensure direct responses.

### What is your overall view on how AI tooling fits into a forward-deployed engineering workflow?

I think AI coding tools fit very naturally into a forward-deployed engineering workflow because they can significantly accelerate implementation while the engineer focuses on understanding the problem and making the right design decisions. In environments where engineers need to quickly build integrations, prototypes, or custom solutions for clients, AI tools are especially useful for generating scaffolding, writing boilerplate code, and iterating quickly on small changes.

They also help developers concentrate more on prioritizing the features that actually matter, rather than spending time on repetitive implementation details. This can be particularly valuable in forward-deployed contexts where the goal is often to deliver working solutions quickly and adapt them based on real-world feedback.

At the same time, they work best when treated as assistive tools rather than decision-makers. The engineer still needs to define the architecture, evaluate trade-offs, verify correctness, and ensure the system behaves reliably. In this assignment, AI was most effective when I used it to speed up implementation after I had already decided on the overall approach.
