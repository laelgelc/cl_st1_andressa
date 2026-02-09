import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from cl_st1.ph1.collect_service import collect


def _author(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name)


def _submission(
        *,
        sid: str = "s1",
        subreddit: str = "testsr",
        created_utc: int = 1000,
        author: SimpleNamespace | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=sid,
        subreddit=subreddit,
        created_utc=created_utc,
        author=author,
        title="title1",
        selftext="text1",
        score=10,
        num_comments=1,
        url="http://url1",
        permalink=f"/r/{subreddit}/{sid}",
        over_18=False,
        removed_by_category=None,
        comments=SimpleNamespace(
            replace_more=lambda limit=0: None,
            list=lambda: [],
        ),
    )


def _comment(
        *,
        cid: str = "c1",
        link_id: str = "t3_s1",
        parent_id: str = "t3_s1",
        subreddit: str = "testsr",
        created_utc: int = 1100,
        author: SimpleNamespace | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=cid,
        link_id=link_id,
        parent_id=parent_id,
        subreddit=subreddit,
        created_utc=created_utc,
        author=author,
        body="comment1",
        score=5,
        permalink=f"/r/{subreddit}/comments/s1/{cid}",
        removed_by_category=None,
    )


@patch("cl_st1.ph1.collect_service.get_reddit")
def test_collect_writes_ndjson_and_provenance(mock_get_reddit, tmp_path):
    # Fake Reddit client and subreddit
    mock_reddit = MagicMock()
    mock_get_reddit.return_value = mock_reddit
    mock_sr = MagicMock()
    mock_reddit.subreddit.return_value = mock_sr

    sub = _submission(author=_author("user1"))
    com = _comment(author=_author("user2"))
    sub.comments.list = lambda: [com]

    mock_sr.new.return_value = [sub]

    out_dir = tmp_path / "run"

    res = collect(
        subreddits=["testsr"],
        out_dir=str(out_dir),
        listing="new",
        per_subreddit_limit=1,
        include_comments=True,
        max_retries=0,  # fail fast in tests
    )

    assert res == {"posts": 1, "comments": 1}

    raw_posts = out_dir / "raw" / "reddit_submissions.ndjson"
    raw_comments = out_dir / "raw" / "reddit_comments.ndjson"
    assert raw_posts.exists()
    assert raw_comments.exists()

    post_data = json.loads(raw_posts.read_text(encoding="utf-8").splitlines()[0])
    assert post_data["id"] == "s1"
    assert post_data["subreddit"] == "testsr"
    assert post_data["author"] == "user1"

    comment_data = json.loads(raw_comments.read_text(encoding="utf-8").splitlines()[0])
    assert comment_data["id"] == "c1"
    assert comment_data["link_id"] == "s1"
    assert comment_data["author"] == "user2"

    logs_dir = out_dir / "logs"
    prov_files = list(logs_dir.glob("ph1_run_*.json"))
    assert len(prov_files) == 1

    prov_data = json.loads(prov_files[0].read_text(encoding="utf-8"))
    assert prov_data["counts"]["posts"] == 1
    assert prov_data["counts"]["comments"] == 1
    assert prov_data["params"]["subreddits"] == ["testsr"]