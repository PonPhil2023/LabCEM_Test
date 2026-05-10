from labcem.core.spec import DesignSpec


def test_spec_defaults():
    spec = DesignSpec()
    assert spec.type == "waveguide"
