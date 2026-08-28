from pathlib import Path

p = Path('services/local-core/src/book_os_core/provider_lane.py')
s = p.read_text()
s = s.replace('import time\n', 'import time\nimport uuid\n')

start = s.index('class YandexAdapter:')
end = s.index('\n\ndef _embedding_result', start)
replacement = '''class YandexAdapter:
    provider_name = "yandex"

    def __init__(
        self,
        secrets: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://ai.api.cloud.yandex.net/foundationModels/v1/completion",
    ) -> None:
        self.secrets = secrets
        self.client = client or httpx.Client()
        self.endpoint = endpoint

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        try:
            key = self.secrets.get_secret("yandex_ai_studio_api_key")
        except Exception as exc:
            raise ModelProviderError("Yandex credential is unavailable") from exc
        response = self.client.post(
            self.endpoint,
            headers={"Authorization": f"Api-Key {key}", "Content-Type": "application/json"},
            json={
                "modelUri": request.model,
                "completionOptions": {
                    "stream": False,
                    "maxTokens": str(request.max_output_tokens),
                },
                "messages": [
                    {"role": "system", "text": prompt.developer_text},
                    {"role": "user", "text": request.section_objective},
                ],
                "jsonSchema": {
                    "schema": OpenAIResponsesAdapter.output_schema(request.task_type),
                },
            },
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"Yandex HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ModelOutputError("Yandex response must be an object")
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ModelOutputError("Yandex response has no result object")
        alternatives = result.get("alternatives")
        if not isinstance(alternatives, list) or not alternatives:
            raise ModelOutputError("Yandex response has no alternatives")
        first = alternatives[0]
        message = first.get("message") if isinstance(first, dict) else None
        text_value = message.get("text") if isinstance(message, dict) else None
        if not isinstance(text_value, str) or not text_value:
            raise ModelOutputError("Yandex response has no generated text")
        usage_raw = result.get("usage")
        usage = dict(usage_raw) if isinstance(usage_raw, dict) else {}
        if result.get("modelVersion") is not None:
            usage["model_version"] = str(result["modelVersion"])
        return ModelAdapterResult(
            str(payload.get("id")) if payload.get("id") else None,
            _validated_output(request, {"output": text_value}),
            usage,
        )


class GigaChatAdapter:
    provider_name = "gigachat"
    _COMMERCIAL_SCOPES = {"GIGACHAT_API_B2B", "GIGACHAT_API_CORP"}

    def __init__(
        self,
        secrets: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://api.giga.chat",
        auth_endpoint: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        scope: str = "GIGACHAT_API_B2B",
        ca_bundle: str | None = None,
        clock: Any = time.time,
    ) -> None:
        if scope not in self._COMMERCIAL_SCOPES:
            raise ValueError("GigaChat product runtime requires a commercial B2B/CORP scope")
        self.secrets = secrets
        self.client = client or httpx.Client(verify=ca_bundle if ca_bundle is not None else True)
        self.endpoint = endpoint.rstrip("/")
        self.auth_endpoint = auth_endpoint
        self.scope = scope
        self.clock = clock
        self._token: tuple[str, float] | None = None

    def _token_expiry(self, payload: dict[str, Any]) -> float:
        expires_in = payload.get("expires_in")
        if isinstance(expires_in, (int, float)):
            return self.clock() + float(expires_in)
        expires_at = payload.get("expires_at")
        if isinstance(expires_at, (int, float)):
            value = float(expires_at)
            if value > 10_000_000_000:
                value /= 1000.0
            return value
        return self.clock() + 1800.0

    def _access_token(self) -> str:
        if self._token and self._token[1] > self.clock() + 5:
            return self._token[0]
        try:
            auth = self.secrets.get_secret("gigachat_authorization_key")
        except Exception as exc:
            raise ModelProviderError("GigaChat credential is unavailable") from exc
        response = self.client.post(
            self.auth_endpoint,
            headers={
                "Authorization": f"Basic {auth}",
                "RqUID": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={"scope": self.scope},
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"GigaChat token HTTP {response.status_code}")
        payload = response.json()
        token = payload.get("access_token") if isinstance(payload, dict) else None
        if not isinstance(token, str) or not token:
            raise ModelProviderError("GigaChat token response is malformed")
        self._token = (token, self._token_expiry(payload))
        return token

    def generate(self, request: ModelTaskRequest, prompt: PromptTemplate) -> ModelAdapterResult:
        response = self.client.post(
            f"{self.endpoint}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Content-Type": "application/json",
            },
            json={
                "model": request.model,
                "messages": [
                    {"role": "system", "content": prompt.developer_text},
                    {"role": "user", "content": request.section_objective},
                ],
                "response_format": {
                    "type": "json_schema",
                    "schema": OpenAIResponsesAdapter.output_schema(request.task_type),
                    "strict": True,
                },
            },
        )
        if response.status_code >= 400:
            raise ModelProviderError(f"GigaChat HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise ModelOutputError("GigaChat response must be an object")
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ModelOutputError("GigaChat response has no choices")
        first = choices[0]
        finish_reason = str(first.get("finish_reason") or "")
        if finish_reason.casefold() in {"blacklist", "content_filter", "refusal"}:
            raise ModelProviderError(f"GigaChat refusal: {finish_reason}")
        message = first.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        usage_raw = payload.get("usage")
        usage = dict(usage_raw) if isinstance(usage_raw, dict) else {}
        if payload.get("model") is not None:
            usage["model_version"] = str(payload["model"])
        return ModelAdapterResult(
            str(payload.get("id")) if payload.get("id") else None,
            _validated_output(request, {"output": content}),
            usage,
        )
'''
s = s[:start] + replacement + s[end:]

