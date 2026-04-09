# NeuroGraph: Self-Improving Syntax-Enforcing GraphRAG System

## Overview
**NeuroGraph** is an experimental Chatbot architecture that combines **Graph Databases (Neo4j)** with an automated **Reinforcement Learning from Human Feedback (RLHF)** loop.

Unlike traditional RAG systems that retrieve static documents, this system actively **listens for coding syntax rules or strict instructions** given by the user, stores them as nodes in a Neo4j Knowledge Graph, and strictly enforces them in all future responses. 

Simultaneously, it runs a background monitor to detect user dissatisfaction. If the system makes a mistake or ignores a rule, it performs root-cause analysis, logging the specific issue directly into the graph and building a dataset that can be used for future model fine-tuning.

## Key Features
*   **Dynamic Rule Extraction**: The system parses user input in real-time to identify "Rules" and "Instructions" (e.g., "Always use snake_case for functions") and stores them in the graph.
*   **Strict RAG Engine**: Retrieves all active rules from the graph during generation, forcing the Local LLM (Llama 3.1) to override its pre-training and adhere to user-defined constraints.
*   **Background Quality Critic**: Analyzes interactions to detect frustration. Breaks down failures into granular entities (`Mistake` -> `Issue` -> `Cause`).
*   **Graph-Based Mistake Logging**: Mistakes are visually and logically linked in Neo4j, making it possible to query the most common causes of AI failure.
*   **Dataset Generation**: Automatically converts logged dissatisfaction into a `requirements_dataset.jsonl` file formatted for fine-tuning.

---

## Architecture

The system is composed of four main components working in tandem:

1.  **`src/graph_manager.py` (The Builder)**
    *   Interfaces with the Neo4j Database.
    *   Stores `SyntaxRule` nodes.
    *   Logs granular hierarchical nodes for failures (`Mistake`, `Issue`, `Cause`, `DetailedAnalytics`).
2.  **`src/rag_engine.py` (The Actor)**
    *   Uses a secondary LLM call to extract syntax rules and store them.
    *   Retrieves relevant context (Rules) from the Graph.
    *   Feeds the Rules + Prompt to the LLM to generate a compliant answer.
3.  **`src/monitor.py` (The Critic)**
    *   After every bot reply, an isolated LLM call evaluates the *next* user input for signals of frustration.
    *   Outputs a JSON analysis of *why* the user was dissatisfied.
    *   Logs data to the Graph and to `dissatisfaction_dataset.jsonl`.
4.  **`dataset_generator.py` (The Tuner)**
    *   Reads the raw JSONL feedback and transforms it into standard fine-tuning formats.
    *   Outputs `sft_dataset.jsonl` (Chat ML format) for Supervised Fine-Tuning.
5.  **`remote_sync.py` (The Auditor)**
    *   Connects the local feedback loop to a larger model (Gemini Pro).
    *   Uploads dissatisfaction clusters for "Bottleneck Analysis," allowing a larger brain to audit why the local model is failing.

---

## Setup & Usage

### Prerequisites
1.  **Neo4j Database**: Must be running locally (Docker or Desktop app).
    *   Default URI: `neo4j://localhost:7687`
    *   Default Auth: `neo4j` / `password` (Configurable in `src/config.py`)
2.  **Ollama**: Must be installed and running locally.
3.  **Gemini API (Optional)**: For remote analysis, obtain an API key from Google AI Studio.
    *   Set `GEMINI_API_KEY` in `src/config.py`.

### Installation
1.  **Activate Virtual Environment**:
    ```bash
    # using an existing venv locally, e.g.:
    source ../gpu/bin/activate  # Linux/Mac
    # or
    ..\gpu\Scripts\activate     # Windows
    ```
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

You can interact with NeuroGraph via a Web UI or Terminal.

**Option 1: Streamlit Web UI (Recommended)**
```bash
streamlit run app.py
```
*   Provides a modern chat interface.
*   Sidebar controls to View Active Rules, View Recorded Mistakes, and Wipe Graph memory.
*   **Generate Training Dataset** button to convert logged feedback into SFT/DPO formats with a single click.

**Option 2: Terminal Interface**
```bash
python main.py
```
*   Lightweight command-line interface.

### Testing the System
1. **Teach it a rule**: "From now on, always reply with a pirate greeting."
2. **Ask a question**: "Write a python function to add two numbers." (Notice the pirate greeting).
3. **Trigger the Monitor**: "No, that's wrong, you forgot the pirate greeting!" 
    * Watch the Streamlit Toast / Terminal output as the Critic captures the mistake, logs it to Neo4j, and writes to the dataset file!
4. **Generate Training Data**: Run `python dataset_generator.py` to see your complaints converted into actionable training data.

---

## 🚀 Roadmap & Planned Features (What's Missing)
While NeuroGraph is functional, several features are planned for future iterations:
- [ ] **Automated Fine-Tuning Trigger**: Automatically trigger a LoRA fine-tuning run once the dataset reaches a certain size (e.g., 100 records).
- [ ] **Vector-Graph Hybrid Search**: Combine Neo4j structural queries with Vector Similarity (Neo4j Vector Index) for better retrieval coverage.
- [ ] **Multi-User Multi-Tenant Support**: Isolate rules and graphs per user session.
- [ ] **Visual Graph Explorer**: An interactive 3D graph visualization (Force-Directed Graph) directly inside the Streamlit UI to explore "Cause" clusters.
- [ ] **Advanced Prompt Versioning**: Track which version of the system prompt led to which type of dissatisfaction.

---

## 📄 Documentation
- **Report.docx**: A one-page technical report covering project methodology and results.
- **Instructions.docx**: Detailed setup and usage guide.
- **paper.tex**: Academic abstract and architecture breakdown.
