from rigol_dashboard.capture_rigol import Rigol

def test_parse_ascii_reply():
    assert Rigol._parse_ascii_reply(b"#91234567895.5,6.6\n") == [5.5, 6.6]

    # no trailing newline
    _in = b'#90000155992.219998e+00,9.999949e-02'
    out = [2.219998, 0.09999949]

    assert Rigol._parse_ascii_reply(_in) == out