start = s.index('class YandexEmbeddingAdapter:')
end = s.index('\n\ndef run_live_probe', start)
replacement = '''class YandexEmbeddingAdapter:
    provider_name = "yandex"

    def __init__(
        self,
        secrets: SecretStore,
        *,
        client: httpx.Client | None = None,
        endpoint: str = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding",
    ) -> None:
        self.secrets = secrets
        self.client = client or httpx.Client()
        self.endpoint = endpoint

    def embed(self, texts: list[str], model: str) -> EmbeddingBatchResult:
        try:
            key = self.secrets.get_secret("yandex_ai_studio_api_key")
        except Exception as exc:
            raise EmbeddingProviderError("Yandex embedding credential is unavailable") from exc
        vectors: list[list[float]] = []
        model_version: str | None = None
        total_tokens = 0
        for text_value in texts:
            try:
                response = self.client.post(
                    self.endpoint,
                    headers={"Authorization": f"Api-Key {key}", "Content-Type": "application/json"},
                    json={"modelUri": model, "text": text_value},
                )
            except httpx.HTTPError as exc:
                raise EmbeddingProviderError("Yandex embeddings request failed") from exc
            if response.status_code >= 400:
                raise EmbeddingProviderError(f"Yandex embeddings HTTP {response.status_code}")
            payload = response.json()
            if not isinstance(payload, dict):
                raise EmbeddingOutputError("Yandex embeddings response must be an object")
            raw_vector = payload.get("embedding")
            if not isinstance(raw_vector, list):
                raise EmbeddingOutputError("Yandex embedding item is malformed")
            try:
                vectors.append([float(value) for value in raw_vector])
            except (TypeError, ValueError) as exc:
                raise EmbeddingOutputError("Yandex embedding is non-numeric") from exc
            returned_version = str(payload.get("modelVersion") or model)
            if model_version is None:
                model_version = returned_version
            elif returned_version != model_version:
                raise EmbeddingOutputError("Yandex embeddings returned inconsistent model versions")
            try:
                total_tokens += int(payload.get("numTokens") or 0)
            except (TypeError, ValueError):
                pass
        return EmbeddingBatchResult(
            self.provider_name,
            model,
            model_version or model,
            vectors,
            {"input_count": len(texts), "input_tokens": total_tokens},
        )


class GigaChatEmbeddingAdapter:
    provider_name = "gigachat"

    def __init__(self, generation: GigaChatAdapter) -> None:
        self._generation = generation

    def embed(self, texts: list[str], model: str) -> EmbeddingBatchResult:
        try:
            response = self._generation.client.post(
                f"{self._generation.endpoint}/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._generation._access_token()}",
                    "Content-Type": "application/json",
                },
                json={"model": model, "input": texts},
            )
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError("GigaChat embeddings request failed") from exc
        if response.status_code >= 400:
            raise EmbeddingProviderError(f"GigaChat embeddings HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise EmbeddingOutputError("GigaChat embeddings response must be an object")
        return _embedding_result(self.provider_name, model, payload)
'''
s = s[:start] + replacement + s[end:]
p.write_text(s)

