def test_index_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
