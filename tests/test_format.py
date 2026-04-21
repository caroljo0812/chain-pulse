from chain_pulse.cli import _format_eth


def test_zero():
    assert _format_eth(0) == "0"


def test_one_eth_exact():
    assert _format_eth(10**18) == "1"


def test_dust_keeps_precision():
    # 1 wei must not collapse to "0" — float math used to do that
    assert _format_eth(1) == "0.000000000000000001"


def test_one_wei_above_one_eth():
    # the float-precision bug used to render this as "1"
    assert _format_eth(10**18 + 1) == "1.000000000000000001"


def test_no_trailing_zeros():
    # 0.5 ETH should render compact, not "0.500000"
    assert _format_eth(5 * 10**17) == "0.5"


def test_large_balance():
    assert _format_eth(123 * 10**18) == "123"
