# Source Record

Use this compact source shape when collecting evidence:

```text
id | source_type | title | url | publisher | observed_at | confidence | summary | caveat
```

`source_type` values:

- official_site
- official_docs
- pricing
- changelog
- integrations
- help_center
- github_repository
- github_issue
- github_pull_request
- github_discussion
- community_post
- review_site
- comparison_page
- local_file
- local_doc
- local_config
- local_test
- local_route
- local_api
- local_schema
- local_dependency

For local project evidence, use:

```text
id | source_type | path | line | symbol_or_area | observed_at | confidence | summary | caveat
```

Do not use local evidence as a substitute for market demand. Local evidence can support claims about what exists, what is partial, what is risky, and what is cheap or expensive to change.

Confidence:

- high: official or directly observed source
- medium: repeated public signal with source URL or directly observed local code with clear scope
- low: one-off or weakly sourced claim

For local evidence, prefer short paraphrases with `path:line` references. Do not quote secrets or sensitive local content.
