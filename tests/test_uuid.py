from uuid.generator import uuid7_str


def test_uuid7_str_has_uuid_format():
    value = uuid7_str()
    assert len(value.split("-")) == 5
    assert value[14] == "7"
