"""
Knowledge Base
Community knowledge sharing for family law.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import datetime
import hashlib


class ResourceType(str, Enum):
    """Types of knowledge resources."""
    ARTICLE = "article"
    FAQ = "faq"
    LEGAL_PRECEDENT = "legal_precedent"
    TEMPLATE = "template"
    CHECKLIST = "checklist"
    GUIDE = "guide"
    VIDEO = "video"
    GLOSSARY = "glossary"


class ArticleStatus(str, Enum):
    """Article publication status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REJECTED = "rejected"


@dataclass
class Article:
    """A knowledge base article."""
    article_id: str
    resource_type: ResourceType
    title: str
    slug: str  # URL-friendly identifier
    summary: str
    content: str  # Markdown content

    # Categorization
    category: str
    subcategory: Optional[str]
    tags: List[str]
    jurisdictions: List[str]
    languages: List[str]

    # Authorship
    author_id: str
    author_name: str
    contributors: List[str]
    expert_reviewed: bool
    reviewer_id: Optional[str]

    # Status
    status: ArticleStatus
    version: int
    revision_history: List[Dict[str, Any]]

    # Engagement
    view_count: int
    helpful_votes: int
    not_helpful_votes: int
    bookmark_count: int
    share_count: int

    # Related
    related_articles: List[str]
    related_cases: List[str]

    # Metadata
    created_at: str
    updated_at: str
    published_at: Optional[str]
    last_reviewed_at: Optional[str]


@dataclass
class LegalPrecedent:
    """A legal precedent or case reference."""
    precedent_id: str
    case_name: str
    case_citation: str
    court: str
    jurisdiction: str
    date_decided: str

    # Content
    summary: str
    key_holdings: List[str]
    legal_principles: List[str]
    full_text_url: Optional[str]

    # Categorization
    case_type: str  # custody, protection, etc.
    issues: List[str]
    keywords: List[str]

    # Impact
    binding_jurisdictions: List[str]
    persuasive_jurisdictions: List[str]
    subsequent_treatment: str  # followed, distinguished, overruled

    # Metadata
    added_by: str
    added_at: str
    verified: bool


@dataclass
class FAQ:
    """A frequently asked question."""
    faq_id: str
    question: str
    answer: str
    category: str
    jurisdictions: List[str]
    languages: List[str]
    related_faqs: List[str]
    view_count: int
    helpful_votes: int
    expert_verified: bool
    last_updated: str


@dataclass
class ArticleContribution:
    """A contribution to the knowledge base."""
    contribution_id: str
    contributor_id: str
    article_id: Optional[str]  # None for new articles
    contribution_type: str  # "new", "edit", "review", "translation"
    title: str
    content: str
    status: str
    submitted_at: str
    reviewed_at: Optional[str]
    reviewer_notes: Optional[str]


