from contextlib import asynccontextmanager
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from utility_service.domain_services.edit_geometry.canonicalization import prepare_geometry
from utility_service.domain_services.edit_geometry.policy import GeometryPolicy
from utility_service.domain_services.edit_geometry.structure import validate_transition
from utility_service.domain_services.edit_geometry.types import GeometryValue
from utility_service.infrastructure.postgresql.geometry_codec import (
    decode_geometry,
    encode_geometry,
)
from utility_service.infrastructure.postgresql.models.user import UserRole
from utility_service.infrastructure.postgresql.models.work_order import EditVersionCommandState
from utility_service.infrastructure.postgresql.repository_rows.edit_geometry import (
    EditGeometryContext,
    EditGeometryDefaultState,
    EditGeometryFeature,
    GeometryWriteResult,
    LockedEditVersion,
    PreparedGeometryHandle,
    ValidatedGeometryChange,
)
from utility_service.infrastructure.postgresql.repository_rows.edit_version_command import (
    EditVersionCommandRow,
)
from utility_service.use_cases.schemas.edit_version.geometry_save_in import GeometrySaveRequest
from utility_service.use_cases.services.edit_version_service import EditVersionService


BASELINE = GeometryValue(
    "LineString",
    tuple(
        tuple(Decimal(v) for v in p)
        for p in (
            ("65.52", "44.82"),
            ("65.525", "44.8205"),
            ("65.53", "44.82"),
        )
    ),
)
MOVED = replace(
    BASELINE,
    coordinates=(
        BASELINE.coordinates[0],
        (Decimal("65.525"), Decimal("44.8215")),
        BASELINE.coordinates[2],
    ),
)


class SaveFixture:
    """In-memory persistence double; geometry rules остаются настоящими."""

    def __init__(self):
        self.actor = SimpleNamespace(
            id=uuid4(),
            role=UserRole.EDITOR,
            is_active=True,
        )
        root = LockedEditVersion(
            uuid4(),
            uuid4(),
            uuid4(),
            1,
            1,
            "open",
            GeometryPolicy(Decimal("0.0000001")),
        )
        feature = EditGeometryFeature(
            uuid4(),
            "line",
            "unchanged",
            1,
            encode_geometry(BASELINE),
        )
        self.context = EditGeometryContext(
            root,
            "in_progress",
            self.actor.id,
            feature,
            replace(
                feature,
                operation=None,
            ),
            EditGeometryDefaultState(
                root.default_state_id,
                root.work_order_id,
                1,
                "active",
            ),
            b"test-aoi",
            (),
        )
        self.commands = {}
        self.history = set()
        self.mutations = 0
        self.validations = 0
        self.commits = 0
        self.fail_commit = False
        self.active = False
        self.service = EditVersionService(
            self,
            self,
            None,
            None,
            geometry_policy=GeometryPolicy(Decimal("0.001")),
            edit_version_repository=self,
        )

    @asynccontextmanager
    async def begin(self):
        assert not self.active
        self.active = True
        original = deepcopy((self.context, self.commands, self.mutations))
        try:
            yield self
            if self.fail_commit:
                raise RuntimeError("commit failed")
            self.commits += 1
        except BaseException:
            self.context, self.commands, self.mutations = original
            raise
        finally:
            self.active = False

    async def get_by_id(
        self,
        actor_id,
    ):
        assert self.active
        return self.actor if self.actor and self.actor.id == actor_id else None

    async def lock_version(
        self,
        *,
        work_order_id,
        edit_version_id,
    ):
        root = self.context.root
        return root if (root.id, root.work_order_id) == (edit_version_id, work_order_id) else None

    async def read_context(
        self,
        root,
        *,
        feature_id,
    ):
        return self.context

    def prepare_candidate(
        self,
        context,
        geometry,
    ):
        return PreparedGeometryHandle(
            context,
            prepare_geometry(
                geometry,
                BASELINE,
                context.root.policy,
            ),
        )

    async def validate_candidate(
        self,
        context,
        prepared,
    ):
        self.validations += 1
        transition = validate_transition(
            BASELINE,
            decode_geometry(context.current.geometry_ewkb),
            prepared.prepared,
        )
        return ValidatedGeometryChange(
            context,
            context.current.geometry_ewkb,
            encode_geometry(prepared.prepared.geometry),
            transition.operation,
            transition.is_noop,
            transition.vertex_index,
        )

    async def write_current(
        self,
        change,
    ):
        self.mutations += int(not change.is_noop)
        self.context = replace(
            self.context,
            current=replace(
                self.context.current,
                geometry_ewkb=change.after_ewkb,
                operation=change.operation,
            ),
        )
        return GeometryWriteResult(
            not change.is_noop,
            change.operation,
            change.before_ewkb,
            change.after_ewkb,
        )

    async def increment_revision(
        self,
        root,
    ):
        self.context = replace(
            self.context,
            root=replace(
                root,
                draft_revision=root.draft_revision + 1,
            ),
        )
        return self.context.root.draft_revision

    async def get_command(
        self,
        root,
        *,
        command_id,
    ):
        return self.commands.get(command_id)

    async def command_has_history(
        self,
        root,
        *,
        command_id,
    ):
        return command_id in self.history

    async def reserve_command(
        self,
        root,
        *,
        command_id,
        feature_id,
        actor_id,
        fingerprint,
    ):
        if command_id in self.commands:
            return False
        self.commands[command_id] = EditVersionCommandRow(
            command_id,
            root.id,
            feature_id,
            actor_id,
            fingerprint,
            EditVersionCommandState.RUNNING,
            False,
            None,
            None,
            None,
            None,
        )
        return True

    async def complete_command(
        self,
        root,
        *,
        command_id,
        payload,
    ):
        self.commands[command_id] = replace(
            self.commands[command_id],
            state=EditVersionCommandState.SUCCEEDED,
            response_status=200,
            response_payload=deepcopy(payload),
        )

    def request(
        self,
        geometry=MOVED,
        *,
        token=None,
        command_id=None,
    ):
        return GeometrySaveRequest(
            command_id or uuid4(),
            token or str(self.context.root.draft_revision),
            geometry,
        )

    async def save(
        self,
        request,
    ):
        return await self.service.save_geometry(
            work_order_id=self.context.root.work_order_id,
            edit_version_id=self.context.root.id,
            feature_id=self.context.current.feature_id,
            actor_id=self.context.assignee_user_id,
            request=request,
        )
