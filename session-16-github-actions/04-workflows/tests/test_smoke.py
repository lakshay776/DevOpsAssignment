# Minimal test so build.yml's "pip install -r requirements.txt" and
# "python -m pytest" steps have something to run.


def test_smoke():
    assert 1 + 1 == 2
