import html as _html
from collections import deque
from html.parser import HTMLParser
from typing import Tuple, List

from telethon import helpers
from telethon.extensions.markup.base import TextDecoration
from telethon.tl import types


class HTMLToTelegramParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = ''
        self.entities = []
        self._building_entities = {}
        self._open_tags = deque()
        self._open_tags_meta = deque()

    def handle_starttag(self, tag, attrs):
        self._open_tags.appendleft(tag)
        self._open_tags_meta.appendleft(None)

        attrs = dict(attrs)
        EntityType = None
        args = {}
        if tag == 'strong' or tag == 'b':
            EntityType = types.MessageEntityBold
        elif tag == 'em' or tag == 'i':
            EntityType = types.MessageEntityItalic
        elif tag == 'u':
            EntityType = types.MessageEntityUnderline
        elif tag == 'del' or tag == 's':
            EntityType = types.MessageEntityStrike
        elif tag == 'blockquote':
            EntityType = types.MessageEntityBlockquote
        elif tag == 'code':
            try:
                # If we're in the middle of a <pre> tag, this <code> tag is
                # probably intended for syntax highlighting.
                #
                # Syntax highlighting is set with
                #     <code class='language-...'>codeblock</code>
                # inside <pre> tags
                pre = self._building_entities['pre']
                try:
                    pre.language = attrs['class'][len('language-') :]
                except KeyError:
                    pass
            except KeyError:
                EntityType = types.MessageEntityCode
        elif tag == 'pre':
            EntityType = types.MessageEntityPre
            args['language'] = ''
        elif tag == 'tg-emoji' or tag == 'emoji':
            EntityType = types.MessageEntityCustomEmoji
            args['document_id'] = int(attrs.get('emoji-id') or attrs.get('document_id'))
        elif tag == 'span' and attrs['class'] == 'tg-spoiler' or tag == 'tg-spoiler':
            EntityType = types.MessageEntitySpoiler
        elif tag == 'a':
            try:
                url = attrs['href']
            except KeyError:
                return
            if url.startswith('mailto:'):
                url = url[len('mailto:') :]
                EntityType = types.MessageEntityEmail
            else:
                if self.get_starttag_text() == url:
                    EntityType = types.MessageEntityUrl
                else:
                    EntityType = types.MessageEntityTextUrl
                    args['url'] = url
                    url = None
            self._open_tags_meta.popleft()
            self._open_tags_meta.appendleft(url)

        if EntityType and tag not in self._building_entities:
            self._building_entities[tag] = EntityType(
                offset=len(self.text),
                # The length will be determined when closing the tag.
                length=0,
                **args,
            )

    def handle_data(self, text):
        previous_tag = self._open_tags[0] if len(self._open_tags) > 0 else ''
        if previous_tag == 'a':
            url = self._open_tags_meta[0]
            if url:
                text = url

        for tag, entity in self._building_entities.items():
            entity.length += len(text)

        self.text += text

    def handle_endtag(self, tag):
        try:
            self._open_tags.popleft()
            self._open_tags_meta.popleft()
        except IndexError:
            pass
        entity = self._building_entities.pop(tag, None)
        if entity:
            self.entities.append(entity)


class HtmlDecoration(TextDecoration):
    def apply_entity(self, entity: types.TypeMessageEntity, text: str) -> str:
        type_ = type(entity)
        if type_ == types.MessageEntityBold:
            return f'<b>{text}</b>'
        elif type_ == types.MessageEntityItalic:
            return f'<i>{text}</i>'
        elif type_ == types.MessageEntityUnderline:
            return f'<u>{text}</u>'
        elif type_ == types.MessageEntityStrike:
            return f'<s>{text}</s>'
        elif type_ == types.MessageEntitySpoiler:
            return f'<span class="tg-spoiler">{text}</span>'
        elif type_ == types.MessageEntityCode:
            return f'<code>{text}</code>'
        elif type_ == types.MessageEntityPre:
            if entity.language:
                return (
                    f'<pre><code class="language-{entity.language}">{text}</code></pre>'
                )
            return f'<pre>{text}</pre>'
        elif type_ == types.MessageEntityTextUrl:
            return f'<a href="{entity.url}">{text}</a>'
        elif type_ == types.MessageEntityEmail:
            return f'<a href="mailto:{text}">{text}</a>'
        elif type_ == types.MessageEntityMentionName:
            return f'<a href="tg://user?id={entity.user_id}">{text}</a>'
        elif type_ == types.MessageEntityCustomEmoji:
            return f'<tg-emoji emoji-id="{entity.document_id}">{text}</tg-emoji>'
        return self.quote(text)

    def quote(self, value: str) -> str:
        return _html.escape(value, quote=False)

    def parse(self, text: str) -> Tuple[str, List[types.TypeMessageEntity]]:
        if not text:
            return text, []

        parser = HTMLToTelegramParser()
        parser.feed(helpers.add_surrogate(text))
        text = helpers.strip_text(parser.text, parser.entities)
        return helpers.del_surrogate(text), parser.entities


__all__ = ['HtmlDecoration']
