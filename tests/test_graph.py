from rigol_dashboard.upd import format_xtick


def test_format_xtick_rounding():
    assert format_xtick(0, 5e-07) == "0ns"
    assert format_xtick(1, 5e-07) == "500ns"
    assert format_xtick(2, 5e-07) == "1μs"
    assert format_xtick(3, 5e-07) == "1.5μs"
    assert format_xtick(4, 5e-07) == "2μs"
