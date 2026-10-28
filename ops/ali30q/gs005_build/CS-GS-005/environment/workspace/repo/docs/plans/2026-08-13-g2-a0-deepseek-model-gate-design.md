# G2-A0 DeepSeek model gate design

**Status:** approved design; no paid call or model-backed runtime is authorized
by this document

**Platform baseline:**
`417d5990cd694616365882d729a95e1ea9bf2185`

## Outcome

G2-A0 establishes one narrow capability gate for the first model-backed
Nautilus coding step. It tests whether one exact DeepSeek model can turn a
fully synthetic defect description into a schema-valid candidate patch while
remaining inside the existing Platform evidence boundary.

The selected candidate is `deepseek-v4-flash-0731` with thinking enabled. The
user has confirmed that the account has balance and that this versioned model
is available in the official DeepSeek console. Public DeepSeek API
documentation currently lists `deepseek-v4-flash` and `deepseek-v4-pro`, not
the dated identifier. G2-A0 therefore treats the user's confirmation as an
input to test, not as conformance evidence. Only an exact response read-back
from the official OpenAI-compatible endpoint can admit the dated model.

G2-A0 is a capability receipt, not V5 runtime admission. It does not authorize
a real repository, general tools, a model fallback, autonomous work, Compass
learning, deployment, push, merge, production data, business data, or FDE.

## Considered approaches

1. Use the floating `deepseek-v4-flash` identifier. This matches public API
   documentation but cannot prove that a later run used the same dated model.
2. Request `deepseek-v4-flash-0731` from the official OpenAI-compatible
   endpoint and require the response model identifier to match byte-for-byte.
   This is selected because it tests the user's version pin without accepting
   a silent alias.
3. Use an Anthropic-compatible or third-party gateway. This is rejected. The
   official Anthropic-compatible endpoint may map unsupported names, and a
   third-party gateway cannot independently prove the serving version.

## Fixed authority and ownership

Platform owns the gate contract, exact request policy, evidence allowlist,
budget decision, and final `admitted`, `rejected`, or `inconclusive` result.
It does not become the long-term model host and does not receive model signing
or repository execution authority.

DeepSeek owns model serving and returns provider metadata. Provider metadata
is evidence to validate; it cannot override the Platform request policy.

V5 is unchanged during G2-A0. After this gate passes, V5 may separately propose
a narrow model adapter that consumes the admitted contract. The existing V5
multi-provider client is not reused because it includes retries, fallback,
environment-derived provider selection, and unrelated runtime side effects.

Compass is unchanged and receives no prompt, reasoning, response, API key, or
experience candidate. A later G2 design may request a read-only coding quality
capsule through the normal owner review path.

## Exact provider request policy

The only permitted network origins are:

- `https://api.deepseek.com/user/balance`; and
- `https://api.deepseek.com/chat/completions`.

The request policy is fixed as follows:

- protocol: OpenAI Chat Completions;
- model: `deepseek-v4-flash-0731`;
- `thinking.type`: `enabled`;
- `reasoning_effort`: `max`;
- response format: `json_object`;
- streaming: false for the first gate;
- retry count: zero;
- fallback providers: empty;
- redirects: prohibited;
- environment proxy inheritance: prohibited;
- `temperature`, `top_p`, `presence_penalty`, and `frequency_penalty`: absent;
- tools and `tool_choice`: absent; and
- bounded input, output, wall time, and CNY cost.

Thinking output is required but is never logged or persisted. The first gate
does not use tools, so it does not need multi-turn `reasoning_content` replay.
Any later tool-using adapter must separately prove the provider-specific
reasoning replay rules before admission.

## Synthetic coding fixture

The model receives one deterministic, no-business-data Python repair task. The
fixture is created under a disposable temporary directory and contains:

- a small module with one bounded defect;
- a public behavior description;
- one public example;
- a fixed output JSON schema; and
- an opaque request identifier containing no account or human identity.

The prompt does not include a precomputed patch. The expected patch and hidden
oracle remain outside the model request. The output object contains exactly:

- `artifact_version`;
- `language`;
- `unified_diff`;
- `summary_code`; and
- `claimed_test_scope`.

The gate rejects Markdown fences, prose outside JSON, extra fields, absolute
paths, path traversal, binary patches, multiple-file changes, source-tree
paths, commands, URLs, credentials, and a diff that touches anything except
the disposable fixture module.

