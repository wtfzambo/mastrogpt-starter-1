import sys
sys.path.append("packages/zambo/reverse")
import reverse

def test_reverse():
    res = reverse.reverse({})
    assert res["output"] == "Please provide some input"
    args = {"input": "hello"}
    res = reverse.reverse(args)
    assert res["output"] == "olleh"
