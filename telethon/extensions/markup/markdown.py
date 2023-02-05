import re
from typing import Tuple, List

from telethon import helpers
from telethon.extensions.markup.base import TextDecoration
from telethon.tl import types

DELIMITERS = {
    '*': types.MessageEntityBold,
    '_': types.MessageEntityItalic,
    '__': types.MessageEntityUnderline,
    '~': types.MessageEntityStrike,
    '||': types.MessageEntitySpoiler,
    '`': types.MessageEntityCode,
    '```': types.MessageEntityPre,
}

QUOTE_PATTERN = re.compile(r"([_*\[\]()~`|\\])")
URL_RE = re.compile(r'\[([\S\s]+?)\]\((.+?)\)')
URL_FORMAT = '[{0}]({1})'


def overlap(a, b, x, y):
    return max(a, x) < min(b, y)


class MarkdownDecoration(TextDecoration):
    def apply_entity(self, entity: types.TypeMessageEntity, text: str) -> str:
        type_ = type(entity)
        if type_ == types.MessageEntityBold:
            return f"*{text}*"
        elif type_ == types.MessageEntityItalic:
            return f"_{text}_"
        elif type_ == types.MessageEntityUnderline:
            return f"__{text}__"
        elif type_ == types.MessageEntityStrike:
            return f"~{text}~"
        elif type_ == types.MessageEntitySpoiler:
            return f"||{text}||"
        elif type_ == types.MessageEntityCode:
            return f"`{text}`"
        elif type_ == types.MessageEntityPre:
            if entity.language:
                return f"```{entity.language}\n{text}\n```"
            return f"```\n{text}\n```"
        elif type_ == types.MessageEntityTextUrl:
            return URL_FORMAT.format(text, entity.url)
        elif type_ == types.MessageEntityEmail:
            return URL_FORMAT.format(text, f'mailto:{text}')
        elif type_ == types.MessageEntityMentionName:
            return URL_FORMAT.format(text, f'tg://user?id={entity.user_id}')
        elif type_ == types.MessageEntityCustomEmoji:
            return URL_FORMAT.format(text, f'tg://emoji?id={entity.document_id}')
        return self.quote(text)

    def quote(self, value: str) -> str:
        return re.sub(pattern=QUOTE_PATTERN, repl=r"\\\1", string=value)

    def parse(self, text: str) -> Tuple[str, List[types.TypeMessageEntity]]:
        if not text:
            return text, []

        # Build a regex to efficiently test all delimiters at once.
        # Note that the largest delimiter should go first, we don't
        # want ``` to be interpreted as a single back-tick in a code block.
        delim_re = re.compile(
            '|'.join(
                '({})'.format(re.escape(k))
                for k in sorted(DELIMITERS, key=len, reverse=True)
            )
        )

        # Cannot use a for loop because we need to skip some indices
        i = 0
        result = []

        # Work on byte level with the utf-16le encoding to get the offsets right.
        # The offset will just be half the index we're at.
        text = helpers.add_surrogate(text)
        while i < len(text):
            m = delim_re.match(text, pos=i)

            # Did we find some delimiter here at `i`?
            if m:
                delim = next(filter(None, m.groups()))

                # +1 to avoid matching right after (e.g. "****")
                end = text.find(delim, i + len(delim) + 1)

                # Did we find the earliest closing tag?
                if end != -1:

                    # Remove the delimiter from the string
                    text = ''.join(
                        (
                            text[:i],
                            text[i + len(delim): end],
                            text[end + len(delim):],
                        )
                    )

                    # Check other affected entities
                    for ent in result:
                        # If the end is after our start, it is affected
                        if ent.offset + ent.length > i:
                            # If the old start is also before ours, it is fully enclosed
                            if ent.offset <= i:
                                ent.length -= len(delim) * 2
                            else:
                                ent.length -= len(delim)

                    # Append the found entity
                    ent = DELIMITERS[delim]
                    if ent == types.MessageEntityPre:
                        result.append(ent(i, end - i - len(delim), ''))  # has 'lang'
                    else:
                        result.append(ent(i, end - i - len(delim)))

                    # No nested entities inside code blocks
                    if ent in (types.MessageEntityCode, types.MessageEntityPre):
                        i = end - len(delim)

                    continue

            else:
                m = URL_RE.match(text, pos=i)
                if m:
                    # Replace the whole match with only the inline URL text.
                    text = ''.join(
                        (text[: m.start()], m.group(1), text[m.end():])
                    )

                    delim_size = m.end() - m.start() - len(m.group())
                    for ent in result:
                        # If the end is after our start, it is affected
                        if ent.offset + ent.length > m.start():
                            ent.length -= delim_size

                    result.append(
                        types.MessageEntityTextUrl(
                            offset=m.start(),
                            length=len(m.group(1)),
                            url=helpers.del_surrogate(m.group(2)),
                        )
                    )
                    i += len(m.group(1))
                    continue

            i += 1

        text = helpers.strip_text(text, result)
        return helpers.del_surrogate(text), result


__all__ = ["MarkdownDecoration"]
