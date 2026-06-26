from unittest.mock import MagicMock

import httpx
from services.slack_service import post_slack_message, slack_configured


def test_slack_configured_false_when_webhook_missing(monkeypatch) -> None:
    monkeypatch.setattr("services.slack_service.settings.SLACK_WEBHOOK_URL", "")
    assert slack_configured() is False


def test_slack_configured_true_when_webhook_present(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.slack_service.settings.SLACK_WEBHOOK_URL",
        "https://hooks.slack.com/services/T/B/X",
    )
    assert slack_configured() is True


def test_post_slack_message_skips_when_webhook_not_configured(monkeypatch) -> None:
    monkeypatch.setattr("services.slack_service.settings.SLACK_WEBHOOK_URL", "")
    mock_client = MagicMock()
    post_slack_message(text="hello", client=mock_client)
    mock_client.post.assert_not_called()


def test_post_slack_message_posts_payload(monkeypatch) -> None:
    webhook = "https://hooks.slack.com/services/T/B/X"
    monkeypatch.setattr("services.slack_service.settings.SLACK_WEBHOOK_URL", webhook)

    response = MagicMock()
    response.raise_for_status.return_value = None
    mock_client = MagicMock()
    mock_client.post.return_value = response

    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Job done"}}]
    post_slack_message(text="Job done", blocks=blocks, client=mock_client)

    mock_client.post.assert_called_once_with(
        webhook,
        json={"text": "Job done", "blocks": blocks},
    )


def test_post_slack_message_raises_on_http_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.slack_service.settings.SLACK_WEBHOOK_URL",
        "https://hooks.slack.com/services/T/B/X",
    )
    mock_client = MagicMock()
    mock_client.post.side_effect = httpx.HTTPError("down")

    try:
        post_slack_message(text="hello", client=mock_client)
        raise AssertionError("expected HTTPError")
    except httpx.HTTPError:
        pass
