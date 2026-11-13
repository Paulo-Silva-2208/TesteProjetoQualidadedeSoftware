# Relatório técnico de qualidade — AlocaSenac

**Análise do pacote:** `trbalho4na-qualidade-principal.zip`  
**Data:** 12/11/2026  
**Objetivo:** meta mínima de 80% de cobertura de linhas, com verificação de cobertura de ramos e restrições do SonarCloud.

## 1. Resumo executivo

O repositório contém aplicação Python/FastAPI, SQLAlchemy, PostgreSQL, testes pytest e BDD, fluxo GitHub Actions e SonarCloud. Os arquivos `pyproject.toml` e `.github/workflows/ci.yml` exigem **80% de cobertura de linhas e 70% de cobertura de ramos**, avaliados separadamente. O relatório pré-existente `docs/qualidade/relatorio-cobertura.md` registra **90,09% de linhas (1.091/1.211) e 71,22% de ramos (198/278)** na suíte local de 60 testes, com 3 testes de integração não selecionados. Essa é uma evidência histórica incluída no ZIP, **não uma medição independente da suíte completa** nesta análise.

Foi realizada medição independente dos testes puros de `app/dominio/regras.py`, que inicialmente tiveram **79% de cobertura combinada**, com 9 casos bem-sucedidos. Após ampliar testes de borda, estados inválidos, datas sem fuso e estoques inválidos, houve **14 testes bem-sucedidos e 100% de cobertura de linhas e ramos nesse módulo** (46/46 comandos e 12/12 ramos). O código da aplicação permaneceu inalterado; somente `tests/test_regras_dominio.py` foi ajustado.

**Importante:** atingir cobertura total no módulo não demonstra 80% de *código novo no pull request*. O SonarCloud calcula a cobertura das linhas novas em relação a uma branch de referência; sem o diff exato do PR e a execução do scanner, esse indicador não pode ser atestado. Um estado anterior informado pelo solicitante indica cobertura de 12,96% em código novo, que demanda investigação específica do PR.

## 2. Arquivos e riscos encontrados

| Área | Achado | Risco / ação |
| --- | --- | --- |
| `pyproject.toml` | `addopts = "-q -m 'not integration'"` | A execução padrão ignora integração; usar `-o addopts=""` para reproduzir o CI. |
| `.github/workflows/ci.yml` | CI roda pytest com integração e concorrência; define PostgreSQL 16 | Sem PostgreSQL/Docker, uma execução local pode ter resultados e skips diferentes do CI. |
| `tests/conftest.py` | `pg_engine` usa `DATABASE_URL` PostgreSQL ou inicia Testcontainers | Docker ausente ou indisponível dificulta testes de integridade/transações; apontar `DATABASE_URL` para base exclusivamente de testes. |
| `app/config.py` e `app/db.py` | Conexão padrão é PostgreSQL de desenvolvimento | Evitar executar testes de integração com banco de desenvolvimento; no CI é `alocasenac_test`. |
| `sonar-project.properties` | `sonar.sources=app`, `sonar.tests=tests`, `coverage.xml` | Confirme XML gerado e disponibilizado na etapa do Sonar; cobertura global e de código novo são métricas distintas. |
| `app/servicos/reservas.py` | Relatório histórico mostra 72% de cobertura combinada | Priorizar fluxos de conflito, status, alteração, cancelamento, concorrência e tratamento de exceções. |
| `app/servicos/relatorios.py` | Relatório histórico mostra 78% combinada | Priorizar filtros, entradas inválidas e resultados vazios. |
| `app/dominio/regras.py` | Antes: 79% combinada; depois: 100% nesta análise | Melhoria demonstrada, com testes de caminhos negativos. |
| `docs/qualidade/relatorio-cobertura.md` | Aponta três testes de integração pendentes e cinco casos de teste não executados | Não declarar que todos os requisitos foram validados só porque a cobertura percentual passou. |
| Dependências do ambiente de análise | Faltam `pytest-bdd`, `psycopg` e `ruff`; a instalação externa não funcionou | A suíte completa e a verificação de lint não puderam ser reproduzidas aqui. Use Python 3.12 e `pip install -r requirements.txt` no computador ou no CI. |