An independent local verifier parses and applies the patch only to a fresh
copy of the disposable fixture, runs the hidden oracle without network, and
deletes both copies afterward. The model never receives a shell, file API,
ToolGateway, repository mount, database, or signing key.

## Model identity and response validation

A successful HTTP status is not admission. The response must satisfy all of
the following:

- returned `model` exactly equals `deepseek-v4-flash-0731`;
- `system_fingerprint` is present and valid for hashing;
- `reasoning_content` is non-empty;
- final `content` is one JSON object with the exact output allowlist;
- finish reason is an allowed terminal state;
- input, output, cache-hit, and cache-miss usage fields are valid non-boolean
  integers; and
- the independently applied candidate passes the hidden oracle.

If the official endpoint rejects the dated identifier, returns the floating
identifier, omits model identity, or silently maps it, the result is
`rejected:model_identity_unproven`. G2-A0 does not retry with another model.

## Budget and idempotency boundary

The normal run makes one paid completion call. The hard cap is three calls,
but no automatic retry path exists. The run obtains account balance before and
after the completion through the official balance endpoint and computes a
usage-based upper bound from the frozen price snapshot. Admission requires:

- available balance before the call;
- completion call count exactly one;
- calculated cost and observed balance delta each no greater than CNY 5;
- no negative or malformed usage; and
- no unexplained second model call.

The same canonical request is replayed after the first result inside the same
gate execution. It must return the already validated result with provider call
count unchanged. A changed payload under the same idempotency key conflicts
before network I/O.

This gate does not claim crash-safe, cross-process exactly-once delivery to an
external model API. A process crash after provider acceptance but before local
result recording is `inconclusive`, and the operator must not automatically
call again. Durable external-call reservation is a later production design
gate, not something G2-A0 silently claims to solve.

## Secret and evidence policy

The API key is supplied only to the paid-run process through a fresh secret
slot. It must not come from the Git-tracked V5 `.env.bak`, appear in command
arguments, be printed, be written to a file, enter Platform persistence, or be
passed to V5, Compass, the fixture, or the verifier.

The committed evidence object contains only an exact allowlist:

- gate and contract versions;
- Platform baseline and implementation commit;
- provider origin identifier;
- requested and returned model identifiers;
- hashes of the canonical request, prompt, fixture, response content,
  reasoning content, system fingerprint, patch, and oracle;
- thinking and reasoning-effort policy;
- token counts and calculated cost in integer micros;
- redacted balance delta, not the account balance;
- provider call count and replay growth;
- verifier result;
- temporary-fixture cleanup result;
- forbidden capability counters; and
- final fixed decision and reason codes.

It excludes the API key, raw prompt, raw response, raw reasoning, raw balance,
account identifiers, request headers, local paths, commands, environment
values, and synthetic patch text. The committed evidence is canonical JSON,
LF-only, and byte-hashed.

## Fail-closed matrix

Offline tests must reject before any network call:

- wrong origin, path, protocol, or model;
- thinking disabled or missing;
- reasoning effort other than `max`;
- any sampling field, tool, retry, fallback, redirect, or proxy widening;
- duplicate JSON keys, extra fields, bool-as-int, malformed hashes, or raw
  secret/prompt/response fields;
- changed payload under an existing idempotency key; and
- unauthorized fixture paths or patch targets.

Injected fake responses must reject:

- returned model mismatch or missing identity;
- missing or empty reasoning;
- malformed or extra output fields;
- invalid usage or excessive calculated cost;
- patch traversal, extra files, commands, or hidden-oracle failure; and
- evidence claiming a call, test, cleanup, or replay result that did not occur.

The live run must stop on authentication failure, insufficient balance,
unsupported model, rate limit, timeout, server error, malformed response,
identity mismatch, budget breach, or inconclusive balance read-back. It may not
retry or change models.

## Acceptance and stop condition

G2-A0 is admitted only when offline tests and one separately authorized live
run prove all fixed bindings, exact model identity, non-empty thinking,
schema-valid output, hidden-oracle success, one-call replay behavior, cost cap,
secret non-persistence, and cleanup. Independent review must report High=0 and
Medium=0.

Admission means only that this exact model and request policy are eligible as
an input to a future V5 Shadow Coding adapter design. It does not authorize
that adapter, another paid call, a real repository, autonomous coding,
learning, deployment, push, or merge. Any of those requires a new versioned
plan and separate user approval.
