import httpx
import json
import pytest
import datetime
from pytz import timezone
from pathlib import Path
from unittest.mock import Mock
import urllib.parse

from rdflib import ConjunctiveGraph

from tdd import create_app
import tdd


DATA_PATH = Path(__file__).parent / "data"
TODAY = datetime.datetime.today().astimezone()
KNOWN_KEY_ERRORS = [
    "type",  # List of URIs or not
    "op",  # str => ["str"]
    "security",  # str => ["str"]
    "nosec_sc",
]
tdd.CONFIG["LIMIT_BATCH_TDS"] = 15
tdd.CONFIG["CHECK_SCHEMA"] = True


@pytest.fixture(autouse=True)
def patch_datetime_now(monkeypatch):
    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return datetime.datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone("UTC"))

        def astimezone(self, tz=timezone("UTC")):
            return super().astimezone(tz=tz)

    monkeypatch.setattr(datetime, "datetime", mydatetime)


@pytest.fixture
def test_client(httpx_mock):
    tdd.wait_for_sparqlendpoint = Mock(True)
    app = create_app()
    with app.test_client() as test_client:
        return test_client


class SparqlGraph:
    def __init__(self, filename=None, format="nquads"):
        self.graph = ConjunctiveGraph()
        if filename is not None:
            self.graph.parse(DATA_PATH / filename, format=format)

    def sparql_get_query(self, query, content_type):
        if "json" not in content_type or content_type == "application/ld+json":
            result = self.graph.query(query).serialize(format=content_type)
            return httpx.Response(status_code=200, content=result)

        json_result = json.loads(self.graph.query(query).serialize(format="json"))
        return httpx.Response(status_code=200, json=json_result)

    def sparql_update_query(self, query):
        if query:
            self.graph.update(query)
        return httpx.Response(status_code=204)

    def custom(self, request, **kwargs):
        content_type = request.headers.get("Accept", "application/json")
        parsed_request = urllib.parse.parse_qs(request.content.decode("utf-8"))
        if content_type == "*/*":
            content_type = "application/json"
        if "update" in parsed_request:
            return self.sparql_update_query(parsed_request["update"][0])

        if "query" in parsed_request:
            return self.sparql_get_query(parsed_request["query"][0], content_type)

        return httpx.Response(status_code=204)


@pytest.fixture
def mock_sparql_with_one_td(httpx_mock):
    graph = SparqlGraph("smart_coffe_machine_init.nquads")
    httpx_mock.add_callback(graph.custom)


@pytest.fixture
def mock_sparql_empty_endpoint(httpx_mock):
    graph = SparqlGraph()
    httpx_mock.add_callback(graph.custom)


@pytest.fixture
def mock_sparql_17_things(httpx_mock):
    graph = SparqlGraph("17_things.nquads")
    httpx_mock.add_callback(graph.custom)


@pytest.fixture
def clear_expired_td_mocked(monkeypatch):
    clear_expired_td_mocked = Mock()
    monkeypatch.setattr("tdd.clear_expired_td", clear_expired_td_mocked)
    return clear_expired_td_mocked


def assert_only_on_known_errors(diff):
    """This assert that the diff is only on known round tripping
    errors: title/titles, description/descriptions, type/@type
    """
    assert "_message" not in diff
    for key in diff.keys():
        if "_message" in diff[key]:
            assert key in KNOWN_KEY_ERRORS
        else:
            assert_only_on_known_errors(diff[key])


def add_registration_to_td(td):
    td["registration"] = {
        "created": "2022-03-17T17:03:48.095473+01:00",
        "retrieved": "2022-03-17T17:31:50.469472+01:00",
    }