## 3. Medições executadas nesta análise

### Antes da alteração

```text
9 passed
app/dominio/regras.py  46 statements  7 miss  12 branches  5 partial  79% combined
```

### Depois da alteração

```text
14 passed
app/dominio/regras.py  46 statements  0 miss  12 branches  0 partial  100% combined
```

A medição isolada usou o comando abaixo, com banco SQLite em memória apenas para evitar importar as dependências de PostgreSQL; os testes verificam **funções puras** e não precisam de conexão de banco:

```bash
DATABASE_URL=sqlite+pysqlite:///:memory: python -m pytest --noconftest tests/test_regras_dominio.py -q --cov=app.dominio.regras --cov-branch --cov-report=term-missing
```

**Não interpretar** os 100% como cobertura de todo o `app/`, pois o escopo do comando foi apenas `app.dominio.regras`.

## 4. Como rodar no Windows (PowerShell)

Na pasta raiz extraída, onde ficam `pyproject.toml` e `requirements.txt`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se o PowerShell restringir a ativação do ambiente, execute o Python diretamente pelo caminho `.\.venv\Scripts\python.exe`, sem alterar a política de execução.

**Testes unitários (sem integração) e cobertura total do app:**

```powershell
python -m pytest -m "not integration" --cov=app --cov-branch --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-report=json:coverage.json
start .\htmlcov\index.html
```

**Executar toda a suíte como o CI:** iniciar PostgreSQL de teste (por exemplo `docker compose up -d postgres` (serviço identificado em `docker-compose.yml`)). A forma mais segura é definir o banco de teste explicitamente:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/alocasenac_test"
$env:APP_ENV = "test"
$env:AUTH_SECRET_KEY = "local-test-secret-key-not-for-production"
python -m pytest -o addopts="" --cov=app --cov-branch --cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-report=json:coverage.json
python -m ruff check .
```

**Validar os limiares separadamente:**

```powershell
python -c "import json,sys; t=json.load(open('coverage.json',encoding='utf-8'))['totals']; l=100*t['covered_lines']/t['num_statements']; b=100*t['covered_branches']/t['num_branches'] if t['num_branches'] else 100; print(f'Linhas: {l:.2f}% | Ramos: {b:.2f}%'); sys.exit(0 if l>=80 and b>=70 else 1)"
```

Após rodar o CI em um PR, confira o SonarCloud em **New Code → Coverage**, para identificar exatamente as novas linhas ainda não cobertas. Esta métrica pode ficar abaixo de 80% mesmo com cobertura global superior a 90%.

## 5. Sugestões de expansão de testes

1. Comparar o diff do PR com a branch `principal` e listar linhas de produção adicionadas/modificadas não cobertas.
2. Priorizar `app/servicos/reservas.py`, especialmente falhas de estado, cancelamentos, horários sobrepostos e validações de acesso.
3. Testar `app/servicos/relatorios.py` com filtros inválidos, intervalos vazios e resultados sem registros.
4. Manter integração/concorrência com PostgreSQL 16 e não substituí-la por SQLite, pois invariantes de transação e triggers não são equivalentes.
5. Não modificar exclusões de cobertura ou inserir testes sem asserções reais apenas para elevar o percentual.

## 6. Limites e conclusão

O arquivo do projeto já documenta resultado acima dos limites globais do pipeline, mas a validação integral não foi reproduzida no ambiente desta análise devido a dependências não instaladas e PostgreSQL/Docker indisponíveis. A melhoria **efetivamente executada e comprovada** neste trabalho é a passagem de 79% para 100% de cobertura combinada do módulo de regras, ampliando os testes existentes de 9 para 14 casos. O gargalo do SonarCloud para código novo deve ser tratado pela diferença do PR, não pela cobertura agregada da branch.
