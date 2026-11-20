from dataclasses import replace

import pytest

from utility_service.domain_services.edit_geometry.structure import internal_vertex_indices
from utility_service.domain_services.tests.geometry_test_support import line


BASE = line((0, 0), (1, 1), (2, 2), (3, 3))


@pytest.mark.parametrize(
    "current,expected",
    [
        (line(("-0", 0), (1, 1), (2, 2), (3, 3)), ()),
        (line((0, 0), (1, 1), (2, 4), (3, 3)), (2,)),
        (line((0, 1), (1, 1), (2, 2), (3, 3)), None),
        (line((0, 0), (1, 4), (2, 4), (3, 3)), None),
        (line((0, 0), (3, 3)), None),
        (replace(BASE, srid=3857), None),
        (replace(BASE, type="Point"), None),
    ],
)
def test_internal_vertex_indices(current, expected):
    assert internal_vertex_indices(BASE, current) == expected
