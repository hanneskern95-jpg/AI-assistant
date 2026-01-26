"""Component tests for SpotifyTool."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.tools._tools.spotify_playlist_creator import SpotifyTool


class TestSpotifyTool:
    """Component tests for the SpotifyTool."""

    @pytest.fixture
    def mock_openai(self):
        """Create a mock OpenAI client."""
        mock_client = MagicMock()
        return mock_client

    @pytest.fixture
    def mock_spotify(self):
        """Create a mock Spotify client."""
        mock_spotify_client = MagicMock()
        return mock_spotify_client

    @pytest.fixture
    def tool(self, mock_openai):
        """Create a SpotifyTool instance with mocked OpenAI client."""
        return SpotifyTool(model="gpt-4o", openai=mock_openai)

    @pytest.fixture
    def sample_playlist(self):
        """Provide sample playlist data for testing."""
        return {
            "name": "Autumn Vibes",
            "songs": [
                {"name": "California Dreaming", "artist": "The Mamas & the Papas"},
                {"name": "Take Me Home, Country Roads", "artist": "John Denver"},
                {"name": "Harvest Moon", "artist": "Neil Young"}
            ]
        }

    def test_run_tool_without_liked_songs(self, tool, mock_openai, sample_playlist):
        """Test run_tool without using liked songs."""
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(sample_playlist)
                )
            )
        ]
        mock_openai.chat.completions.create.return_value = mock_response

        # Mock create_playlist function
        with patch("src.tools._tools.spotify_playlist_creator.spotify_playlist_creator.create_playlist") as mock_create:
            result = tool.run_tool("A nice autumn day")

        # Assertions
        assert "answer_str" in result
        assert "Autumn Vibes" in result["answer_str"]
        assert "California Dreaming" in result["answer_str"]
        assert "The Mamas & the Papas" in result["answer_str"]
        assert "Harvest Moon" in result["answer_str"]
        mock_create.assert_called_once_with("Autumn Vibes", sample_playlist["songs"])

    def test_run_tool_with_liked_songs(self, tool, mock_openai, sample_playlist):
        """Test run_tool using liked songs as reference."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(sample_playlist)
                )
            )
        ]
        mock_openai.chat.completions.create.return_value = mock_response

        liked_songs = ["Song 1 — Artist 1", "Song 2 — Artist 2"]

        with patch("src.tools._tools.spotify_playlist_creator.spotify_playlist_creator.create_playlist") as mock_create:
            with patch("src.tools._tools.spotify_playlist_creator.spotify_playlist_creator.catch_liked_songs", return_value=liked_songs):
                result = tool.run_tool(
                    "Mix of new and liked songs",
                    use_liked_songs=True,
                    liked_songs_description="Balance between new and existing favorites"
                )

        assert "answer_str" in result
        assert "Autumn Vibes" in result["answer_str"]
        mock_create.assert_called_once_with("Autumn Vibes", sample_playlist["songs"])

    def test_run_tool_calls_openai_with_correct_model(self, tool, mock_openai, sample_playlist):
        """Test that run_tool calls OpenAI with the correct model."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(sample_playlist)
                )
            )
        ]
        mock_openai.chat.completions.create.return_value = mock_response

        with patch("src.tools._tools.spotify_playlist_creator.spotify_playlist_creator.create_playlist"):
            tool.run_tool("Test playlist")

        # Verify OpenAI was called with correct model
        call_args = mock_openai.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o"
        assert call_args.kwargs["response_format"] == {"type": "json_object"}
        assert call_args.kwargs["messages"][0]["role"] == "system"
        assert "spotify" in call_args.kwargs["messages"][0]["content"]
        assert call_args.kwargs["messages"][1]["role"] == "user"
        assert "Test playlist" in call_args.kwargs["messages"][1]["content"]

    def test_run_tool_with_description_containing_songs_and_artists(self, tool, mock_openai, sample_playlist):
        """Test run_tool with description containing example songs and artists."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(sample_playlist)
                )
            )
        ]
        mock_openai.chat.completions.create.return_value = mock_response

        with patch("src.tools._tools.spotify_playlist_creator.spotify_playlist_creator.create_playlist"):
            result = tool.run_tool(
                "A nice autumn day with California Dreaming and Green Day as inspiration"
            )

        assert "answer_str" in result
        call_args = mock_openai.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_run_tool_with_empty_liked_songs(self, tool, mock_openai, sample_playlist):
        """Test run_tool with empty liked songs list."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(sample_playlist)
                )
            )
        ]
        mock_openai.chat.completions.create.return_value = mock_response

        with patch("src.tools._tools.spotify_playlist_creator.spotify_playlist_creator.create_playlist"):
            with patch("src.tools._tools.spotify_playlist_creator.spotify_playlist_creator.catch_liked_songs", return_value=[]):
                result = tool.run_tool(
                    "Playlist description",
                    use_liked_songs=True,
                    liked_songs_description="Use as reference"
                )
        assert "answer_str" in result
        assert "Autumn Vibes" in result["answer_str"]
        assert "California Dreaming" in result["answer_str"]
        assert "The Mamas & the Papas" in result["answer_str"]
        assert "Harvest Moon" in result["answer_str"]

    def test_create_answer_formats_multiple_songs(self, tool):
        """Test that create_answer properly formats multiple songs."""
        playlist = {
            "name": "Test Playlist",
            "songs": [
                {"name": "Song 1", "artist": "Artist 1"},
                {"name": "Song 2", "artist": "Artist 2"},
                {"name": "Song 3", "artist": "Artist 3"}
            ]
        }

        result = tool.create_answer(playlist)

        assert "answer_str" in result
        assert "Test Playlist" in result["answer_str"]
        assert "Song 1 - Artist 1" in result["answer_str"]
        assert "Song 2 - Artist 2" in result["answer_str"]
        assert "Song 3 - Artist 3" in result["answer_str"]

    def test_create_answer_with_single_song(self, tool):
        """Test create_answer with a single song playlist.^DELETE"""
        playlist = {
            "name": "Solo",
            "songs": [
                {"name": "One Song", "artist": "One Artist"}
            ]
        }

        result = tool.create_answer(playlist)

        assert "answer_str" in result
        assert "Solo" in result["answer_str"]
        assert "One Song - One Artist" in result["answer_str"]

    def test_run_tool_caches_liked_songs(self, tool, mock_openai, sample_playlist):
        """Test that run_tool caches liked songs after first fetch."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(sample_playlist)
                )
            )
        ]
        mock_openai.chat.completions.create.return_value = mock_response

        liked_songs = ["Song 1 — Artist 1", "Song 2 — Artist 2"]

        with patch("src.tools._tools.spotify_playlist_creator.spotify_playlist_creator.create_playlist"):
            with patch("src.tools._tools.spotify_playlist_creator.spotify_playlist_creator.catch_liked_songs", return_value=liked_songs) as mock_catch:
                # First call
                tool.run_tool(
                    "Playlist 1",
                    use_liked_songs=True,
                    liked_songs_description="Description 1"
                )
                # Second call
                tool.run_tool(
                    "Playlist 2",
                    use_liked_songs=True,
                    liked_songs_description="Description 2"
                )

        # catch_liked_songs should only be called once due to caching
        mock_catch.assert_called_once()
