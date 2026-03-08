# 🎬 3-5 Minute Loom Walkthrough Script: Agentic Postcard QA

Use this script to record a professional, high-impact demo for your interviewers.

---

## **Part 1: The Intro (30 Seconds)**
> **Visual**: Start on the `README.md` or the Architecture Diagram.
- "Hi everyone! I'm [Your Name]. Today, I'm excited to walk you through the **Digital Postcard Automation Pipeline**—a production-grade Agentic System designed for high-reliability content moderation."
- "The goal of this project isn't just to use an LLM, but to build a **Deterministic AI Pipeline** that guards brand safety while scaling human efficiency."

## **Part 2: The Architecture "Why" (1 Minute)**
> **Visual**: Switch to `architecture_overview.md`.
- "The core of this system is **LangGraph**. Unlike standard chatbots, we use a stateful graph to ensure decisions are auditable and reproducible."
- "We solved the 'flakiness' of AI by using a **Multi-Layered Defense**: 
    1. First, **Deterministic Validation** catches simple errors before we spend a single token.
    2. Second, **Stateful Reasoning** handles complex policy checks.
    3. Third, **Fail-Safe Routing** ensures that if an AI is 50/50 or encounters a rate limit, it *never* guesses—it flags a human expert."

## **Part 3: The Live Demo (2 Minutes)**
> **Visual**: Switch to the **HITL App** (Streamlit).
- "Let's look at the **Human-in-the-Loop Dashboard**. This is the operational 'Final Authority' for our moderations."
- "Here you can see **`demo-approved-1`**. The AI analyzed this, saw it was safe, and recommended approval. But notice the **Technical Trace**—every logical step is persisted in PostgreSQL for audit."
- "Now look at **`demo-review-1`**. This was an ambiguous case. Instead of the system failing, it sent a **Slack Alert** and an **Email** (as documented in our tools) and routed the task here for me to review."
- *[Perform a review action]*: "I'll go ahead and 'Approve' this. Notice how it's instantly logged in our **Audit Trail** below. This is senior-level observability in practice."

## **Part 4: Scaling & Reusability (30 Seconds)**
> **Visual**: Switch to `src/engine/config_runner.py`.
- "Finally, I want to highlight that this is a **System that Builds Systems**. Our `WorkflowRunner` is entirely generic. 
- "If we wanted to move from Postcards to 'Email Receipt QA' or 'Image Moderation,' we could do it in under 15 minutes by just swapping the configuration steps. It’s built for real-world enterprise growth."

## **Part 5: Conclusion**
- "Thanks for watching! This project demonstrates how we can move AI from 'experimental' to 'mission-critical' by prioritizing resilience, observability, and human authority."

---

### **💡 Pro-Tips for Recording:**
- **Record in One Take**: Authenticity beats perfection. 
- **Show, Don't Just Tell**: Keep the terminal and UI visible.
- **Micro-Animations**: Mouse over the cards as you talk to keep the viewer engaged.
