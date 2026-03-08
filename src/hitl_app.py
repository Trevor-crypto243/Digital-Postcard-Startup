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
                        st.divider()
                        st.write(f"### 📋 Reviewing Submission: `{selected_thread}`")
                        
                        # Query LangGraph state
                        cur.execute("SELECT checkpoint FROM checkpoints WHERE thread_id = %s ORDER BY checkpoint_id DESC LIMIT 1", (selected_thread,))
                        row = cur.fetchone()
                        
                        if row:
                            checkpoint_data = row[0]
                            # LangGraph v1/v2 checkpoint structure: look for 'channel_values' or 'values'
                            v1_values = checkpoint_data.get("channel_values", {})
                            v2_values = checkpoint_data.get("values", {})
                            state_values = v1_values or v2_values
                            
                            content = state_values.get("text_content", "N/A")
                            eval_data = state_values.get("evaluation") or {}
                            
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.subheader("✉️ Postcard Message")
                                st.info(f'"{content}"')
                                
                                st.subheader("🤖 AI's Initial Thought")
                                status = eval_data.get("status", "NEEDS_REVIEW") # Default to review if uncertain
                                confidence = eval_data.get('confidence_score', 0)
                                reasoning = eval_data.get('reasoning', 'The AI is uncertain and requests your expert judgment.')
                                
                                # Friendly Labels
                                friendly_status = {
                                    "APPROVED": "✅ Safe to Print",
                                    "REJECTED": "❌ Policy Violation",
                                    "NEEDS_REVIEW": "⚠️ Needs Expert Eyes"
                                }.get(status, "🔍 Under Investigation")
                                
                                st.markdown(f"**AI Suggestion**: {friendly_status}")
                                st.markdown(f"**Certainty Level**: `{confidence*100:.1f}%`")
                                st.markdown(f"**AI's Note**: *{reasoning}*")
                                
                                with st.expander("🛠️ Engineer's View (JSON State)"):
                                    st.json(checkpoint_data)
                            
                            with col2:
                                st.subheader("⚖️ Your Final Decision")
                                st.markdown("As a human moderator, you have the **Final Authority**. Choose whether to override or confirm the AI's suggestion.")
                                
                                with st.form("resolution_form"):
                                    new_status = st.radio("What should we do with this postcard?", ["APPROVE", "REJECT"], 
                                                        index=0 if status == "APPROVED" else 1,
                                                        help="Approve means it goes to print. Reject means the user is notified of a violation.")
                                    comments = st.text_area("Why are you making this choice? (Audit Note)", placeholder="e.g., 'False positive, the content is actually a joke, not a threat.'")
                                    submit = st.form_submit_button("Confirm Decision & Update System", use_container_width=True)
                                    
                                    if submit:
                                        cur.execute("""
                                            INSERT INTO human_reviews (submission_id, decision, reasoning)
                                            VALUES (%s, %s, %s)
                                            ON CONFLICT (submission_id) DO UPDATE SET 
                                                decision = EXCLUDED.decision,
                                                reasoning = EXCLUDED.reasoning,
                                                reviewed_at = CURRENT_TIMESTAMP
                                        """, (selected_thread, new_status, comments))
                                        conn.commit()
                                        st.success(f"✅ Resolution for `{selected_thread}` has been officially logged. The system will now execute your decision.")
                                        st.balloons()
                        else:
                            st.warning("Could not find the 'thinking process' for this postcard in the database.")
                else:
                    st.write("No pending reviews found in the database.")
    except Exception as e:
        st.error(f"Error querying database: {e}")
        st.warning("Note: If you just started the containers, the `checkpoints` table might be empty until the first evaluation is run.")

st.divider()
st.subheader("🕒 Audit Log: Resolution History")
if pool:
    try:
        with pool.connection() as conn:
            df = pd.read_sql("SELECT submission_id as ID, decision as Decision, reasoning as Notes, reviewed_at as Time FROM human_reviews ORDER BY reviewed_at DESC LIMIT 5", conn)
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No resolutions have been recorded yet.")
    except Exception:
        st.write("Complete your first human review to initialize the audit log.")

st.divider()
st.caption("Agentic Systems Engineer | Compliance & Manual Review Interface")
