# Contributing to Nautilus | 智涌

We welcome contributions from the community.

## How to Contribute

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feat/my-feature`
3. **Commit** with conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
4. **Push** and open a Pull Request

## Priority Areas

| Area | What We Need | Layer |
|------|-------------|-------|
| Agent capabilities | New task type plugins (data analysis, NLP, etc.) | L1 |
| RAID strategies | Additional consensus algorithms beyond RAID 1/2/3/5 | Engine |
| Blockchain VAR | On-chain Verifiable Agent Registry with DID | L1 |
| Task templates | Templates for domain-specific tasks | L1 |
| Survival tuning | Better scoring formulas, anti-gaming | L2 |
| Observatory metrics | New health metrics and anomaly detectors | L3 |
| Proposal intelligence | Improve analysis quality at Level 2-3 | L3 |
| Docs & translations | Chinese/English documentation | All |

## Development Setup

```bash
# Clone
git clone https://github.com/chunxiaoxx/nautilus-core.git
cd nautilus-core

# Backend
cd phase3/backend
pip install -r requirements.txt
cp ../../.env.example .env  # Edit with your API keys
uvicorn main:app --reload

# Frontend
cd ../website
npm install
npm run dev
```

## Code Style

- Python: PEP 8, type hints, 88-char line limit (Black)
- TypeScript: ESLint + Prettier
- Commit messages: [Conventional Commits](https://www.conventionalcommits.org/)

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the three-layer design and file mapping.

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
