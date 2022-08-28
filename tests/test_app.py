import pytest
from extracursus import app

@pytest.fixture()
def client():
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_index(client):
    resp = client.get("/", follow_redirects=True)

    assert resp.status_code == 200
    assert b"Extracursus" in resp.data

def test_redirect(client):
    resp = client.get("/pretty_grades")

    assert resp.status_code == 302
