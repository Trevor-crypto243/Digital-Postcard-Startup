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
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.subheader("🤖 AI Evaluation State")
                            st.json(checkpoint[0] if checkpoint else {"info": "No checkpoint data found."})
                        
                        with col2:
                            st.subheader("👤 Human Resolution")
                            with st.form("resolution_form"):
                                new_status = st.radio("Resolution Decision:", ["APPROVE", "REJECT"])
                                comments = st.text_area("Resolution Reasoning/Notes:")
                                submit = st.form_submit_button("Record Human Decision")
                                
                                if submit:
                                    # Create table if it doesn't exist (demo convenience)
                                    cur.execute("""
                                        CREATE TABLE IF NOT EXISTS human_reviews (
                                            submission_id TEXT PRIMARY KEY,
                                            decision TEXT,
                                            reasoning TEXT,
                                            reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                        )
                                    """)
                                    cur.execute("""
                                        INSERT INTO human_reviews (submission_id, decision, reasoning)
                                        VALUES (%s, %s, %s)
                                        ON CONFLICT (submission_id) DO UPDATE SET 
                                            decision = EXCLUDED.decision,
                                            reasoning = EXCLUDED.reasoning,
                                            reviewed_at = CURRENT_TIMESTAMP
                                    """, (selected_thread, new_status, comments))
                                    conn.commit()
                                    st.success(f"Successfully recorded resolution for {selected_thread}!")
                else:
                    st.write("No pending reviews found in the database.")
    except Exception as e:
        st.error(f"Error querying database: {e}")
        st.warning("Note: If you just started the containers, the `checkpoints` table might be empty until the first evaluation is run.")

st.subheader("🕒 Audit Log: Recent Human Decisions")
if pool:
    try:
        with pool.connection() as conn:
            df = pd.read_sql("SELECT * FROM human_reviews ORDER BY reviewed_at DESC LIMIT 5", conn)
            if not df.empty:
                st.table(df)
            else:
                st.info("No human decisions logged yet.")
    except Exception:
        st.write("Run your first review to see the audit log.")

st.divider()
st.caption("Agentic Systems Engineer Trial - Human-in-the-Loop Component")
