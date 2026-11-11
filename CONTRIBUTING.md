# Contributing

Use synthetic fixtures and dedicated temporary directories. Do not call live research sessions from unit tests. First reproduce a behavioral bug, then make the smallest change that fixes it. Existing local interfaces are version-sensitive: separate observed live results from fixture, protocol and static checks.

Run the commands in README before a pull request. Include the platform/app versions, actual behavior, intended behavior, test evidence and remaining limitations. Avoid raw app state, tokens, personal paths and transcripts. Do not add fallback transports that evade application refusals, impersonate a user, or alter model/permission settings without explicit user intent.

Documentation changes should preserve new-versus-existing-session routing and describe competing projects fairly. There is no claim of first-of-kind functionality. A future durable outbox or correlated reply reader should be tested under concurrent human input and uncertain writes before becoming the default.
