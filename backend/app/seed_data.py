"""
Seed initial data for the news aggregator.
Run this once after creating the database to populate sources, topics, seed frameworks,
test user, and trigger initial article scraping.
"""

from sqlmodel import Session, select
from .database import engine
from .models import Source, Topic, Framework, SourceTopicLink, User, UserTopicPreference
from .utils.auth import hash_password
from datetime import datetime
import time
import logging
import os

logger = logging.getLogger(__name__)


# News Sources
SOURCES = [
    {
        "name": "Associated Press",
        "url": "https://apnews.com",
        "rss_feed_url": "https://rsshub.app/apnews/topics/apf-topnews",
        "description": "Non-profit news agency, known for factual reporting",
        "trust_score": 0.95,
        "topics": ["general", "politics", "world"],
    },
    {
        "name": "Reuters",
        "url": "https://www.reuters.com",
        "rss_feed_url": "https://www.reutersagency.com/feed/",
        "description": "International news organization, business focus",
        "trust_score": 0.95,
        "topics": ["general", "economics", "world"],
    },
    {
        "name": "NPR",
        "url": "https://www.npr.org",
        "rss_feed_url": "https://feeds.npr.org/1001/rss.xml",
        "description": "Public radio, in-depth news analysis",
        "trust_score": 0.90,
        "topics": ["general", "culture", "politics"],
    },
    {
        "name": "BBC News",
        "url": "https://www.bbc.com/news",
        "rss_feed_url": "http://feeds.bbci.co.uk/news/rss.xml",
        "description": "British public broadcaster, global coverage",
        "trust_score": 0.92,
        "topics": ["world", "general"],
    },
    {
        "name": "The New York Times",
        "url": "https://www.nytimes.com",
        "rss_feed_url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "description": "Major US newspaper, comprehensive coverage",
        "trust_score": 0.88,
        "topics": ["general", "politics", "culture"],
    },
    {
        "name": "Politico",
        "url": "https://www.politico.com",
        "rss_feed_url": "https://www.politico.com/rss/politicopicks.xml",
        "description": "Political news and analysis",
        "trust_score": 0.85,
        "topics": ["politics"],
    },
    {
        "name": "Ars Technica",
        "url": "https://arstechnica.com",
        "rss_feed_url": "http://feeds.arstechnica.com/arstechnica/index",
        "description": "Technology news and analysis",
        "trust_score": 0.90,
        "topics": ["technology", "science"],
    },
    {
        "name": "The Atlantic",
        "url": "https://www.theatlantic.com",
        "rss_feed_url": "https://www.theatlantic.com/feed/all/",
        "description": "Long-form journalism, culture and politics",
        "trust_score": 0.87,
        "topics": ["culture", "politics"],
    },
]

# Topics (user can toggle these)
TOPICS = [
    {"name": "general", "description": "General news and current events", "is_active_default": True},
    {"name": "politics", "description": "Political news and policy", "is_active_default": True},
    {"name": "economics", "description": "Business, finance, and economic policy", "is_active_default": True},
    {"name": "technology", "description": "Tech industry, innovation, and digital culture", "is_active_default": True},
    {"name": "science", "description": "Scientific research and discoveries", "is_active_default": True},
    {"name": "culture", "description": "Arts, society, and cultural trends", "is_active_default": False},
    {"name": "world", "description": "International news and global affairs", "is_active_default": True},
    {"name": "environment", "description": "Climate, sustainability, and environmental issues", "is_active_default": False},
]