p = Path('apps/desktop/src/ProviderLanePanel.tsx')
s = p.read_text()
s = s.replace(
    'Region: <strong>RU</strong> · Russia-ready (WRITER):{" "}\n        <strong>{writerReady ? "YES" : "NO"}</strong>',
    'Region: <strong>RU</strong> · WRITER production route:{" "}\n        <strong>{writerReady ? "AVAILABLE" : "UNAVAILABLE"}</strong>',
)
s = s.replace(
    'Production routing requires verified regional policy and an explicit role promotion.</p>',
    'Production routing requires verified regional policy and an explicit role promotion. A Russia-ready claim additionally requires Stage B live promotion acceptance.</p>',
)
p.write_text(s)

p = Path('apps/desktop/src/ProviderLanePanel.test.tsx')
s = p.read_text()
s = s.replace('Russia-ready (WRITER): NO', 'WRITER production route: UNAVAILABLE')
s = s.replace('Russia-ready (WRITER): YES', 'WRITER production route: AVAILABLE')
s = s.replace(
    'expect(container).not.toHaveTextContent(/use vpn/i);',
    'expect(container).not.toHaveTextContent(/use vpn/i);\n  expect(container).toHaveTextContent("Russia-ready claim additionally requires Stage B");',
)
p.write_text(s)

p = Path('services/local-core/tests/test_provider_lane.py')
s = p.read_text()
s = s.replace(
'''    def success(http_request: httpx.Request) -> httpx.Response:
        assert http_request.headers["Authorization"] == "Api-Key test-key"
        return httpx.Response(
            200,
            json={
                "id": "yc-1",
                "result": {"text": "Synthetic", "notes": []},
                "usage": {"tokens": 2},
            },
        )
''',
'''    def success(http_request: httpx.Request) -> httpx.Response:
        assert http_request.url.path == "/foundationModels/v1/completion"
        assert http_request.headers["Authorization"] == "Api-Key test-key"
        body = json.loads(http_request.content)
        assert body["jsonSchema"]["schema"]["type"] == "object"
        return httpx.Response(
            200,
            json={
                "id": "yc-1",
                "result": {
                    "alternatives": [
                        {"message": {"text": json.dumps({"text": "Synthetic", "notes": []})}}
                    ],
                    "usage": {"totalTokens": "2"},
                    "modelVersion": "yandexgpt:stage-a",
                },
            },
        )
''')
s = s.replace(
'''    assert result.output["text"] == "Synthetic"
    assert "test-key" not in repr(result)
''',
'''    assert result.output["text"] == "Synthetic"
    assert result.usage["model_version"] == "yandexgpt:stage-a"
    assert "test-key" not in repr(result)
''', 1)
s = s.replace(
'''    malformed = YandexAdapter(
        DictSecretStore({"yandex_ai_studio_api_key": "key"}),
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(200, json={"result": {"notes": []}})
            )
        ),
    )
    with pytest.raises(ModelOutputError, match="schema"):
        malformed.generate(request("yandex", "m"), SECTION_DRAFT_V1)
''',
'''    malformed = YandexAdapter(
        DictSecretStore({"yandex_ai_studio_api_key": "key"}),
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    json={
                        "result": {
                            "alternatives": [{"message": {"text": json.dumps({"notes": []})}}]
                        }
                    },
                )
            )
        ),
    )
    with pytest.raises(ModelOutputError, match="schema"):
        malformed.generate(request("yandex", "m"), SECTION_DRAFT_V1)

    provider_error = YandexAdapter(
        DictSecretStore({"yandex_ai_studio_api_key": "key"}),
        client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(503))),
    )
    with pytest.raises(ModelProviderError, match="503"):
        provider_error.generate(request("yandex", "m"), SECTION_DRAFT_V1)
''')