class KnowledgeBase:
    """Manages the community knowledge base."""

    def __init__(self):
        self.articles: Dict[str, Article] = {}
        self.precedents: Dict[str, LegalPrecedent] = {}
        self.faqs: Dict[str, FAQ] = {}
        self.contributions: Dict[str, ArticleContribution] = {}

    def create_article(
        self,
        title: str,
        content: str,
        summary: str,
        category: str,
        author_id: str,
        author_name: str,
        resource_type: ResourceType = ResourceType.ARTICLE,
        tags: Optional[List[str]] = None,
        jurisdictions: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        subcategory: Optional[str] = None
    ) -> Article:
        """Create a new article."""
        article_id = hashlib.md5(
            f"{title}-{author_id}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        slug = title.lower().replace(" ", "-").replace("'", "")[:50]
        now = datetime.datetime.now().isoformat()

        article = Article(
            article_id=article_id,
            resource_type=resource_type,
            title=title,
            slug=slug,
            summary=summary,
            content=content,
            category=category,
            subcategory=subcategory,
            tags=tags or [],
            jurisdictions=jurisdictions or ["general"],
            languages=languages or ["en"],
            author_id=author_id,
            author_name=author_name,
            contributors=[],
            expert_reviewed=False,
            reviewer_id=None,
            status=ArticleStatus.DRAFT,
            version=1,
            revision_history=[{
                "version": 1,
                "timestamp": now,
                "author": author_id,
                "action": "created"
            }],
            view_count=0,
            helpful_votes=0,
            not_helpful_votes=0,
            bookmark_count=0,
            share_count=0,
            related_articles=[],
            related_cases=[],
            created_at=now,
            updated_at=now,
            published_at=None,
            last_reviewed_at=None
        )

        self.articles[article_id] = article
        return article

    def update_article(
        self,
        article_id: str,
        content: str,
        editor_id: str,
        summary_of_changes: str
    ) -> bool:
        """Update an article's content."""
        if article_id not in self.articles:
            return False

        article = self.articles[article_id]
        now = datetime.datetime.now().isoformat()

        article.content = content
        article.version += 1
        article.revision_history.append({
            "version": article.version,
            "timestamp": now,
            "author": editor_id,
            "action": "updated",
            "summary": summary_of_changes
        })
        article.updated_at = now

        if editor_id not in article.contributors and editor_id != article.author_id:
            article.contributors.append(editor_id)

        return True

    def publish_article(
        self,
        article_id: str,
        reviewer_id: Optional[str] = None
    ) -> bool:
        """Publish an article."""
        if article_id not in self.articles:
            return False

        article = self.articles[article_id]
        now = datetime.datetime.now().isoformat()

        article.status = ArticleStatus.PUBLISHED
        article.published_at = now
        article.updated_at = now

        if reviewer_id:
            article.expert_reviewed = True
            article.reviewer_id = reviewer_id
            article.last_reviewed_at = now

        return True

    def add_precedent(
        self,
        case_name: str,
        case_citation: str,
        court: str,
        jurisdiction: str,
        date_decided: str,
        summary: str,
        key_holdings: List[str],
        legal_principles: List[str],
        case_type: str,
        added_by: str,
        issues: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        full_text_url: Optional[str] = None
    ) -> LegalPrecedent:
        """Add a legal precedent."""
        precedent_id = hashlib.md5(
            f"{case_citation}".encode()
        ).hexdigest()[:12]

        precedent = LegalPrecedent(
            precedent_id=precedent_id,
            case_name=case_name,
            case_citation=case_citation,
            court=court,
            jurisdiction=jurisdiction,
            date_decided=date_decided,
            summary=summary,
            key_holdings=key_holdings,
            legal_principles=legal_principles,
            full_text_url=full_text_url,
            case_type=case_type,
            issues=issues or [],
            keywords=keywords or [],
            binding_jurisdictions=[jurisdiction],
            persuasive_jurisdictions=[],
            subsequent_treatment="followed",
            added_by=added_by,
            added_at=datetime.datetime.now().isoformat(),
            verified=False
        )

        self.precedents[precedent_id] = precedent
        return precedent

    def add_faq(
        self,
        question: str,
        answer: str,
        category: str,
        jurisdictions: Optional[List[str]] = None,
        languages: Optional[List[str]] = None
    ) -> FAQ:
        """Add a FAQ."""
        faq_id = hashlib.md5(
            f"{question}".encode()
        ).hexdigest()[:12]

        faq = FAQ(
            faq_id=faq_id,
            question=question,
            answer=answer,
            category=category,
            jurisdictions=jurisdictions or ["general"],
            languages=languages or ["en"],
            related_faqs=[],
            view_count=0,
            helpful_votes=0,
            expert_verified=False,
            last_updated=datetime.datetime.now().isoformat()
        )

        self.faqs[faq_id] = faq
        return faq

    def search_articles(
        self,
        query: str,
        category: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        resource_type: Optional[ResourceType] = None,
        limit: int = 20
    ) -> List[Article]:
        """Search articles."""
        query_lower = query.lower()
        results = []

        for article in self.articles.values():
            if article.status != ArticleStatus.PUBLISHED:
                continue

            # Filter by category
            if category and article.category != category:
                continue

            # Filter by jurisdiction
            if jurisdiction and jurisdiction not in article.jurisdictions:
                continue

            # Filter by type
            if resource_type and article.resource_type != resource_type:
                continue

            # Search in title, summary, content, tags
            score = 0
            if query_lower in article.title.lower():
                score += 10
            if query_lower in article.summary.lower():
                score += 5
            if query_lower in article.content.lower():
                score += 1
            if any(query_lower in tag.lower() for tag in article.tags):
                score += 3

            if score > 0:
                results.append((article, score))

        # Sort by relevance score
        results.sort(key=lambda x: x[1], reverse=True)
        return [article for article, _ in results[:limit]]

    def search_precedents(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        case_type: Optional[str] = None,
        limit: int = 20
    ) -> List[LegalPrecedent]:
        """Search legal precedents."""
        query_lower = query.lower()
        results = []

        for precedent in self.precedents.values():
            # Filter by jurisdiction
            if jurisdiction and precedent.jurisdiction != jurisdiction:
                continue

            # Filter by case type
            if case_type and precedent.case_type != case_type:
                continue

            # Search in case name, summary, holdings, principles
            score = 0
            if query_lower in precedent.case_name.lower():
                score += 10
            if query_lower in precedent.summary.lower():
                score += 5
            if any(query_lower in h.lower() for h in precedent.key_holdings):
                score += 3
            if any(query_lower in p.lower() for p in precedent.legal_principles):
                score += 3
            if any(query_lower in k.lower() for k in precedent.keywords):
                score += 2

            if score > 0:
                results.append((precedent, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [precedent for precedent, _ in results[:limit]]

    def search_faqs(
        self,
        query: str,
        category: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        limit: int = 10
    ) -> List[FAQ]:
        """Search FAQs."""
        query_lower = query.lower()
        results = []

        for faq in self.faqs.values():
            # Filter by category
            if category and faq.category != category:
                continue

            # Filter by jurisdiction
            if jurisdiction and jurisdiction not in faq.jurisdictions:
                continue

            # Search in question and answer
            score = 0
            if query_lower in faq.question.lower():
                score += 10
            if query_lower in faq.answer.lower():
                score += 3

            if score > 0:
                results.append((faq, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [faq for faq, _ in results[:limit]]

    def submit_contribution(
        self,
        contributor_id: str,
        contribution_type: str,
        title: str,
        content: str,
        article_id: Optional[str] = None
    ) -> ArticleContribution:
        """Submit a contribution for review."""
        contribution_id = hashlib.md5(
            f"{contributor_id}-{title}-{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        contribution = ArticleContribution(
            contribution_id=contribution_id,
            contributor_id=contributor_id,
            article_id=article_id,
            contribution_type=contribution_type,
            title=title,
            content=content,
            status="pending",
            submitted_at=datetime.datetime.now().isoformat(),
            reviewed_at=None,
            reviewer_notes=None
        )

        self.contributions[contribution_id] = contribution
        return contribution

    def review_contribution(
        self,
        contribution_id: str,
        approved: bool,
        reviewer_notes: str
    ) -> bool:
        """Review a contribution."""
        if contribution_id not in self.contributions:
            return False

        contribution = self.contributions[contribution_id]
        contribution.status = "approved" if approved else "rejected"
        contribution.reviewed_at = datetime.datetime.now().isoformat()
        contribution.reviewer_notes = reviewer_notes
        return True

    def record_engagement(
        self,
        resource_type: str,
        resource_id: str,
        engagement_type: str  # view, helpful, not_helpful, bookmark, share
    ):
        """Record user engagement with a resource."""
        if resource_type == "article" and resource_id in self.articles:
            article = self.articles[resource_id]
            if engagement_type == "view":
                article.view_count += 1
            elif engagement_type == "helpful":
                article.helpful_votes += 1
            elif engagement_type == "not_helpful":
                article.not_helpful_votes += 1
            elif engagement_type == "bookmark":
                article.bookmark_count += 1
            elif engagement_type == "share":
                article.share_count += 1

        elif resource_type == "faq" and resource_id in self.faqs:
            faq = self.faqs[resource_id]
            if engagement_type == "view":
                faq.view_count += 1
            elif engagement_type == "helpful":
                faq.helpful_votes += 1

    def get_popular_articles(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Article]:
        """Get most popular articles."""
        articles = [
            a for a in self.articles.values()
            if a.status == ArticleStatus.PUBLISHED
        ]

        if category:
            articles = [a for a in articles if a.category == category]

        # Score by engagement
        scored = [
            (a, a.view_count + a.helpful_votes * 5 + a.bookmark_count * 3)
            for a in articles
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [a for a, _ in scored[:limit]]

    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories with article counts."""
        categories: Dict[str, int] = {}

        for article in self.articles.values():
            if article.status == ArticleStatus.PUBLISHED:
                categories[article.category] = categories.get(article.category, 0) + 1

        return [
            {"category": cat, "article_count": count}
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)
        ]