# Seed Frameworks (hand-curated ethical debates)
FRAMEWORKS = [
    {
        "name": "Individual Liberty vs. Collective Welfare",
        "description": "The tension between personal freedom and societal benefit",
        "axis_description": "personal autonomy ←→ social responsibility",
        "left_position": "Maximize individual rights and freedoms",
        "right_position": "Prioritize community well-being and collective good",
        "is_seed": True,
    },
    {
        "name": "Free Markets vs. Government Regulation",
        "description": "The role of government in economic activity",
        "axis_description": "market forces ←→ state intervention",
        "left_position": "Minimal regulation, let markets self-correct",
        "right_position": "Active government oversight to prevent harm",
        "is_seed": True,
    },
    {
        "name": "Tradition vs. Progress",
        "description": "Preserving established values vs. embracing change",
        "axis_description": "traditional values ←→ progressive change",
        "left_position": "Preserve time-tested institutions and norms",
        "right_position": "Embrace innovation and social evolution",
        "is_seed": True,
    },
    {
        "name": "National Interest vs. Global Cooperation",
        "description": "Sovereignty vs. international collaboration",
        "axis_description": "national sovereignty ←→ global governance",
        "left_position": "Prioritize domestic concerns and independence",
        "right_position": "International cooperation and multilateralism",
        "is_seed": True,
    },
    {
        "name": "Economic Growth vs. Environmental Protection",
        "description": "Development vs. sustainability",
        "axis_description": "economic expansion ←→ ecological preservation",
        "left_position": "Economic development as primary goal",
        "right_position": "Environmental sustainability as priority",
        "is_seed": True,
    },
    {
        "name": "Security vs. Privacy",
        "description": "Safety through surveillance vs. personal privacy",
        "axis_description": "national security ←→ individual privacy",
        "left_position": "Enhanced security measures, even if invasive",
        "right_position": "Protect privacy rights from government overreach",
        "is_seed": True,
    },
    {
        "name": "Meritocracy vs. Equity",
        "description": "Individual achievement vs. equal outcomes",
        "axis_description": "merit-based rewards ←→ equitable distribution",
        "left_position": "Reward individual merit and achievement",
        "right_position": "Ensure equitable outcomes across groups",
        "is_seed": True,
    },
    {
        "name": "Innovation vs. Precaution",
        "description": "Speed of technological adoption vs. careful assessment",
        "axis_description": "rapid innovation ←→ cautious evaluation",
        "left_position": "Move fast, iterate, accept some risk",
        "right_position": "Thorough testing and risk assessment first",
        "is_seed": True,
    },
    {
        "name": "Globalization vs. Localization",
        "description": "Global integration vs. local autonomy",
        "axis_description": "global integration ←→ local control",
        "left_position": "Embrace global trade and cultural exchange",
        "right_position": "Strengthen local economies and identities",
        "is_seed": True,
    },
    {
        "name": "Punishment vs. Rehabilitation",
        "description": "Criminal justice philosophy",
        "axis_description": "punitive justice ←→ restorative justice",
        "left_position": "Punish wrongdoing as deterrent",
        "right_position": "Rehabilitate and reintegrate offenders",
        "is_seed": True,
    },
]


def create_test_user(session: Session, topic_map: dict = None):
    """Create a test user for development and testing"""
    test_user_email = os.getenv("TEST_USER_EMAIL", "test@pulse.com")
    test_user_password = os.getenv("TEST_USER_PASSWORD", "testpassword123")
    test_user_name = os.getenv("TEST_USER_NAME", "Test User")

    # Check if test user already exists
    existing_user = session.exec(select(User).where(User.email == test_user_email)).first()
    if not existing_user:
        test_user = User(
            email=test_user_email,
            hashed_password=hash_password(test_user_password),
            name=test_user_name,
            email_verified=True,
            is_active=True
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)

        # Subscribe test user to all default topics if topic_map provided
        if topic_map:
            for topic_name, topic in topic_map.items():
                if topic.is_active_default:
                    preference = UserTopicPreference(
                        user_id=test_user.id,
                        topic_id=topic.id,
                        priority_level=3,  # Medium priority
                        include_in_newsletter=True,
                        articles_per_topic=5
                    )
                    session.add(preference)
            session.commit()
        else:
            # If no topic_map, subscribe to all existing default topics
            topics = session.exec(select(Topic).where(Topic.is_active_default == True)).all()
            for topic in topics:
                preference = UserTopicPreference(
                    user_id=test_user.id,
                    topic_id=topic.id,
                    priority_level=3,
                    include_in_newsletter=True,
                    articles_per_topic=5
                )
                session.add(preference)
            session.commit()

        print(f"✓ Created test user: {test_user.email}")
        print(f"   Password: {test_user_password}")
        return test_user
    else:
        print(f"✓ Test user already exists: {test_user_email}")
        return existing_user


