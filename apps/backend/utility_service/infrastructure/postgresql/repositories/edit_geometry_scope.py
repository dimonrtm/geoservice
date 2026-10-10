from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    RepositoryProtocolError,
)


class EditGeometryScope:
    """Один tracker на session; handles живут только во внешней transaction."""

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.transaction = None
        self.invalid = False
        self.issued = {}
        self.generations = {}
        event.listen(
            session.sync_session,
            "after_transaction_create",
            self._created,
        )
        event.listen(
            session.sync_session,
            "after_transaction_end",
            self._ended,
        )

    @classmethod
    def for_session(
        cls,
        session: AsyncSession,
    ):
        key = "edit_version_repository_scope"
        if key not in session.info:
            session.info[key] = cls(session)
        return session.info[key]

    def _created(
        self,
        session,
        transaction,
    ):
        if transaction.nested and self.transaction is not None:
            self.invalid = True

    def _ended(
        self,
        session,
        transaction,
    ):
        if transaction is self.transaction:
            self.issued.clear()
            self.generations.clear()
            self.transaction = None
            self.invalid = False

    def require_transaction(self):
        transaction = self.session.sync_session.get_transaction()
        if transaction is None or not transaction.is_active:
            raise RepositoryProtocolError("Требуется активная внешняя транзакция.")
        if self.session.in_nested_transaction() or self.invalid:
            raise RepositoryProtocolError(
                "Точка сохранения несовместима с контекстом заблокированной версии."
            )
        if self.transaction is None:
            self.transaction = transaction
        if self.transaction is not transaction:
            raise RepositoryProtocolError("Транзакция контекста изменилась.")

    def issue(
        self,
        value,
        version_id,
        *,
        root=False,
    ):
        self.require_transaction()
        generation = (
            None
            if root
            else self.generations.get(
                version_id,
                0,
            )
        )
        self.issued[id(value)] = (
            value,
            version_id,
            generation,
        )
        return value

    def require(
        self,
        value,
    ):
        self.require_transaction()
        entry = self.issued.get(id(value))
        if entry is None or entry[0] is not value:
            raise RepositoryProtocolError(
                "Контекст получен в другой сессии или транзакции либо не был выдан репозиторием."
            )
        if entry[2] is not None and entry[2] != self.generations.get(
            entry[1],
            0,
        ):
            raise RepositoryProtocolError("Контекст уже использован или устарел.")

    def consume(
        self,
        version_id,
    ):
        self.generations[version_id] = (
            self.generations.get(
                version_id,
                0,
            )
            + 1
        )
        self.issued = {
            key: entry
            for key, entry in self.issued.items()
            if entry[1] != version_id or entry[2] is None
        }
