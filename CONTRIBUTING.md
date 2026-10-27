# Contributing

Thank you for improving AutoRAG Router. Open an issue for major design changes; use focused pull requests and include tests for changes in routing, retrieval, validation or security.

## Local setup

```bash
python -m venv .venv
# Activate your environment.
python -m pip install -e '.[dev]'
python -m pytest -q
```

## Quality expectations

- Document backend limitations precisely. Do not describe fuzzy character similarity as a neural embedding model.
- Keep external cloud calls **opt-in**, never silently initiated in a basic installation.
- New routing strategies need at least a positive test, fallback behavior test and a trace explanation.
- Use parameterized storage queries; never trust document content as executable instructions.
- Preserve tenant separation. Multi-tenant production requires a verified identity-to-tenant mapping.
- Avoid committing secrets, datasets with private information, trained model weights or generated databases.

## License and contributions

AutoRAG Router uses a **personal noncommercial, source-available license**. Commercial use requires separate written permission from Md Najmul Hossain. Before submitting a pull request, make sure you have the rights to contribute the changes, and understand that accepted contributions will be distributed under the repository license. This is not an OSI-approved open-source license.

## Commercial demos

Use `scripts/make_promo.py` for a product-concept demo and label synthetic footage. Demonstrate actual runtime behavior with the included dashboard or API example.
