import asyncio
import os
from datetime import datetime
from src.models.schemas import PostcardSubmission, QAStatus, PostcardEvaluation
from src.engine.pipeline import create_postcard_pipeline
from src.config import settings

# This script seeds the database with diverse samples for the demo
DEMO_SAMPLES = [
    {
        "id": "demo-approved-1",
        "user_id": "user-sunny",
        "text": "The weather is beautiful at the beach! Wish you were here to enjoy the sunset."
    },
    {
        "id": "demo-rejected-1",
        "user_id": "user-bot",
        "text": "URGENT: Click here to win a million dollars now! NO SCAM! http://spam-link.xyz"
    },
    {
        "id": "demo-review-1",
        "user_id": "user-vague",
        "text": "I will see you soon. Very soon. You cannot hide from the truth forever."
    },
     {
        "id": "demo-short-1",
        "user_id": "user-brief",
        "text": "Hi."
    }
]

async def seed_demo():
    print("🚀 Seeding Demo Samples into the Pipeline...")
    pipeline = create_postcard_pipeline()
    
    for sample in DEMO_SAMPLES:
        print(f"Processing: {sample['id']}...")
        submission = PostcardSubmission(
            id=sample["id"],
            user_id=sample["user_id"],
            text_content=sample["text"]
        )
        try:
            result = await pipeline.execute(submission)
            print(f"Result for {sample['id']}: {result.evaluation.status}")
        except Exception as e:
            print(f"Expected validation failure for {sample['id']}: {e}")

if __name__ == "__main__":
    if not settings.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not found in .env. Cannot seed demo results.")
    else:
        asyncio.run(seed_demo())
        print("✅ Seeding complete. Check your Streamlit HITL app dashboard!")
