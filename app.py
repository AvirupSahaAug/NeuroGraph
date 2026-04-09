import streamlit as st
import src.config as config
from src.graph_manager import GraphManager
from src.rag_engine import RAGEngine
from src.monitor import DissatisfactionMonitor
import sys

# Page Config
st.set_page_config(
    page_title="NeuroGraph",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark mode adjustments if needed
# (Streamlit handles most, but we can enforce some styles)
st.markdown("""
<style>
    .stChatInput {
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Components
@st.cache_resource
def get_system():
    try:
        gm = GraphManager()
        # Test connection
        gm.query("RETURN 1")
    except Exception as e:
        st.error(f"Neo4j Connection Failed: {e}")
        st.stop()
        
    rag = RAGEngine(gm)
    monitor = DissatisfactionMonitor(gm) # Pass GM to monitor for graph logging
    return gm, rag, monitor

gm, rag, monitor = get_system()

# Session State for History
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state: # For RAG context
    st.session_state.history = []
if "last_bot_reply" not in st.session_state:
    st.session_state.last_bot_reply = ""

# Sidebar for controls/status
with st.sidebar:
    st.title("NeuroGraph 🧠")
    st.markdown("### Self-Improving GraphRAG System")
    st.info("Uses local Llama 3.1 & Neo4j to build a Knowledge Graph in real-time.")
    
    if st.button("Clear Memory (Wipe Graph)"):
        gm.wipe_db()
        st.success("Graph Wiped!")
        st.rerun()

    st.markdown("---")
    st.markdown("### 🛠 Training Data")
    if st.button("Generate Training Dataset"):
        with st.spinner("Processing feedback into datasets..."):
            import dataset_generator
            try:
                stats = dataset_generator.generate_requirements(
                    "dissatisfaction_dataset.jsonl",
                    "sft_dataset.jsonl",
                    "dpo_dataset.jsonl"
                )
                if stats['sft'] > 0 or stats['dpo'] > 0:
                    st.success(f"Generated {stats['sft']} SFT and {stats['dpo']} DPO records!")
                else:
                    st.info("No feedback logged yet.")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("### 📊 Metrics & Rules")
    
    # Checkbox to view active rules
    if st.checkbox("View Active Rules"):
        try:
            # Query rules from Neo4j
            rules = gm.query("MATCH (r:SyntaxRule) RETURN r.rule, r.context ORDER BY r.created_at DESC")
            if rules:
                st.write("**Learned Syntax Rules:**")
                for r in rules:
                    st.code(f"[{r['r.context']}] {r['r.rule']}", language="text")
            else:
                st.info("No syntax rules learned yet.")
        except Exception as e:
            st.error(f"Error fetching rules: {e}")

    # Checkbox to view Graph Mistakes
    if st.checkbox("View Recorded Mistakes"):
        try:
            # Query mistakes from Neo4j (including granular issues). 
            # We use OPTIONAL MATCH to avoid warnings if the labels don't exist yet in a fresh DB.
            mistakes = gm.query("""
                MATCH (m:Mistake)
                OPTIONAL MATCH (m)-[:HAS_ISSUE]->(i:Issue)
                RETURN m.timestamp as Timestamp, 
                       m.user_input as User_Input, 
                       coalesce(i.issue_type, 'N/A') as Issue_Type,
                       coalesce(i.description, 'N/A') as Description,
                       coalesce(i.cause, 'N/A') as Cause
                ORDER BY m.timestamp DESC LIMIT 15
            """)
            if mistakes:
                st.write("**Recent Granular Issues:**")
                import pandas as pd
                df = pd.DataFrame(mistakes)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No mistakes recorded yet.")
        except Exception as e:
            st.error(f"Error fetching mistakes: {e}")

    st.markdown("---")
    st.caption("Feedback Monitor Active")

# Chat Interface
# Display existing messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("What is your command?"):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 1. Monitor for dissatisfaction on PREVIOUS interaction
    # If the user says "That's wrong", they are dissatisfied with the *previous* bot reply.
    monitor_result = None
    if st.session_state.last_bot_reply:
         # We analyze if the CURRENT prompt is a complaint about the LAST reply
        is_dissatisfied, analysis = monitor.analyze_interaction(
            prompt, 
            st.session_state.last_bot_reply, 
            st.session_state.history[-5:] # Last 5 turns for context
        )
        if is_dissatisfied:
            # analysis is now a dict with keys: issues, detailed_analytics
            issues = analysis.get("issues", [])
            
            st.toast(f"Dissatisfaction Logged ({len(issues)} issues found)", icon="📝")
            for issue in issues:
                st.error(f"[{issue.get('issue_type', 'UNKNOWN')}] {issue.get('description', '')} (Cause: {issue.get('cause', '')})")
            
            monitor_result = analysis

    # 2. Generate Reply
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Thinking & Updating Graph..."):
            try:
                response = rag.generate_reply(prompt)
                message_placeholder.markdown(response)
            except Exception as e:
                st.error(f"Error generating reply: {e}")
                response = "I encountered an error."
            
    # Update Session State
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.history.append(f"User: {prompt}")
    st.session_state.history.append(f"Bot: {response}")
    st.session_state.last_bot_reply = response
