# Source Record Reference

Use this lightweight source record shape in Markdown tables or JSON drafts.

```text
id
source_type
title
url
publisher
observed_at
recency
confidence
summary
claims
caveats
```

Recommended `source_type` values:

```text
official_site
official_docs
pricing
changelog
integrations
help_center
github_repository
github_issue
github_pull_request
github_discussion
github_release
community_post
review_site
comparison_page
local_file
local_doc
local_config
local_test
local_route
local_api
local_schema
local_dependency
unknown
```

For local project evidence, use this lightweight shape:

```text
id
source_type
path
line
symbol_or_area
observed_at
confidence
summary
claims
caveats
```

Recommended local `source_type` values:

```text
local_file
local_doc
local_config
local_test
local_route
local_api
local_schema
local_dependency
```

Do not use local evidence as a substitute for market demand. Local evidence can support claims about what exists, what is partial, what is risky, and what is cheap or expensive to change.

Confidence guidance:

- `high`: official docs, product pages, changelogs, release notes, directly observed GitHub artifacts
- `medium`: well-sourced community threads, repeated GitHub issues, or directly observed local code with clear scope
- `low`: SEO comparison posts, uncited claims, old posts, one-off complaints

Do not quote long passages. Prefer short paraphrases with URLs.

For local evidence, prefer short paraphrases with `path:line` references. Do not quote secrets or sensitive local content.
