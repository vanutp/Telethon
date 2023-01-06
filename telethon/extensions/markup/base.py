from abc import abstractmethod, ABC
from typing import List, Tuple, Optional, Generator

from telethon.tl import types


class TextDecoration(ABC):
    @abstractmethod
    def apply_entity(self, entity: types.TypeMessageEntity, text: str) -> str:
        ...

    @abstractmethod
    def quote(self, text: str) -> str:
        ...

    @abstractmethod
    def parse(self, text: str) -> Tuple[str, List[types.TypeMessageEntity]]:
        """
        Parses the given message with markup and returns its stripped representation
        plus a list of the MessageEntity's that were found.

        :param text: the message with markup to be parsed.
        :return: a tuple consisting of (clean message, [message entities]).
        """
        ...

    def unparse(
        self, text: str, entities: Optional[List[types.TypeMessageEntity]] = None
    ) -> str:
        """
        Unparse message entities
        :param text: raw text
        :param entities: Array of MessageEntities
        :return:
        """
        return "".join(
            self._unparse_entities(
                self._add_surrogates(text),
                sorted(entities, key=lambda item: item.offset) if entities else [],
            )
        )

    def _unparse_entities(
        self,
        text: bytes,
        entities: List[types.TypeMessageEntity],
        offset: Optional[int] = None,
        length: Optional[int] = None,
    ) -> Generator[str, None, None]:
        if offset is None:
            offset = 0
        length = length or len(text)

        for index, entity in enumerate(entities):
            if entity.offset * 2 < offset:
                continue
            if entity.offset * 2 > offset:
                yield self.quote(
                    self._remove_surrogates(text[offset : entity.offset * 2])
                )
            start = entity.offset * 2
            offset = entity.offset * 2 + entity.length * 2

            sub_entities = list(
                filter(lambda e: e.offset * 2 < (offset or 0), entities[index + 1 :])
            )
            yield self.apply_entity(
                entity,
                "".join(
                    self._unparse_entities(
                        text, sub_entities, offset=start, length=offset
                    )
                ),
            )

        if offset < length:
            yield self.quote(self._remove_surrogates(text[offset:length]))

    @staticmethod
    def _add_surrogates(text: str):
        return text.encode("utf-16-le")

    @staticmethod
    def _remove_surrogates(text: bytes):
        return text.decode("utf-16-le")


__all__ = ["TextDecoration"]
