Telethon-v1.24
==============

vanutp's fork of v1.24 branch of telethon

Parse modes
-----------

* Parse modes are reworked to be more accurate and more compatible with TDLib/Bot API.

HTML:

* Custom emojis are supported via ``<tg-emoji>`` or ``<emoji>`` tags with ``document``, ``document_id``, ``document-id``, ``emoji``, ``emoji_id`` or ``emoji-id`` attributes.
* Spoilers are supported via either ``<span class="tg-spoiler">`` or ``<tg-spoiler>`` tags.
* Pre blocks with language are supported via ``<pre><code class="language-<name>">`` tags.


Markdown:

* This implementation tries to be compatible with MarkdownV2 from TDLib/Bot API.
* The unparser is ported from aiogram, the parser is written from scratch.
* Escaping is done via backslash. Any character can be escaped.
* All entities and escapes are ignored in pre and code blocks.
  That means that you can't use ``````` in pre block and ````` in code block at all,
  but you can use any other characters inside them without escaping.

* All entities and escapes are ignored in URLs (but not in URL captions).
  That means you can't use ``)`` in URL.
  For example, ``[*bold \*text*](https://example.com/\\))`` is equivalent to
  ``<a href="https://example.com/\\"><b>bold *text</b></a>)``.

* You must escape ``_*[]()~`|\`` characters in any other context.
  Note that escaping ``>#+-={}.!`` characters is not required.

* Custom emojis are supported via ``[👍](tg://emoji?id=6334815245336315702)'`` syntax.


Telethon
========
.. epigraph::

  ⭐️ Thanks **everyone** who has starred the project, it means a lot!

|logo| **Telethon** is an asyncio_ **Python 3**
MTProto_ library to interact with Telegram_'s API
as a user or through a bot account (bot API alternative).

.. important::

    If you have code using Telethon before its 1.0 version, you must
    read `Compatibility and Convenience`_ to learn how to migrate.

What is this?
-------------

Telegram is a popular messaging application. This library is meant
to make it easy for you to write Python programs that can interact
with Telegram. Think of it as a wrapper that has already done the
heavy job for you, so you can focus on developing an application.


Installing
----------

.. code-block:: sh

  pip3 install telethon


Creating a client
-----------------

.. code-block:: python

    from telethon import TelegramClient, events, sync

    # These example values won't work. You must get your own api_id and
    # api_hash from https://my.telegram.org, under API Development.
    api_id = 12345
    api_hash = '0123456789abcdef0123456789abcdef'

    client = TelegramClient('session_name', api_id, api_hash)
    client.start()


Doing stuff
-----------

.. code-block:: python

    print(client.get_me().stringify())

    client.send_message('username', 'Hello! Talking to you from Telethon')
    client.send_file('username', '/home/myself/Pictures/holidays.jpg')

    client.download_profile_photo('me')
    messages = client.get_messages('username')
    messages[0].download_media()

    @client.on(events.NewMessage(pattern='(?i)hi|hello'))
    async def handler(event):
        await event.respond('Hey!')


Next steps
----------

Do you like how Telethon looks? Check out `Read The Docs`_ for a more
in-depth explanation, with examples, troubleshooting issues, and more
useful information.

.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _MTProto: https://core.telegram.org/mtproto
.. _Telegram: https://telegram.org
.. _Compatibility and Convenience: https://docs.telethon.dev/en/latest/misc/compatibility-and-convenience.html
.. _Read The Docs: https://docs.telethon.dev

.. |logo| image:: logo.svg
    :width: 24pt
    :height: 24pt
