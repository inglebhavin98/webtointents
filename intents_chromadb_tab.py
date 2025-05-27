import streamlit as st
from chromadb_store import get_chromadb_client, get_or_create_intents_collection

def show_intents_chromadb_tab():
    """Display the Intents ChromaDB collection in a Streamlit tab."""
    print(f"*** show_intents_chromadb_tab")  # Debugging line
    
    if 'intents_chromadb_outputs' not in st.session_state:
        st.session_state.intents_chromadb_outputs = {}
    st.header("Intents ChromaDB Collection")
    client = get_chromadb_client()
    intents_collection = get_or_create_intents_collection(client)
    # Fetch all entries (ids, metadatas, documents)
    intent_results = intents_collection.get(include=["metadatas", "documents"])
    intent_ids = intent_results.get("ids", [])
    intent_metadatas = intent_results.get("metadatas", [])
    intent_documents = intent_results.get("documents", [])
    if not intent_ids:
        st.info("No entries found in the Intents ChromaDB collection.")
    else:
        for i, entry_id in enumerate(intent_ids):
            meta = intent_metadatas[i] if intent_metadatas and i < len(intent_metadatas) else {}
            doc = intent_documents[i] if intent_documents and i < len(intent_documents) else ""
            col1, col2 = st.columns([5, 2])
            with col1:
                st.write(f"**Intent ID:** {entry_id}")
                st.write(f"**Metadata:** {meta}")
            with col2:
                if st.button("Show Intent Document", key=f"show_intent_doc_{i}"):
                    st.session_state.intents_chromadb_outputs[entry_id] = doc
            # Show output if available
            if entry_id in st.session_state.intents_chromadb_outputs:
                st.markdown("**Intent Document:**")
                st.code(st.session_state.intents_chromadb_outputs[entry_id], language='json')
