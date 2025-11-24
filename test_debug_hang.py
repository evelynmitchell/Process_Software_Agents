"""Debug test to see where it hangs."""
import pytest
import sys

@pytest.mark.e2e
class TestDebug:
    def test_hang_reproduction(self):
        """Reproduce the hang."""
        sys.stdout.write("ENTERING TEST METHOD\n")
        sys.stdout.flush()

        print("\n" + "="*80)
        print("After first print")
        sys.stdout.flush()

        assert True