start = s.index('def test_gigachat_mocked_oauth_cache_rate_limit_and_secret_safety()')
end = s.index('\n\ndef test_live_runner_is_never_implicit', start)
giga_test = '''def test_gigachat_mocked_oauth_cache_rate_limit_refusal_and_provenance() -> None:
    calls: list[str] = []

    def handler(http_request: httpx.Request) -> httpx.Response:
        calls.append(str(http_request.url))
        if http_request.url.path.endswith("/api/v2/oauth"):
            assert http_request.url.host == "ngw.devices.sberbank.ru"
            assert http_request.headers["RqUID"]
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        assert http_request.url.host == "api.giga.chat"
        assert http_request.url.path == "/v1/chat/completions"
        body = json.loads(http_request.content)
        assert body["response_format"]["type"] == "json_schema"
        assert body["response_format"]["strict"] is True
        assert "json_schema" not in body["response_format"]
        return httpx.Response(
            200,
            json={
                "id": "gc-1",
                "model": "GigaChat-2-Pro:stage-a",
                "choices": [
                    {
                        "message": {"content": json.dumps({"text": "Synthetic", "notes": []})},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 4},
            },
        )

    adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "test-auth"}),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    first = adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1)
    second = adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1)
    assert first.output["text"] == "Synthetic"
    assert second.output["text"] == "Synthetic"
    assert first.usage["model_version"] == "GigaChat-2-Pro:stage-a"
    assert sum(url.endswith("/api/v2/oauth") for url in calls) == 1
    assert "test-auth" not in repr(adapter)

    with pytest.raises(ValueError, match="commercial"):
        GigaChatAdapter(DictSecretStore({}), scope="GIGACHAT_API_PERS")

    def limited(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path.endswith("/api/v2/oauth"):
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        return httpx.Response(429, json={"error": "rate limited"})

    limited_adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "auth"}),
        client=httpx.Client(transport=httpx.MockTransport(limited)),
    )
    with pytest.raises(ModelProviderError, match="429"):
        limited_adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1)

    def refusal(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path.endswith("/api/v2/oauth"):
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": "{}"},
                        "finish_reason": "blacklist",
                    }
                ]
            },
        )

    refusal_adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "auth"}),
        client=httpx.Client(transport=httpx.MockTransport(refusal)),
    )
    with pytest.raises(ModelProviderError, match="refusal"):
        refusal_adapter.generate(request("gigachat", "GigaChat-2-Pro"), SECTION_DRAFT_V1)
'''
s = s[:start] + giga_test + s[end:]

start = s.index('def test_mocked_embedding_adapters_return_exact_model_identity_and_validate_output()')
end = s.index('\n\ndef test_persisted_role_promotion', start)
embedding_test = '''def test_mocked_embedding_adapters_return_exact_model_identity_and_validate_output() -> None:
    yandex_requests: list[dict[str, object]] = []

    def yandex(http_request: httpx.Request) -> httpx.Response:
        assert http_request.url.path == "/foundationModels/v1/textEmbedding"
        body = json.loads(http_request.content)
        yandex_requests.append(body)
        assert "text" in body and "texts" not in body
        return httpx.Response(
            200,
            json={"modelVersion": "yandex-embed-v1", "embedding": [0.1, 0.2], "numTokens": "2"},
        )

    yandex_gateway = EmbeddingGateway(
        {
            "yandex": YandexEmbeddingAdapter(
                DictSecretStore({"yandex_ai_studio_api_key": "key"}),
                client=httpx.Client(transport=httpx.MockTransport(yandex)),
            )
        }
    )
    yandex_result = yandex_gateway.embed(["one", "two"], provider="yandex", model="m")
    assert yandex_result.model_version == "yandex-embed-v1"
    assert len(yandex_result.vectors) == 2
    assert len(yandex_requests) == 2

    malformed_gateway = EmbeddingGateway(
        {
            "yandex": YandexEmbeddingAdapter(
                DictSecretStore({"yandex_ai_studio_api_key": "key"}),
                client=httpx.Client(
                    transport=httpx.MockTransport(lambda _: httpx.Response(200, json={}))
                ),
            )
        }
    )
    with pytest.raises(EmbeddingOutputError):
        malformed_gateway.embed(["synthetic"], provider="yandex", model="m")

    def giga(http_request: httpx.Request) -> httpx.Response:
        if http_request.url.path.endswith("/api/v2/oauth"):
            return httpx.Response(200, json={"access_token": "access", "expires_in": 1800})
        assert http_request.url.path == "/v1/embeddings"
        return httpx.Response(
            200, json={"model": "giga-v1", "data": [{"embedding": [0.1, 0.2]}]}
        )

    giga_adapter = GigaChatAdapter(
        DictSecretStore({"gigachat_authorization_key": "auth"}),
        client=httpx.Client(transport=httpx.MockTransport(giga)),
    )
    giga_gateway = EmbeddingGateway({"gigachat": GigaChatEmbeddingAdapter(giga_adapter)})
    assert giga_gateway.embed(["synthetic"], provider="gigachat", model="m").model_version == "giga-v1"
'''
s = s[:start] + embedding_test + s[end:]
p.write_text(s)
