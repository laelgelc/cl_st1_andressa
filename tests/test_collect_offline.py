from unittest.mock import MagicMock, patch

import json

from cl_st1.ph1.collect_service import collect


@patch("cl_st1.ph1.collect_service.get_reddit")
def test_collect_writes_ndjson_and_provenance(mock_get_reddit, tmp_path):
    # Setup mocks
    mock_reddit = MagicMock()
    mock_get_reddit.return_value = mock_reddit

    mock_sr = MagicMock()
    mock_reddit.subreddit.return_value = mock_sr

    # Mock submissions
    sub1 = MagicMock()
    sub1.id = "s1"
    sub1.subreddit = "testsr"
    sub1.created_utc = 1000
    sub1.author.name = "user1"
    sub1.title = "title1"
    sub1.selftext = "text1"
    sub1.score = 10
    sub1.num_comments = 1
    sub1.url = "http://url1"
    sub1.permalink = "/r/testsr/s1"
    sub1.over_18 = False
    sub1.removed_by_category = None

    # Mock comments for sub1
    c1 = MagicMock()
    c1.id = "c1"
    c1.link_id = "t3_s1"
    c1.parent_id = "t3_s1"
    c1.subreddit = "testsr"
    c1.created_utc = 1100
    c1.author.name = "user2"
    c1.body = "comment1"
    c1.score = 5
    c1.permalink = "/r/testsr/s1/c1"
    c1.removed_by_category = None

    mock_sr.new.return_value = [sub1]
    sub1.comments.list.return_value = [c1]

    out_dir = tmp_path / "run"

    # Execute (fail fast if mocks are incomplete)
    res = collect(
        subreddits=["testsr"],
        out_dir=str(out_dir),
        listing="new",
        per_subreddit_limit=1,
        include_comments=True,
        max_retries=0,
    )

    # Verify results
    assert res == {"posts": 1, "comments": 1}

    # Verify NDJSON files
    raw_posts = out_dir / "raw" / "reddit_submissions.ndjson"
    raw_comments = out_dir / "raw" / "reddit_comments.ndjson"

    assert raw_posts.exists()
    assert raw_comments.exists()

    post_data = json.loads(raw_posts.read_text(encoding="utf-8").splitlines()[0])
    assert post_data["id"] == "s1"

    comment_data = json.loads(raw_comments.read_text(encoding="utf-8").splitlines()[0])
    assert comment_data["id"] == "c1"
    assert comment_data["link_id"] == "s1"

    # Verify provenance
    logs_dir = out_dir / "logs"
    prov_files = list(logs_dir.glob("ph1_run_*.json"))
    assert len(prov_files) == 1

    prov_data = json.loads(prov_files[0].read_text(encoding="utf-8"))
    assert prov_data["counts"]["posts"] == 1
    assert prov_data["counts"]["comments"] == 1
    assert prov_data["params"]["subreddits"] == ["testsr"]