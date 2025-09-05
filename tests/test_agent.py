import os
from unittest.mock import MagicMock
# Note the cleaner import, which is possible because of pytest.ini
from agent import summarize_diff

def test_summarize_diff_with_mock_api(mocker):
    """
    Tests the summarize_diff function by correctly mocking the OpenAI API call.
    This test should run instantly and make no external network requests.
    """
    # 1. Arrange: Set up the mock
    # The patch target must match how the object is imported in the file under test.
    # In agent.py, we do `from openai import OpenAI`, so we patch 'agent.OpenAI'.
    mock_openai_class = mocker.patch('agent.OpenAI')

    # When `OpenAI()` is called in our code, it will return this mock instance
    mock_instance = MagicMock()
    mock_openai_class.return_value = mock_instance

    # Configure the mock instance to return a predictable response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a mock summary."
    mock_instance.chat.completions.create.return_value = mock_response

    # We still need to patch the environment variable because the code reads it
    mocker.patch.dict(os.environ, {"OPENAI_API_KEY": "dummy_key_should_not_be_used"})
    
    sample_diff = "--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-hello\n+world"

    # 2. Act: Run the function we are testing
    summary = summarize_diff(sample_diff)

    # 3. Assert: Check if we got our mocked response
    assert summary == "This is a mock summary."

    # Assert that the real API was never actually called, but our mock was.
    mock_instance.chat.completions.create.assert_called_once()