"""
Integration tests for the complete article processing pipeline.
Tests multiple services working together.
"""

import pytest
from sqlmodel import Session
from app.models import Source, Article, ArticleAnalysis, Topic, ProcessingStatus, PoliticalLean
from app.services.rss_scraper import scrape_source
from app.services.article_extractor import extract_article_content
from unittest.mock import patch, Mock
import feedparser


class TestArticlePipelineIntegration:
    """Test the complete article processing pipeline"""

    def test_scrape_to_extraction_pipeline(self, session: Session):
        """
        Integration test: RSS scrape → article extraction
        Tests that scraped articles can be extracted
        """
        # Create source and topic
        topic = Topic(name="Technology", description="Tech news")
        source = Source(
            name="TechNews",
            rss_url="https://technews.example.com/feed",
            website_url="https://technews.example.com",
            is_active=True,
            trust_score=8.0
        )
        session.add(topic)
        session.add(source)
        session.commit()
        session.refresh(source)

        # Mock RSS feed data
        mock_feed = {
            'entries': [
                {
                    'title': 'New AI Development',
                    'link': 'https://technews.example.com/ai-development',
                    'description': 'Major AI breakthrough announced',
                    'published': 'Wed, 01 Jan 2025 10:00:00 GMT'
                }
            ]
        }

        # Mock article content extraction
        mock_html = "<html><body><p>This is the full article content about AI development.</p></body></html>"

        with patch('app.services.rss_scraper.feedparser.parse', return_value=mock_feed):
            with patch('app.services.article_extractor.requests.get') as mock_get:
                mock_response = Mock()
                mock_response.text = mock_html
                mock_response.status_code = 200
                mock_get.return_value = mock_response

                with patch('app.services.article_extractor.trafilatura.extract', return_value="This is the full article content about AI development."):
                    # Step 1: Scrape articles
                    scraped_count = scrape_source(session, source.id)
                    assert scraped_count == 1

                    # Verify article was created
                    article = session.query(Article).filter(Article.source_id == source.id).first()
                    assert article is not None
                    assert article.title == 'New AI Development'
                    assert article.status == ProcessingStatus.SCRAPED

                    # Step 2: Extract content
                    extracted_count = extract_article_content(session, article.id)
                    assert extracted_count == 1

                    # Verify article was updated
                    session.refresh(article)
                    assert article.content_text is not None
                    assert article.status == ProcessingStatus.EXTRACTED
                    assert "full article content" in article.content_text

    def test_extraction_to_analysis_pipeline(self, session: Session):
        """
        Integration test: Article extraction → AI analysis
        Tests that extracted articles can be analyzed
        """
        from app.services.ai_analyzer import analyze_article

        # Create source and article
        source = Source(
            name="NewsSource",
            rss_url="https://news.example.com/feed",
            website_url="https://news.example.com",
            is_active=True,
            trust_score=9.0
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        article = Article(
            title="Economic Policy Update",
            url="https://news.example.com/economy",
            source_id=source.id,
            description="New economic policy announced",
            published_at="2025-01-01T10:00:00Z",
            content_text="The government announced a new economic policy aimed at reducing inflation by 2%.",
            status=ProcessingStatus.EXTRACTED
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "summary": "Government announces new economic policy to reduce inflation",
            "sentiment_score": 0,
            "political_lean": "CENTER",
            "bias_indicators": "neutral",
            "key_stats": ["2% inflation reduction target"]
        }
        '''
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        with patch('app.services.ai_analyzer.openai_client') as mock_client:
            mock_client.is_available.return_value = True
            mock_client.client.chat.completions.create.return_value = mock_response

            # Analyze article
            result = analyze_article(session, article.id)
            assert result is True

            # Verify analysis was created
            session.refresh(article)
            assert article.status == ProcessingStatus.ANALYZED

            analysis = session.query(ArticleAnalysis).filter(
                ArticleAnalysis.article_id == article.id
            ).first()

            assert analysis is not None
            assert "Government announces" in analysis.summary
            assert analysis.sentiment_score == 0
            assert analysis.political_lean == PoliticalLean.CENTER

    def test_full_pipeline_with_error_handling(self, session: Session):
        """
        Integration test: Full pipeline with error handling
        Tests graceful handling of failures at each stage
        """
        # Create source
        source = Source(
            name="ErrorSource",
            rss_url="https://error.example.com/feed",
            website_url="https://error.example.com",
            is_active=True,
            trust_score=7.0
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        # Test 1: Scraping with invalid feed
        with patch('app.services.rss_scraper.feedparser.parse', side_effect=Exception("Feed error")):
            count = scrape_source(session, source.id)
            assert count == 0  # Should handle error gracefully

        # Test 2: Extraction with network error
        article = Article(
            title="Test Article",
            url="https://error.example.com/article",
            source_id=source.id,
            description="Test",
            published_at="2025-01-01T10:00:00Z",
            status=ProcessingStatus.SCRAPED
        )
        session.add(article)
        session.commit()

        with patch('app.services.article_extractor.requests.get', side_effect=Exception("Network error")):
            count = extract_article_content(session, article.id)
            # Should handle error but still mark as processed
            session.refresh(article)
            assert article.status == ProcessingStatus.EXTRACTION_FAILED or article.status == ProcessingStatus.SCRAPED

    def test_batch_processing_integration(self, session: Session):
        """
        Integration test: Batch processing
        Tests that multiple articles can be processed in batch
        """
        from app.services.ai_analyzer import analyze_articles_batch

        # Create source
        source = Source(
            name="BatchSource",
            rss_url="https://batch.example.com/feed",
            website_url="https://batch.example.com",
            is_active=True,
            trust_score=8.5
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        # Create multiple extracted articles
        for i in range(3):
            article = Article(
                title=f"Article {i+1}",
                url=f"https://batch.example.com/article-{i+1}",
                source_id=source.id,
                description=f"Description {i+1}",
                published_at="2025-01-01T10:00:00Z",
                content_text=f"Content for article {i+1}",
                status=ProcessingStatus.EXTRACTED
            )
            session.add(article)

        session.commit()

        # Mock batch analysis
        with patch('app.services.ai_analyzer.openai_client') as mock_client:
            mock_client.is_available.return_value = True
            mock_client.analyze_articles_batch.return_value = [
                {
                    "summary": f"Summary {i+1}",
                    "sentiment_score": i,
                    "political_lean": "CENTER",
                    "bias_indicators": "neutral",
                    "key_stats": []
                }
                for i in range(3)
            ]

            # Process batch
            count = analyze_articles_batch(session, batch_size=3)
            assert count == 3

            # Verify all articles were analyzed
            analyzed = session.query(Article).filter(
                Article.status == ProcessingStatus.ANALYZED
            ).all()
            assert len(analyzed) == 3


class TestNewsletterPipelineIntegration:
    """Test newsletter generation with multiple components"""

    def test_newsletter_respects_user_preferences(self, session: Session):
        """
        Integration test: Newsletter generation with preferences
        Tests that newsletters respect user topic and source preferences
        """
        from app.models import User, UserTopicPreference, UserSourceSubscription
        from app.services.newsletter_service import generate_newsletter
        from app.utils.auth import hash_password

        # Create user
        user = User(
            email="newsletter@example.com",
            name="Newsletter User",
            hashed_password=hash_password("password123"),
            source_discovery_mode="curated",
            article_order_preference="good_first",
            articles_per_topic_default=2
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create topics
        tech_topic = Topic(name="Technology", description="Tech news")
        politics_topic = Topic(name="Politics", description="Political news")
        session.add_all([tech_topic, politics_topic])
        session.commit()
        session.refresh(tech_topic)
        session.refresh(politics_topic)

        # User subscribes only to Technology
        pref = UserTopicPreference(
            user_id=user.id,
            topic_id=tech_topic.id,
            is_subscribed=True,
            priority=5,
            articles_per_topic=2
        )
        session.add(pref)
        session.commit()

        # Create source
        source = Source(
            name="TechSource",
            rss_url="https://tech.example.com/feed",
            website_url="https://tech.example.com",
            is_active=True,
            trust_score=8.0
        )
        session.add(source)
        session.commit()
        session.refresh(source)

        # User subscribes to source
        source_sub = UserSourceSubscription(
            user_id=user.id,
            source_id=source.id,
            is_subscribed=True
        )
        session.add(source_sub)
        session.commit()

        # Create articles in both topics
        from app.models import ArticleTopic

        tech_article = Article(
            title="Tech Article",
            url="https://tech.example.com/article1",
            source_id=source.id,
            description="Tech news",
            published_at="2025-01-01T10:00:00Z",
            status=ProcessingStatus.ANALYZED
        )
        session.add(tech_article)
        session.commit()
        session.refresh(tech_article)

        # Link tech article to tech topic
        session.add(ArticleTopic(article_id=tech_article.id, topic_id=tech_topic.id))

        # Add analysis
        session.add(ArticleAnalysis(
            article_id=tech_article.id,
            summary="Tech summary",
            sentiment_score=5,
            political_lean=PoliticalLean.CENTER,
            bias_indicators="neutral",
            key_stats=[]
        ))

        politics_article = Article(
            title="Politics Article",
            url="https://tech.example.com/article2",
            source_id=source.id,
            description="Political news",
            published_at="2025-01-01T11:00:00Z",
            status=ProcessingStatus.ANALYZED
        )
        session.add(politics_article)
        session.commit()
        session.refresh(politics_article)

        # Link politics article to politics topic
        session.add(ArticleTopic(article_id=politics_article.id, topic_id=politics_topic.id))

        # Add analysis
        session.add(ArticleAnalysis(
            article_id=politics_article.id,
            summary="Politics summary",
            sentiment_score=-2,
            political_lean=PoliticalLean.LEFT,
            bias_indicators="slight left bias",
            key_stats=[]
        ))

        session.commit()

        # Generate newsletter
        newsletter = generate_newsletter(session, user.id)

        assert newsletter is not None
        assert newsletter.user_id == user.id

        # Newsletter should only include tech article (user's subscribed topic)
        from app.models import NewsletterArticle
        newsletter_articles = session.query(NewsletterArticle).filter(
            NewsletterArticle.newsletter_id == newsletter.id
        ).all()

        # Should have tech article, not politics article
        article_ids = [na.article_id for na in newsletter_articles]
        assert tech_article.id in article_ids
        assert politics_article.id not in article_ids
