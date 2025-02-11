import os, requests as req
def test_reverse():
    url = os.environ.get("OPSDEV_HOST") + "/api/my/zambo/reverse"
    res = req.get(url).json()
    assert res.get("output") == "Please provide some input"
    args = {"input": "hello"}
    res = req.get(url, json=args).json()
    assert res.get("output") == "olleh"
