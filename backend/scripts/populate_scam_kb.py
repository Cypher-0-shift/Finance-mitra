"""
scripts/populate_scam_kb.py — Populate Supabase scam_kb_cards table with Indian financial fraud patterns.

Usage:
    python -m scripts.populate_scam_kb [--dry-run]

Description:
    Generates 768-dimensional Gemini embeddings (models/text-embedding-004) for curated
    Indian scam awareness cards sourced from Reserve Bank of India (RBI) guidelines and
    cybercrime advisories. Inserts or updates cards in Supabase pgvector storage.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Ensure project root is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_settings
from app.db.client import init_supabase
from app.services.rag import generate_embedding

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CURATED_SCAM_CARDS = [
    {
        "pattern_name": "Unregulated Chit Fund & Ponzi Schemes",
        "description": "Unregistered entities asking for recurring deposits with promises of 30-50% returns in short timeframes, relying on new members to pay old investors until collapse.",
        "example_phrasing": "Double your money in 6 months; GUARANTEED scheme; referral commission; chit fund committee prize; guaranteed fixed returns without risk.",
        "source": "RBI / SEBI Investor Advisory on Chit Funds",
    },
    {
        "pattern_name": "Predatory Digital Lending / Fake Loan Apps",
        "description": "Unauthorized apps offering instant short-term loans with exhalative interest rates (300%+ APR), harvesting contacts and photos from phones to harass and shame borrowers upon delay.",
        "example_phrasing": "Instant KYC free loan in 5 minutes; download apk link directly; no credit score check; we will call all your contacts if not paid today.",
        "source": "RBI Working Group on Digital Lending Guidelines",
    },
    {
        "pattern_name": "WhatsApp / Telegram Part-Time Job Scam",
        "description": "Scammers recruiting victims for easy online tasks (liking YouTube videos, reviewing hotels) with small initial earnings, then demanding upfront deposit amounts to 'unlock' VIP tasks or withdraw commissions.",
        "example_phrasing": "Earn Rs 2000-5000 daily working from home 2 hours; like YouTube videos for cash; pay deposit to activate VIP Merchant task.",
        "source": "National Cyber Crime Reporting Portal (MHA)",
    },
    {
        "pattern_name": "OTP & PIN Phishing / Bank Account Block Warning",
        "description": "Fraudsters posing as Bank Officers or KYC executives claiming account/ATM card will be blocked unless an OTP, PIN, or CVV is verified over call or SMS.",
        "example_phrasing": "Your YONO SBI account is blocked immediately; update KYC via this APK link; share the OTP sent to your registered mobile number for debit card verification.",
        "source": "RBI Cyber Security Awareness for Citizens",
    },
    {
        "pattern_name": "Fake Government Scheme Processing Fee",
        "description": "Scammers claiming user has been selected for PM-SVANidhi, Pradhan Mantri Awas Yojana, or Mudra Loan, demanding an upfront 'processing fee' or 'insurance charge' via UPI.",
        "example_phrasing": "Your 2 lakh Mudra loan is approved; deposit Rs 3,500 advance tax or processing fee via PhonePe/GPay to release funds into account.",
        "source": "PMMY Official Scam Alert Advisory",
    },
    {
        "pattern_name": "Lottery & Prize Winner WhatsApp Spam",
        "description": "Messages pretending to be from WhatsApp Lucky Draw, Kaun Banega Crorepati (KBC), or e-commerce brands claiming immense lottery winnings that require taxes or customs clearance fees upfront.",
        "example_phrasing": "Congratulations you won 25 Lakh in KBC WhatsApp Lucky Draw; contact Rana Pratap on audio call; pay GST fee to get winner check.",
        "source": "National Cyber Security Coordinator Advisory",
    },
    {
        "pattern_name": "Fake Insurance & Policy Bonus Call",
        "description": "Calls from individuals pretending to be IRDAI or LIC officials promising large pending bonuses on lapsed policies if an advance fee or new investment is deposited.",
        "example_phrasing": "IRDAI refund notice; share policy number to release bonus amount; buy one more single premium bond to encash old funds.",
        "source": "IRDAI Consumer Vigilance Circular",
    },
    {
        "pattern_name": "Electricity / Utility Connection Disconnection Threat",
        "description": "Urgent SMS claiming power supply will be shut down tonight at 9 PM by electric officer due to billing dispute, urging victim to click a remote screen-sharing app link or pay small token fee.",
        "example_phrasing": "Dear consumer your electricity power will be disconnected tonight at 9:30 PM by electricity power officer; call immediately on mobile; download AnyDesk for meter recharge.",
        "source": "Power Ministry & State Discom Fraud Alert",
    },
    {
        "pattern_name": "Investment & Stock Market Tips Groups",
        "description": "Telegram or WhatsApp groups led by fake stock analysts promising guaranteed intraday profits or pre-IPO share allocations via unregulated foreign trading applications.",
        "example_phrasing": "Guaranteed 10x return in options trading; join VIP signals Telegram channel; open trading account on our international platform link.",
        "source": "SEBI Fraud Awareness Guidelines",
    },
    {
        "pattern_name": "Aadhaar Enabled Payment System (AePS) Fingerprint Misuse",
        "description": "Unauthorized agents withdrawing funds from user bank accounts using cloned Aadhaar biometrics or deceptive POS machines during subsidy cashouts.",
        "example_phrasing": "Put thumb impression again machine failed; free ration balance verification check; Aadhaar linking charges.",
        "source": "NPCI Security Advisory for AePS Users",
    }
]


async def run_population(dry_run: bool = False) -> None:
    """Populate scam cards into Supabase database."""
    settings = get_settings()
    logger.info(f"Starting Scam KB Population. Total Curated Cards: {len(CURATED_SCAM_CARDS)} | Dry Run: {dry_run}")

    db = None
    if not dry_run:
        try:
            db = init_supabase(settings)
            logger.info("Supabase client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            logger.info("Tip: Use --dry-run flag to test embedding validation locally without active database.")
            return

    success_count = 0
    for i, card in enumerate(CURATED_SCAM_CARDS, start=1):
        name = card["pattern_name"]
        text_to_embed = f"{name}: {card['description']} Examples: {card['example_phrasing']}"
        logger.info(f"[{i}/{len(CURATED_SCAM_CARDS)}] Processing: {name} ...")

        embedding = await generate_embedding(text_to_embed, settings, is_query=False)
        
        if embedding is not None:
            logger.info(f"    -> Generated vector of dim: {len(embedding)}")
        else:
            logger.warning("    -> Embedding generation returned None (using dummy zero-vector or skipping in dry run).")
            # Create a 768-dim mock vector if running in dry-run or testing mode
            if dry_run:
                embedding = [0.0] * 768

        row_data = {
            "pattern_name": name,
            "description": card["description"],
            "example_phrasing": card["example_phrasing"],
            "source": card["source"],
            "updated_at": datetime.utcnow().isoformat(),
        }
        if embedding:
            row_data["embedding"] = embedding

        if dry_run:
            logger.info(f"    [DRY RUN] Would insert card: {name} (Fields: {list(row_data.keys())})")
            success_count += 1
        elif db:
            try:
                await db.table("scam_kb_cards").insert(row_data).execute()
                logger.info(f"    [SUCCESS] Inserted '{name}' into scam_kb_cards.")
                success_count += 1
            except Exception as insert_err:
                logger.error(f"    [ERROR] Database insert failed for '{name}': {insert_err}")

    logger.info(f"\nPopulation completed. Successfully processed: {success_count}/{len(CURATED_SCAM_CARDS)} cards.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate Scam KB in Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Simulate script without writing to database")
    args = parser.parse_args()

    asyncio.run(run_population(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
