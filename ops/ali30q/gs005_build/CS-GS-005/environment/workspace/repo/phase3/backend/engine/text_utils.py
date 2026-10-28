"""Text utility functions for the Nautilus Engine."""


def truncate(text: str, max_len: int = 200, ellipsis: str = '...') -> str:
    """Truncate text to a maximum length, appending an ellipsis if truncated.

    Args:
        text: The input string to potentially truncate.
        max_len: Maximum desired length of the output string.
        ellipsis: String to append when truncation occurs.

    Returns:
        The original text if its length is <= max_len, otherwise the truncated
        text with ellipsis appended.
    """
    if max_len < 0:
        return ''
    if max_len <= len(ellipsis):
        return ellipsis[:max_len]
    if len(text) <= max_len:
        return text
    return text[:max_len - len(ellipsis)] + ellipsis