def seed_database():
    """Populate database with initial data"""
    with Session(engine) as session:
        # Check if already seeded (check for topics AND sources)
        existing_topics = session.exec(select(Topic)).first()

        if existing_topics:
            print("Database already seeded (topics exist).")
            # Still create test user if it doesn't exist
            test_user_email = os.getenv("TEST_USER_EMAIL", "test@pulse.com")
            existing_user = session.exec(select(User).where(User.email == test_user_email)).first()
            if not existing_user:
                print("Creating test user...")
                create_test_user(session)
                print("\n✅ Test user created!")
                print(f"\n📧 Test user credentials:")
                print(f"   Email: {test_user_email}")
                print(f"   Password: {os.getenv('TEST_USER_PASSWORD', 'testpassword123')}")
            else:
                print("Test user already exists. Skipping...")
            return

        print("Seeding database...")

        # Create Topics
        topic_map = {}
        for topic_data in TOPICS:
            topic = Topic(**topic_data)
            session.add(topic)
            session.commit()
            session.refresh(topic)
            topic_map[topic.name] = topic
            print(f"✓ Created topic: {topic.name}")

        # Create Sources and link to Topics
        for source_data in SOURCES:
            topic_names = source_data.pop("topics", [])
            source = Source(**source_data)
            session.add(source)
            session.commit()
            session.refresh(source)

            # Link to topics
            for topic_name in topic_names:
                if topic_name in topic_map:
                    link = SourceTopicLink(
                        source_id=source.id,
                        topic_id=topic_map[topic_name].id
                    )
                    session.add(link)

            session.commit()
            print(f"✓ Created source: {source.name} ({len(topic_names)} topics)")

        # Create Seed Frameworks
        for framework_data in FRAMEWORKS:
            framework = Framework(**framework_data)
            session.add(framework)
            session.commit()
            print(f"✓ Created framework: {framework.name}")

        # Create Test User
        test_user = create_test_user(session, topic_map)

        print("\n✅ Database seeding complete!")
        print(f"   - {len(TOPICS)} topics")
        print(f"   - {len(SOURCES)} sources")
        print(f"   - {len(FRAMEWORKS)} frameworks")
        print(f"   - 1 test user")
        print(f"\n📧 Test user credentials:")
        print(f"   Email: {test_user.email}")
        print(f"   Password: {os.getenv('TEST_USER_PASSWORD', 'testpassword123')}")


def run_initial_scraping():
    """
    Trigger initial article scraping pipeline after seeding.
    This populates the database with actual articles.
    """
    print("\n🚀 Starting initial article scraping pipeline...")

    try:
        # Import here to avoid circular dependencies
        from .jobs.tasks import scrape_job, extract_job, analyze_job, framework_job

        # Step 1: Scrape RSS feeds
        print("\n1️⃣  Scraping RSS feeds...")
        scrape_job()
        print("   ✓ Scraping complete, waiting 10 seconds...")
        time.sleep(10)

        # Step 2: Extract article content
        print("\n2️⃣  Extracting article content...")
        extract_job()
        print("   ✓ Extraction complete, waiting 30 seconds...")
        time.sleep(30)

        # Step 3: AI analysis
        print("\n3️⃣  Running AI analysis...")
        analyze_job()
        print("   ✓ Analysis complete, waiting 30 seconds...")
        time.sleep(30)

        # Step 4: Framework mapping
        print("\n4️⃣  Mapping articles to frameworks...")
        framework_job()
        print("   ✓ Framework mapping complete!")

        print("\n✅ Initial scraping pipeline complete!")
        print("   Articles are now available in the feed.")

    except Exception as e:
        logger.error(f"Error during initial scraping: {e}")
        print(f"\n⚠️  Warning: Initial scraping failed: {e}")
        print("   You can manually trigger scraping via: POST /admin/jobs/scrape")


if __name__ == "__main__":
    seed_database()

    # Run initial scraping to populate articles
    run_initial_scraping()
