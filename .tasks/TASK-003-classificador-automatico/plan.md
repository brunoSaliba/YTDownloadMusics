# TASK-003 — Classificador automático de trilha

**Objetivo:** reduzir cerimônia classificando a trilha por regra determinística (`aip.py classify`), portado do PortalCliente.
**Arquivos:** `tools/aip.py`, `tools/tests/test_aip.py`, `.ai/classify.json`, `.ai/rubrics/complexity.md`, `.ai/workflows/task.md`, `AGENTS.md` §2.
**Regras:** sensível / >1 módulo / >15 arquivos de código → FEATURE; senão TASK/BUGFIX; só escalona. Config por projeto em `.ai/classify.json`.
**Testes:** 2.
**Segurança:** não toca trust boundary; caminho sensível sempre sobe para FEATURE.

## Revisão (passada única)
Diff lido: regex em raw strings, defaults genéricos, config opcional via JSON local do repositório (sem rede). Sem segredos nem dependências novas.
