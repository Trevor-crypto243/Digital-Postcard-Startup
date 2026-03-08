import streamlit as st
import os
import pandas as pd
from psycopg_pool import ConnectionPool

st.set_page_config(page_title="Agentic QA - Human-in-the-Loop", layout="wide")

st.title("🛡️ Postcard Content QA: Human-in-the-Loop Interface")
st.markdown("""
This interface is designed to review postcards that the automated AI pipeline flagged as `NEEDS_REVIEW`.
""")

# Database Connection
DB_URI = os.getenv("DATABASE_SYNC_URL", "postgresql://admin:password@localhost:5435/agentic_db")

@st.cache_resource
def get_conn_pool():
    try:
        # Standardize URI for psycopg
        pg_uri = DB_URI.replace("postgresql+psycopg://", "postgresql://")
        return ConnectionPool(conninfo=pg_uri, max_size=10)
    except Exception as e:
        st.error(f"Failed to connect to Database: {e}")
        return None

pool = get_conn_pool()

st.sidebar.header("System Status")
if pool:
    st.sidebar.success("Database Connected (Port 5435)")
else:
    st.sidebar.error("Database Disconnected")

st.subheader("Pending Reviews")
st.info("The automated pipeline routes ambiguous cases here. In this demo, we simulate the review queue by querying the LangGraph state store.")

if pool:
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                # Query LangGraph checkpoints to see thread history
                cur.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id DESC LIMIT 10")
                threads = cur.fetchall()
                
                if threads:
                    selected_thread = st.selectbox("Select a Thread (Submission ID) to inspect:", [t[0] for t in threads])
                    
                    if selected_thread:
                        st.write(f"### Inspection for Thread: `{selected_thread}`")
                        # This is a simplified view of the checkpoint data
                        cur.execute("SELECT checkpoint FROM checkpoints WHERE thread_id = %s ORDER BY checkpoint_id DESC LIMIT 1", (selected_thread,))
                        checkpoint = cur.fetchone()
                        st.json(checkpoint[0] if checkpoint else {"info": "No checkpoint data found."})
                else:
                    st.write("No pending reviews found in the database.")
    except Exception as e:
        st.error(f"Error querying database: {e}")
        st.warning("Note: If you just started the containers, the `checkpoints` table might be empty until the first evaluation is run.")

st.divider()
st.caption("Agentic Systems Engineer Trial - Human-in-the-Loop Component")
