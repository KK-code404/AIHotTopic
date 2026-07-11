from ai_daily.news import Article, deduplicate


def test_deduplicate_same_title_and_tracking_url() -> None:
    articles = [
        Article("A", "Model X released!", "one", "https://x.test/a?utm_source=rss", "2026-01-02"),
        Article("B", "Model X released", "two", "https://x.test/a", "2026-01-01"),
    ]
    result = deduplicate(articles)
    assert len(result) == 1
    assert result[0].source == "A"


def test_deduplicate_keeps_different_titles() -> None:
    articles = [
        Article("A", "Model X", "", "https://x.test/a", "2026-01-01"),
        Article("A", "Model Y", "", "https://x.test/b", "2026-01-02"),
    ]
    assert len(deduplicate(articles)) == 2

