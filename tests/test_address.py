import pytest

from chain_pulse.address import InvalidAddress, normalize


def test_lowercase_gets_checksummed():
    assert normalize("0xd8da6bf26964af9d7eed9e03e53415d37aa96045") == \
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"


def test_already_checksummed_round_trips():
    a = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    assert normalize(a) == a


def test_whitespace_is_stripped():
    assert normalize("  0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045\n").startswith("0xd8")


@pytest.mark.parametrize("bad", [
    "",
    "0x",
    "d8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # no 0x
    "0xZZ" + "a" * 38,
    "0x" + "a" * 39,  # too short
    "0x" + "a" * 41,  # too long
])
def test_invalid_inputs_raise(bad):
    with pytest.raises(InvalidAddress):
        normalize(bad)


def test_non_string_raises():
    with pytest.raises(InvalidAddress):
        normalize(12345)  # type: ignore[arg-type]
