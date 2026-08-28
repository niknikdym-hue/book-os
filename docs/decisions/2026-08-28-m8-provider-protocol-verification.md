# M8 provider protocol verification — 2026-08-28

**Status:** REVIEWED — Central Brain implementation evidence

This decision records the dated external API facts used by Task 009 Stage A after direct verification against current official provider documentation.

## Yandex AI Studio

- Native text completion endpoint: `https://ai.api.cloud.yandex.net/foundationModels/v1/completion`.
- Native completion requests support `jsonSchema` with a JSON Schema object.
- Native completion responses expose generated text under `result.alternatives[].message.text`, usage under `result.usage`, and exact returned model version under `result.modelVersion`.
- Native text embedding endpoint: `https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding`.
- Text embedding requests are one `text` per request with explicit `modelUri`; responses include `embedding`, `numTokens`, and `modelVersion`.

Official sources:
- https://yandex.cloud/ru/docs/ai-studio/prompts/yandexgpt/automation-ner
- https://aistudio.yandex.ru/docs/en/ai-studio/embeddings/api-ref/Embeddings/textEmbedding.html
- https://yandex.cloud/ru-kz/docs/foundation-models/text-generation/api-ref/TextGenerationAsync/completion

## GigaChat

- Target inference host: `https://api.giga.chat`.
- New inference requests use `/v1/chat/completions` or `/v2/chat/completions`; Stage A uses `/v1/chat/completions`.
- Access-token exchange remains `https://ngw.devices.sberbank.ru:9443/api/v2/oauth`.
- Product runtime scope is commercial `GIGACHAT_API_B2B` or `GIGACHAT_API_CORP`; personal `PERS` is not a product-runtime default.
- Strict structured output for v1 uses `response_format.type=json_schema`, `response_format.schema`, and `response_format.strict=true`.
- Production TLS verification remains enabled; an explicit trusted CA bundle may be supplied when required. `verify=False` is prohibited in BOOK OS production code.
- `GigaChat-3-Ultra` remains unavailable to paid legal-entity/commercial access under the dated provider terms and is not a production candidate for BOOK OS M8.

Official sources:
- https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/gigachat-api
- https://developers.sber.ru/docs/ru/gigachat/guides/structured-output
- https://developers.sber.ru/docs/ru/gigachat/models/gigachat-3-ultra
- https://developers.sber.ru/docs/ru/gigachat/certificates

This is dated provider-policy evidence, not permanent provider authority. Any material provider endpoint, model, commercial-term, or structured-output change requires capability-matrix re-verification before production promotion.
