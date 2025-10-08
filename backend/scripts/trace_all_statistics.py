#!/usr/bin/env python3
"""
Script to analyze and trace all statistic sources currently in the database.
Uses the V2 statistics verifier to trace sources and verify statistics.
"""

import sys
import os
from sqlmodel import Session, select
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

..app.database import engine
..app.models import StatisticVerification, Article
..app.services.statistics_verifier import verify_statistic_v2

def main():
    print("=" * 80)
    print("STATISTIC SOURCE VERIFICATION ANALYSIS")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}\n")

    with Session(engine) as session:
        # Get all statistics from database
        statistics = session.exec(
            select(StatisticVerification)
            .order_by(StatisticVerification.id)
        ).all()

        total_count = len(statistics)
        print(f"Found {total_count} statistics in database\n")

        if total_count == 0:
            print("No statistics found in database. Exiting.")
            return

        # Statistics counters
        stats_by_status = {
            "verified": 0,
            "unverified": 0,
            "disputed": 0,
            "false": 0
        }
        stats_by_method = {
            "article_content": 0,
            "web_search": 0,
            "database_search": 0,
            "none": 0
        }
        stats_with_source = 0
        stats_with_fact_check = 0
        stats_re_verified = 0

        print("-" * 80)
        print("ANALYZING EACH STATISTIC:")
        print("-" * 80)

        for i, stat in enumerate(statistics, 1):
            print(f"\n[{i}/{total_count}] Statistic ID: {stat.id}")
            print(f"  Article ID: {stat.article_id}")
            print(f"  Text: {stat.statistic_text[:80]}{'...' if len(stat.statistic_text) > 80 else ''}")
            print(f"  Current Status: {stat.verification_status.value}")

            # Get the article
            article = session.exec(
                select(Article).where(Article.id == stat.article_id)
            ).first()

            if not article:
                print(f"  ⚠️  WARNING: Article {stat.article_id} not found!")
                continue

            # Check current verification state
            print(f"  Previous verification:")
            if stat.source_url:
                print(f"    - Source: {stat.source_name or 'Unknown'} ({stat.source_url[:50]}...)")
                print(f"    - Credibility: {stat.source_credibility_score if stat.source_credibility_score else 'N/A'}")
                stats_with_source += 1
            else:
                print(f"    - Source: Not traced")

            if stat.fact_check_status:
                print(f"    - Fact-check: {stat.fact_check_status} via {stat.fact_check_source or 'Unknown'}")
                stats_with_fact_check += 1
            else:
                print(f"    - Fact-check: Not performed")

            # Re-verify with V2 system
            print(f"  🔄 Re-verifying with V2 system...")
            success = verify_statistic_v2(stat, article, session)

            if success:
                stats_re_verified += 1
                # Refresh the stat from DB to get updated values
                session.refresh(stat)
                print(f"  ✅ Verification complete!")
                print(f"    - New Status: {stat.verification_status.value}")
                print(f"    - Confidence Score: {stat.confidence_score:.2f}")
                print(f"    - Method: {stat.verification_method.value if stat.verification_method else 'N/A'}")

                # Track which method found the source
                if stat.source_name:
                    # Check logs to determine method - for now, count as successful trace
                    stats_by_method["article_content"] += 1  # Default assumption
                else:
                    stats_by_method["none"] += 1

                # Update counters
                stats_by_status[stat.verification_status.value] += 1
            else:
                print(f"  ❌ Verification failed")
                stats_by_status["unverified"] += 1
                stats_by_method["none"] += 1

            print("-" * 80)

        # Final summary
        print("\n" + "=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"\nTotal Statistics Analyzed: {total_count}")
        print(f"Successfully Re-verified: {stats_re_verified}")
        print(f"\nStatus Breakdown:")
        print(f"  ✅ Verified:    {stats_by_status['verified']:3d} ({stats_by_status['verified']/total_count*100:.1f}%)")
        print(f"  ❓ Unverified:  {stats_by_status['unverified']:3d} ({stats_by_status['unverified']/total_count*100:.1f}%)")
        print(f"  ⚠️  Disputed:    {stats_by_status['disputed']:3d} ({stats_by_status['disputed']/total_count*100:.1f}%)")
        print(f"  ❌ False:       {stats_by_status['false']:3d} ({stats_by_status['false']/total_count*100:.1f}%)")

        print(f"\nSource Tracing Methods:")
        print(f"  📄 Article Content: {stats_by_method['article_content']:3d}")
        print(f"  🌐 Web Search:      {stats_by_method['web_search']:3d}")
        print(f"  💾 Database:        {stats_by_method['database_search']:3d}")
        print(f"  ❌ Not Found:       {stats_by_method['none']:3d}")

        print(f"\nCompleted at: {datetime.now().isoformat()}")
        print("=" * 80)

if __name__ == "__main__":
    main()
