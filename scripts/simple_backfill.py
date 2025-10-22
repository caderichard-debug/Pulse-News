#!/usr/bin/env python3
"""
Simple Source Backfill Script

Fetches additional articles from underrepresented sources to improve source diversity.
This version is designed to work with the current RSS scraper system.
"""

import sys
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.database import get_session, engine
from backend.app.models import Source, Article
from backend.app.services.rss_scraper import scrape_all_active_sources
from sqlmodel import Session, select, func

def get_source_stats():
    """Get current article count per source."""
    with Session(engine) as session:
        stats = session.exec(
            select(Source.name, func.count(Article.id).label('count'))
            .join(Article, Source.id == Article.source_id, isouter=True)
            .group_by(Source.name)
            .order_by(func.count(Article.id).desc())
        ).all()

        print("Current Source Distribution:")
        print("-" * 50)
        for name, count in stats:
            print(f"{name:25} : {count:4} articles")
        print("-" * 50)

        return stats

def trigger_additional_scraping():
    """Trigger additional RSS scraping to get more articles."""
    print("Triggering additional RSS scraping...")
    print("This will fetch new articles from all active RSS feeds.")

    try:
        result = scrape_all_active_sources()
        print(f"Scraping completed: {result}")
    except Exception as e:
        print(f"Error during scraping: {e}")

def main():
    print("Source Diversity Analysis")
    print("=" * 50)

    # Show current stats
    stats = get_source_stats()

    # Calculate current totals
    total_articles = sum(count for _, count in stats)
    unique_sources = len(stats)

    print(f"\nTotal Articles: {total_articles}")
    print(f"Unique Sources: {unique_sources}")

    # Identify underrepresented sources
    print("\nTarget: 200 articles per source (excluding BBC)")
    print("-" * 50)

    target_count = 200
    exclude_sources = ['BBC News', 'www.bbc.com']

    for name, count in stats:
        if name not in exclude_sources:
            needed = target_count - count
            status = "✓" if needed <= 0 else "NEEDS MORE"
            print(f"{name:25} : {count:4} articles ({needed:4} needed) [{status}]")

    print("\nRecommendations:")
    print("-" * 50)

    # Find sources that need the most articles
    needy_sources = [(name, target_count - count) for name, count in stats
                   if name not in exclude_sources and target_count - count > 0]
    needy_sources.sort(key=lambda x: x[1], reverse=True)

    if needy_sources:
        print(f"Top 5 sources needing articles:")
        for i, (name, needed) in enumerate(needy_sources[:5], 1):
            print(f"  {i}. {name}: needs {needed} more articles")

        print(f"\nTo improve diversity:")
        print(f"1. Run additional RSS scraping cycles")
        print(f"2. Add more RSS feeds for underrepresented sources")
        print(f"3. Consider historical article importing")

        # Ask if user wants to trigger scraping
        response = input("\nTrigger additional RSS scraping? (y/n): ").lower().strip()
        if response == 'y':
            trigger_additional_scraping()
            print("\nChecking updated stats...")
            get_source_stats()
    else:
        print("All sources meet target count!")

    print("\nProduction Deployment Notes:")
    print("-" * 50)
    print("1. Schedule multiple scraping cycles per day")
    print("2. Add RSS feeds for diverse sources (Al Jazeera, Reuters, etc.)")
    print("3. Monitor source distribution weekly")
    print("4. Set up alerts when source diversity drops below threshold")
    print("5. Consider adding international sources for global coverage")

if __name__ == "__main__":
    main()