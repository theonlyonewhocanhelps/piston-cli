import json
from typing import Optional

import requests
from piston.utilities.constants import FormatOutput


def format_output(output: str) -> str:
    """
    Format the output and return a tuple of the formatted output and a URL to the full output.

    Prepend each line with a line number. Truncate if there are over MAX_LINES lines or
    MAX_CHARACTERS characters and upload the full output to a paste service.
    """
    original_output = output  # To be uploaded to a pasting service if needed
    output = output.strip()
    paste_link = None
    truncated = False
    lines = output.count("\n")

    if lines > 0:
        output = [f"{i:02d} | {line}" for i, line in enumerate(output.split("\n"), 1)]
        output = output[: FormatOutput.max_lines]
        output = "\n".join(output)

    if lines > FormatOutput.max_lines:  # Limiting to only 20 lines
        truncated = True
        if len(output) >= FormatOutput.max_characters:
            output = f"{output[:FormatOutput.max_characters]}\n... (truncated - too long, too many lines)"
        else:
            output = f"{output}\n... (truncated - too many lines)"
    elif len(output) >= FormatOutput.max_characters:
        truncated = True
        output = f"{output[:FormatOutput.max_characters]}\n... (truncated - too long)"

    if truncated:
        paste_link = upload_output(original_output)

    output = output or "[No output]"

    msg = f"{output}\n"
    if paste_link:
        msg = f"{msg}\nFull output: {paste_link}"

    return msg


def upload_output(output: str) -> Optional[str]:
    """Upload the eval output to a paste service and return a URL to it if successful."""
    if len(output) > FormatOutput.max_paste_len:
        return "too long to upload"
    return send_to_paste_service(output, extension="txt")


def send_to_paste_service(contents: str, *, extension: str = "") -> Optional[str]:
    """
    Upload `contents` to the paste service.

    `extension` is added to the output URL
    When an error occurs, `None` is returned, otherwise the generated URL with the suffix.
    """
    upload_url = "https://emkc.org/snippets"
    for _ in range(FormatOutput.paste_failed_request_attempts):
        payload = json.dumps(
            {
                "language": "txt",
                "snip": contents,
            }
        )

        response = requests.post(upload_url, data=payload)
        status = response.status_code
        if status == 200:
            response = response.json()
            return "https://emkc.org" + response["url"]

    return f"[Pasting failed with status code {status}... Try again later.]"
