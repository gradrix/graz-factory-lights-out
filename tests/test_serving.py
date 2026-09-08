"""Launcher checks: fake Docker and a loopback-only HTTP fixture, no GPU needed."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("serve", Path(__file__).resolve().parents[1] / "scripts/serve.py")
serve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(serve)


def external(**changes):
    return {"mode": "external", "base_url": "http://127.0.0.1:30000/v1", "model": "gflo-local",
            "request_timeout": 1, "startup_timeout": 2, **changes}


def managed():
    return {**external(mode="managed"), "managed": {
        "image": "lmsysorg/sglang@sha256:" + "a" * 64, "model_path": "Qwen/test",
        "revision": "b" * 40, "name": "gflo-test", "gpu": "0", "context_length": 8192,
        "memory_fraction": 0.85, "shm_size": "4g", "server_options": {}}}


class ConfigTests(unittest.TestCase):
    def read(self, c):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "config.json"
            p.write_text(json.dumps(c))
            with patch.dict(os.environ, {}, clear=True):
                return serve.load(p)

    def test_local_default(self):
        self.assertEqual(self.read(external())["mode"], "external")

    def test_remote_requires_explicit_https(self):
        with self.assertRaises(serve.Failure):
            self.read(external(base_url="https://example.invalid/v1"))
        with self.assertRaises(serve.Failure):
            self.read(external(base_url="http://example.invalid/v1", allow_remote=True))
        self.read(external(base_url="https://example.invalid/v1", allow_remote=True))

    def test_credentials_and_unknown_fields_rejected(self):
        for changes in ({"base_url": "http://secret@localhost/v1"}, {"api_key": "secret"},
                        {"api_key_env": "bad\nname"}, {"startup_timeout": -1}):
            with self.subTest(changes=list(changes)), self.assertRaises(serve.Failure):
                self.read(external(**changes))

    def test_managed_pins_and_options(self):
        self.read(managed())
        for key, value in (("image", "lmsysorg/sglang:latest"), ("revision", "main"),
                           ("name", "unrelated"), ("server_options", {"trust-remote-code": "true"})):
            c = managed()
            c["managed"][key] = value
            with self.subTest(key=key), self.assertRaises(serve.Failure):
                self.read(c)

    def test_external_down_never_calls_docker(self):
        with patch.object(serve, "load", return_value=external()), patch.object(serve, "docker") as docker:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(serve.main(["down"]), 1)
            docker.assert_not_called()


class LifecycleTests(unittest.TestCase):
    def container(self, c, running=True, fingerprint=None):
        return {"Id": "owned-id", "State": {"Running": running}, "Config": {"Labels": {
            "org.gflo.serving": c["managed"]["name"], "org.gflo.spec": fingerprint or serve.fingerprint(c)}}}

    def test_external_up_only_waits(self):
        with patch.object(serve, "wait_ready", return_value={"ready": True}), patch.object(serve, "docker") as docker:
            serve.up(external())
            docker.assert_not_called()

    def test_matching_running_container_is_not_restarted(self):
        c = managed()
        with patch.object(serve, "inspect", return_value=self.container(c)), patch.object(serve, "docker") as docker, patch.object(serve, "wait_ready"):
            serve.up(c)
            docker.assert_not_called()

    def test_running_drift_is_rejected(self):
        c = managed()
        with patch.object(serve, "inspect", return_value=self.container(c, fingerprint="old")), patch.object(serve, "docker") as docker:
            with self.assertRaises(serve.Failure):
                serve.up(c)
            docker.assert_not_called()

    def test_stopped_matching_container_reuses_cache(self):
        c = managed()
        with patch.object(serve, "inspect", return_value=self.container(c, running=False)), patch.object(serve, "doctor"), patch.object(serve, "docker") as docker, patch.object(serve, "wait_ready"):
            serve.up(c)
            docker.assert_called_once_with("start", "owned-id")

    def test_foreign_container_is_not_adopted(self):
        data = [{"Config": {"Labels": {}}}]
        with patch.object(serve, "docker", side_effect=["foreign", json.dumps(data)]):
            with self.assertRaises(serve.Failure):
                serve.inspect(managed())

    def test_new_server_command_and_token_not_in_arguments(self):
        c = managed()
        c["managed"]["hf_token_env"] = "TEST_HF_TOKEN"
        with patch.dict(os.environ, {"TEST_HF_TOKEN": "private-value"}), patch.object(serve, "inspect", return_value=None), patch.object(serve, "doctor"), patch.object(serve, "docker") as docker, patch.object(serve, "wait_ready"):
            serve.up(c)
        calls = docker.call_args_list
        self.assertEqual(calls[0].args[:2], ("pull", c["managed"]["image"]))
        args = calls[1].args
        self.assertIn("--revision", args)
        self.assertIn("127.0.0.1:30000:30000", args)
        self.assertNotIn("private-value", args)
        self.assertEqual(calls[1].kwargs["env"]["HF_TOKEN"], "private-value")

    def test_transient_readiness_retries(self):
        with patch.object(serve, "ready", side_effect=[serve.NotReady("loading"), {"ready": True}]), patch.object(serve.time, "sleep"):
            self.assertEqual(serve.wait_ready(external()), {"ready": True})

    def test_dead_managed_server_fails_early(self):
        c = managed()
        with patch.object(serve, "ready", side_effect=serve.NotReady("loading")), patch.object(serve, "inspect", return_value=self.container(c, running=False)):
            with self.assertRaisesRegex(serve.Failure, "stopped"):
                serve.wait_ready(c)

    def test_docker_failure_is_not_treated_as_missing_container(self):
        with patch.object(serve, "docker", side_effect=serve.Failure("unavailable")):
            with self.assertRaises(serve.Failure):
                serve.up(managed())

    def test_remote_docker_host_rejected_before_command(self):
        with patch.dict(os.environ, {"DOCKER_HOST": "ssh://other-machine"}, clear=True), patch.object(serve.subprocess, "run") as run:
            with self.assertRaisesRegex(serve.Failure, "local Unix"):
                serve.docker("stop", "owned-id")
            run.assert_not_called()

    def test_stopped_drift_pulls_before_removing_owned_id(self):
        c = managed()
        with patch.object(serve, "inspect", return_value=self.container(c, running=False, fingerprint="old")), patch.object(serve, "doctor"), patch.object(serve, "docker") as docker, patch.object(serve, "wait_ready"):
            serve.up(c)
        self.assertEqual(docker.call_args_list[0].args[0], "pull")
        self.assertEqual(docker.call_args_list[1].args, ("rm", "owned-id"))
        self.assertNotIn("volume", [call.args[0] for call in docker.call_args_list])

    def test_down_is_idempotent(self):
        c = managed()
        with patch.object(serve, "load", return_value=c), patch.object(serve, "lock", return_value=contextlib.nullcontext()), patch.object(serve, "inspect", return_value=self.container(c, running=False)), patch.object(serve, "docker") as docker, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(serve.main(["down"]), 0)
            docker.assert_not_called()

    def test_startup_deadline(self):
        with patch.object(serve.time, "monotonic", side_effect=[0, 3]), patch.object(serve, "ready") as ready:
            with self.assertRaisesRegex(serve.Failure, "deadline"):
                serve.wait_ready(external(startup_timeout=2))
            ready.assert_not_called()

    def test_incomplete_smoke_response_rejected(self):
        with patch.object(serve, "ready"), patch.object(serve, "request", return_value={"choices": [{"finish_reason": "length", "message": {"content": '{"ok":true}'}}]}):
            with self.assertRaisesRegex(serve.Failure, "finish normally"):
                serve.smoke(external())

    def test_smoke_requires_boolean_not_integer(self):
        with patch.object(serve, "ready"), patch.object(serve, "request", return_value={"choices": [{"finish_reason": "stop", "message": {"content": '{"ok":1}'}}]}):
            with self.assertRaisesRegex(serve.Failure, "requested content"):
                serve.smoke(external())


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.response_mode = "ok"
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                fixture.calls.append(("GET", self.path, self.headers.get("Authorization")))
                if fixture.response_mode == "redirect":
                    self.send_response(302)
                    self.send_header("Location", "/must-not-follow")
                    self.end_headers()
                    return
                if fixture.response_mode == "unauthorized":
                    self.send_response(401)
                    self.end_headers()
                    self.wfile.write(b"secret response body")
                    return
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"data": [{"id": "gflo-local"}]}).encode())

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                fixture.calls.append(("POST", self.path, payload))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": '{"ok":true}'}}]}).encode())

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.c = external(base_url="http://127.0.0.1:" + str(self.server.server_port) + "/v1")

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def test_readiness_sends_no_prompt(self):
        self.assertTrue(serve.ready(self.c)["ready"])
        self.assertEqual([c[0] for c in self.calls], ["GET"])

    def test_synthetic_structured_smoke(self):
        self.assertTrue(serve.smoke(self.c, True)["smoke_passed"])
        payload = self.calls[-1][2]
        self.assertEqual(payload["max_tokens"], 256)
        self.assertEqual(payload["response_format"]["type"], "json_schema")

    def test_redirect_not_followed(self):
        self.response_mode = "redirect"
        with self.assertRaisesRegex(serve.Failure, "302"):
            serve.ready(self.c)
        self.assertEqual(len(self.calls), 1)

    def test_auth_failure_does_not_leak_body(self):
        self.response_mode = "unauthorized"
        self.c["api_key_env"] = "TEST_KEY"
        with patch.dict(os.environ, {"TEST_KEY": "private-token"}):
            with self.assertRaises(serve.Failure) as result:
                serve.ready(self.c)
        self.assertEqual(str(result.exception), "Endpoint returned HTTP 401")
        self.assertEqual(self.calls[0][2], "Bearer private-token")

    def test_wrong_model_fails(self):
        self.c["model"] = "wrong-model"
        with self.assertRaisesRegex(serve.Failure, "not advertised"):
            serve.ready(self.c)


if __name__ == "__main__":
    unittest.main()
