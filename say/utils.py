import re
import json
from redbot.core import commands

START_CODE_BLOCK_RE = re.compile(r"^((```json)(?=\s)|(```))")


def _check_owner(ctx: commands.Context):
    if not ctx.guild:
        return True
    if ctx.author.id != ctx.guild.owner.id:
        return False
    return True


def cleanup_code(content):
    """Automatically removes code blocks from the code."""
    # remove ```json\n```
    if content.startswith("```") and content.endswith("```"):
        return START_CODE_BLOCK_RE.sub("", content)[:-3]

    # remove `foo`
    return content.strip("` \n")


async def _str_to_json(payload: str):
    try:
        return json.loads(cleanup_code(payload))
    except json.JSONDecodeError:
        return None
