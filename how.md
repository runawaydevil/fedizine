# Fedizine — Como funciona este projeto

Documento de referência completo sobre o **Fedizine**: o que é, para que serve, como está organizado, como se parece e como opera do Fediverso até a webzine publicada e o PDF imprimível.

**Domínio alvo:** [https://zine.murad.social](https://zine.murad.social)  
**Porta local (Docker):** `4927` → container na porta `8000`  
**Versão atual do código:** `0.1.0`

---

## 1. O que é o Fedizine

O Fedizine é um **gerador de webzines pessoais e PDFs imprimíveis** a partir da atividade pública de uma pessoa no **Fediverso**.

Ele não é uma rede social, um dashboard de métricas nem um agregador infinito de feeds. É uma **pequena prensa editorial** para a web pessoal: coleta fragmentos federados, cura uma seleção mensal e publica o resultado em dois formatos:

1. **Webzine navegável** — HTML com URL estável, leitura confortável, arquivo histórico e feed RSS.
2. **PDF A5 imprimível** — versão paginada, colecionável, gerada com WeasyPrint a partir de template próprio.

A ideia central:

> A timeline é contínua. O zine é uma edição.

Posts, fotos, vídeos, leituras, comunidades e links do Fediverso viram um número mensal com começo, meio e fim — preservando memória e presença digital fora das plataformas alheias.

---

## 2. Filosofia e princípios

### 2.1. A web pessoal importa

Cada editor pode ter:

- uma página inicial (`/`)
- edições mensais (`/YYYY-MM/`)
- slash pages IndieWeb (`/about/`, `/now/`, `/uses/`, `/links/`)
- arquivo (`/archive/`)
- colofão (`/colophon/`)
- feed RSS (`/feed.xml`)
- PDFs arquiváveis (`/YYYY-MM/zine.pdf`)

O conteúdo não desaparece numa timeline infinita; vira publicação editorial.

### 2.2. O Fediverso é fonte, não destino

O sistema coleta, normaliza, pontua, reorganiza e transforma conteúdo. O resultado não é cópia da timeline — é curadoria.

### 2.3. Curadoria vale mais que coleta

**Prioriza:** posts autorais, mídia, threads, leituras, vídeos, fotos, links com contexto, comunidades, eventos.

**Reduz:** respostas curtas, boosts sem comentário, duplicatas, ruído técnico.

### 2.4. Baixa interferência humana, mas não zero

Fluxo ideal:

```text
coleta automática → pontuação → seleção automática → montagem da edição → revisão leve → publicação
```

O editor revisa, aprova, rejeita ou destaca itens na **Mesa editorial** (`/mesa/`), sem montar tudo manualmente.

### 2.5. Multiusuário na arquitetura, uso pessoal no MVP

- Banco e modelos já têm `user_id` em fontes, itens e edições.
- Cadastro público desativado (`ENABLE_PUBLIC_SIGNUP=false`).
- Primeiro uso: editor padrão `pablo` em `zine.murad.social`.

---

## 3. Stack técnica

| Camada | Tecnologia |
|--------|------------|
| Linguagem | Python 3.12+ |
| API / servidor | FastAPI + Uvicorn |
| ORM / migrações | SQLAlchemy 2 + Alembic |
| Banco | PostgreSQL 16 |
| Filas / agendamento | Celery + Redis |
| Templates web | Jinja2 |
| Mesa editorial (UI admin) | HTMX + Alpine.js |
| PDF | WeasyPrint |
| HTTP cliente (coleta) | httpx, feedparser |
| Sanitização HTML | bleach |
| Containerização | Docker Compose |
| CLI | Typer (`fedizine`) |

**Dependências principais** estão em `pyproject.toml`. O pacote expõe o comando `fedizine` após `pip install -e .`.

---

## 4. Arquitetura em camadas

```text
┌─────────────────────────────────────────────────────────────┐
│  Público (site v3)          Mesa editorial (/mesa)          │
│  templates/public/          templates/admin/                 │
│  static/css/site.css        tema-papel.css + mesa.css        │
└──────────────┬──────────────────────────┬─────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────────────────────────────────────────┐
│  app/web/public.py          app/web/admin.py                 │
│  app/renderers/web_edition  app/services/*                   │
└──────────────┬──────────────────────────┬────────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────────────────────────────────────────┐
│  Conectores (RSS, ActivityPub) → Normalização → Editorial    │
│  app/connectors/            app/editorial/                   │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  PostgreSQL (users, sources, items, editions, zines, jobs)     │
└──────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Celery worker + beat (coleta periódica, tarefas assíncronas) │
└──────────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  storage/public/ — snapshots HTML, feed.xml, PDFs           │
│  storage/media/  — mídia baixada                             │
└──────────────────────────────────────────────────────────────┘
```

### 4.1. Pontos de entrada

- **`app/main.py`** — monta FastAPI, sessões, arquivos estáticos (`/static`), snapshots (`/files`), routers de health, público e admin.
- **`scripts/entrypoint.sh`** — espera PostgreSQL, roda `alembic upgrade head`, inicia Uvicorn.
- **`app/cli.py`** — comandos Typer para operação sem interface web.

### 4.2. Serviços Docker

| Serviço | Função |
|---------|--------|
| `app` | API + site + Mesa |
| `worker` | Celery worker (coleta, score, build, publish) |
| `scheduler` | Celery beat (coleta agendada) |
| `postgres` | Banco relacional |
| `redis` | Broker e backend Celery |

Volume persistente: `./storage` montado em `/data` no container (`/data/public`, `/data/media`, etc.).

---

## 5. Modelo de dados

### 5.1. Entidades principais

**User** — editor com `email`, `password_hash`, `display_name`, `slug`, `timezone`, `locale`.

**Source** — fonte fediversal do usuário: `name`, `platform`, `source_type` (feed, perfil…), `url`, `handle`, `config` (JSON), `enabled`.

**Item** — fragmento normalizado coletado:

- Identidade: `external_id`, `platform`, `content_type`
- Conteúdo: `title`, `content`, `summary`, `canonical_url`
- Autoria: `author_name`, `author_handle`
- Metadados: `published_at`, `media` (JSON), `tags`, `metrics`, `raw_data`
- Editorial: `score`, `status`, `suggested_section`

Status de item: `candidate` → `selected` / `featured` / `rejected` / `archived`.

**Edition** — edição mensal (`period_year_month` no formato `YYYY-MM`):

- `title`, `editorial_text`, `status`, `visibility`, `published_at`
- `sections_config` (JSON com seções padrão)
- Relação 1:N com `EditionItem`

**EditionItem** — liga item à edição com `section`, `sort_order`, `is_featured`, overrides de título/resumo.

**Zine** — artefato publicado: caminhos do PDF (`pdf_path`), web (`web_path`), timestamps.

**Job** — registro de tarefas assíncronas (coleta, etc.).

### 5.2. Seções editoriais padrão

```text
Editorial · Destaques · Fragmentos · Fotos · Leituras · Vídeos
Comunidades · Links comentados · Agenda · Rodapé
```

O pontuador (`app/editorial/scorer.py`) mapeia `content_type` → seção sugerida (ex.: `image` → Fotos, `book` → Leituras).

### 5.3. Pontuação editorial

Critérios positivos (exemplos):

- +30 conteúdo próprio / `own_content`
- +20 possui mídia
- +20 parte de thread
- +15 link comentado no texto
- +15 alt text em mídia
- +10 tags
- +10 engajamento (limitado)
- +5 publicado na última semana
- +10 texto longo (>280 caracteres)

Critérios negativos:

- −20 texto muito curto
- −30 repost/boost sem contexto

Limite de seleção automática: `EDITORIAL_SCORE_THRESHOLD` (padrão **50**). Itens acima passam de `candidate` para `selected`.

---

## 6. Conectores e plataformas

Registro em `config/platform_registry.yml`:

| Plataforma | Conector | Protocolos | Tipos de conteúdo |
|------------|----------|------------|-------------------|
| RSS / Atom | rss | rss, atom | article, link, status |
| ActivityPub | activitypub | activitypub | status, article, image, video, event |
| Mastodon | activitypub | activitypub, mastodon_api, rss | status, image, link, thread |
| Pixelfed | activitypub | activitypub, rss | image, album |
| Lemmy | activitypub | activitypub, rss | community_post, comment, link |
| PeerTube | activitypub | activitypub, peertube_api, rss | video, channel |
| BookWyrm | activitypub | activitypub, rss | book, review, quote |

Implementação em `app/connectors/` (`base.py`, `rss.py`, `activitypub.py`, `registry.py`).

Coleta com validação de URL (`app/utils/url_validator.py`): apenas HTTPS, bloqueio de IPs privados por padrão.

---

## 7. Fluxo editorial completo

### 7.1. Passo a passo (Mesa ou CLI)

```text
1. Cadastrar fontes        → /mesa/fontes ou API admin
2. Coletar fragmentos      → "Coletar agora" ou `fedizine collect`
3. Pontuar itens           → automático na coleta ou `fedizine score --month YYYY-MM`
4. Revisar fragmentos      → /mesa/fragmentos (aprovar, rejeitar, destacar)
5. Montar edição           → /mesa/edicao ou `fedizine build-edition --month YYYY-MM`
6. Gerar prova PDF         → /mesa/edicao/prova ou `fedizine build-pdf --month YYYY-MM`
7. Publicar                → botão publicar ou `fedizine publish --month YYYY-MM`
```

### 7.2. O que a publicação faz

`publish_service.publish_edition()`:

1. Renderiza HTML da edição → `storage/public/YYYY-MM/index.html`
2. Gera PDF → `storage/public/YYYY-MM/zine.pdf`
3. Atualiza `feed.xml` na raiz pública
4. Regenera `index.html` da home
5. Marca edição como `published`, `visibility=public`, grava `published_at`

O site dinâmico (FastAPI) serve as páginas em tempo real; os arquivos em `storage/public/` são **snapshots estáticos** para espelhamento ou CDN. Após mudanças de template, republicar com `fedizine publish` atualiza os snapshots.

### 7.3. Coleta agendada

Celery beat dispara `collect_all_users` conforme `COLLECTION_INTERVAL_HOURS` (padrão 24h). Tarefas individuais: `collect_source`, `score_items`, `build_edition_task`, `build_pdf_task`, `publish_edition_task`.

---

## 8. Rotas públicas

Todas as slash pages são registradas **antes** da rota `/{period}/` para evitar conflito com slugs de mês.

| Rota | Descrição |
|------|-----------|
| `/` | Home — hero, grid 2×2, edição atual, slash pages, fediverso, prateleira |
| `/about/` | Sobre a webzine |
| `/now/` | Foco atual (slash page) |
| `/uses/` | Ferramentas e bastidores |
| `/links/` | Vizinhos e atalhos |
| `/archive/` | Arquivo de todas as edições publicadas |
| `/colophon/` | Como o site é feito (stack, intenção) |
| `/feed.xml` | Feed RSS das edições |
| `/YYYY-MM/` | Edição mensal (seções + fragmentos) |
| `/YYYY-MM/zine.pdf` | PDF A5 da edição |
| `/health` | Health check |
| `/static/*` | CSS e assets |
| `/files/*` | Arquivos publicados em `storage/public` |

**Nota:** URLs com `@usuario` do documento de conceito (`Build_Docs/README.md`) ainda não estão implementadas; o MVP usa domínio único com período `YYYY-MM`.

---

## 9. Mesa editorial (admin)

Prefixo: **`/mesa`**. Autenticação por sessão (email + senha). Sem cadastro público.

| Rota | Função |
|------|--------|
| `/mesa/login` | Login |
| `/mesa/logout` | Encerrar sessão |
| `/mesa/` | Dashboard — contadores, edição do mês |
| `/mesa/fontes` | CRUD de fontes fediversais |
| `/mesa/fragmentos` | Lista e triagem de itens coletados |
| `/mesa/edicao` | Montagem da edição mensal |
| `/mesa/edicao/prova` | Preview e geração/publicação de PDF |

### 9.1. Aparência da Mesa (separada do site público)

A Mesa **não** usa o visual v3 colorido. Mantém estética **“papel de trabalho”**:

- `static/css/tema-papel.css` — tokens bege, serifas, ambiente calmo
- `static/css/mesa.css` — layout sidebar + área principal
- `templates/admin/base.html` — sidebar com links, HTMX e Alpine.js

Isso é intencional: o site público é cartaz IndieWeb; a Mesa é ferramenta de trabalho discreta.

---

## 10. Identidade visual — site público v3

O guia definitivo está em `Build_Docs/visual.md` (v3). A implementação vive em `static/css/site.css` e nos templates `templates/public/` + `templates/partials/`.

### 10.1. Frase-guia visual

> Fedizine deve parecer uma webzine fediversal viva, colorida e pessoal — algo entre um cartaz IndieWeb, uma homepage de bairro digital e uma pequena prensa editorial.

### 10.2. Referências de design

- **omg.lol** — cores doces, hero com personalidade, energia lúdica
- **slashpages.net** — títulos tipo `# /ABOUT`, tipografia forte, links com caráter
- **IndieWeb / Tildeverse** — web pessoal, URLs estáveis, slash pages visíveis
- **Zines xerocados** — contraste, cor, sombras duras (não minimalismo corporativo)

A v1/v2 “cozy bege” foi abandonada como direção principal. Bege (`#fff7f0`) existe só como fundo de apoio; a interface é **colorida e gráfica**.

### 10.3. Paleta de cores (tokens CSS)

```css
--bg: #fff7f0          /* fundo creme suave */
--surface: #ffffff
--ink: #171321         /* texto e contornos */

--pink: #ff4fa3
--pink-hot: #e40066    /* links */
--blue: #1677ff
--blue-sky: #b9e3ff
--cyan: #31c6d4
--purple: #8b5cf6
--violet: #6d28d9
--orange: #ff8a00
--yellow: #ffd43b
--green: #37d67a
--teal: #00a896
--red: #ff4d4d

--line: #171321
--muted: #5f5a6b

--shadow-hard: 8px 8px 0 #171321
--shadow-small: 4px 4px 0 #171321
```

### 10.4. Tipografia

- **Corpo:** system-ui stack, 18px, line-height 1.55
- **Títulos / marca:** Georgia (ou Arial Rounded MT Bold como fallback), peso 900, letter-spacing negativo
- **Hero H1:** clamp(2.5rem … 5.5rem) — quase cartaz
- **Labels / eyebrow:** uppercase, peso 900, caixa amarela com borda preta

### 10.5. Links

Todos os links usam:

```css
text-decoration: underline wavy currentColor;
text-underline-offset: 4px;
color: var(--pink-hot);
```

Hover muda para azul. Foco visível com outline azul (acessibilidade).

### 10.6. Componentes visuais

#### Topbar (`.topbar`)

- Marca com **bolha rosa** (`♥`) em círculo com borda 3px e sombra
- Nome **Fedizine** + domínio (`zine.murad.social`) em cinza
- **Nav pills** — cada link é um “botão” com borda preta, sombra offset e cor de fundo diferente (amarelo, azul céu, rosa claro, verde claro, roxo claro, laranja)

#### Hero (`.hero`)

- Bloco grande com gradiente azul céu, borda 4px, border-radius 32px, sombra dura
- Nuvem decorativa “**fedizine**” (`.hero-cloud`) — pill branca, texto rosa gigante
- **Eyebrow** amarelo: “★ webzine fediversal mensal”
- H1: “Uma pequena prensa para o Fediverso.”
- Subtítulo explicativo
- Botões de ação (`.btn-pink`, `.btn-blue`, `.btn-yellow`…)
- **Stickers** fediversais na base (ActivityPub, RSS, Mastodon, Pixelfed, BookWyrm, PeerTube, Lemmy)
- Pseudo-elemento `::after` com “colinas” verdes na parte inferior

#### Botões (`.btn`)

- Borda 3px preta, border-radius 14px, sombra 5px offset
- Hover: translate(3px, 3px) + sombra reduzida (efeito “pressionar”)
- Variantes por cor de fundo: pink, blue-sky, yellow, green, purple

#### Cards (`.card`)

- Borda 3px, radius 22px, sombra pequena
- Variantes coloridas: `.card-pink`, `.card-yellow`, `.card-blue`, `.card-green`, `.card-purple`, `.card-orange`
- `.label` — rótulo editorial pequeno acima dos títulos
- `.meta` — texto secundário em `--muted`

#### Home grid (`.home-grid`)

Grid 2×2 na home com quatro cartões:

1. **Rosa** — edição atual (mês, título, contagem de fragmentos/fontes, PDF pronto)
2. **Amarelo** — slash pages com links `#/about`, `#/now`, etc.
3. **Azul** — tag cloud do Fediverso
4. **Verde** — prateleira (edições por ano + link para arquivo)

#### Slash pages

- Título visual: `# /ABOUT`, `# /NOW`, etc. (`.slash-title`)
- Card amarelo ou roxo com lede e corpo
- Links `.slash` com estilo de slug

#### Página de edição

- **Capa** (`.edition-cover.card-pink`) — título, mês, texto editorial opcional, botões PDF/arquivo/início
- **Sumário** (`.toc.card-yellow`) — índice por seção com contagem
- **Coluna de leitura** — seções com `.card-editorial` por fragmento
- Partial `selo_origem.html` — indica plataforma/origem do item

#### Footer (`.footer`)

Colofão curto, links para arquivo, RSS, colophon, crédito Fedizine.

### 10.7. Responsividade

`@media (max-width: 760px)`:

- Topbar empilha
- Hero reduz padding e tamanhos
- Home grid vira coluna única
- Nav pills e botões ajustam espaçamento

### 10.8. Aliases de compatibilidade

Classes antigas ainda funcionam: `.button-primary` → `.btn-pink`, `.button-secondary` → `.btn-yellow`, `.site-shell`, `.selo`.

---

## 11. Templates — mapa de arquivos

```text
templates/
├── base.html                 # Layout público (site.css)
├── partials/
│   ├── site_header.html      # topbar + nav-pills
│   ├── site_footer.html      # footer colophon
│   ├── card_editorial.html   # card de fragmento (reuso)
│   └── selo_origem.html      # selo da plataforma de origem
├── public/
│   ├── home.html             # página inicial v3
│   ├── edition.html          # edição mensal
│   ├── archive.html          # arquivo
│   ├── colophon.html         # colofão
│   └── slash.html            # about, now, uses, links
├── admin/
│   ├── base.html             # layout Mesa
│   ├── login.html
│   ├── mesa.html             # dashboard
│   ├── fontes.html
│   ├── fragmentos.html
│   ├── edicao.html
│   └── prova.html
├── print/
│   └── zine_a5.html          # template PDF A5
└── feeds/
    └── rss.xml               # template RSS
```

Contexto Jinja da home é montado em `build_home_context()`:

- `latest`, `fragment_count`, `source_count`, `pdf_ready`, `month_label`
- `editions`, `editions_by_year`, `site_host`, `public_url`

Filtro customizado: `month_name` (ex.: `2026-06` → “Junho”).

---

## 12. PDF imprimível

- Template: `templates/print/zine_a5.html`
- CSS: `static/css/print-a5.css`
- Renderização: `app/renderers/print_edition.py` (WeasyPrint)
- Formato padrão: **A5**
- Saída: `storage/public/YYYY-MM/zine.pdf`

O PDF tem diagramação própria — não é “print da página web”. Margens, capa, sumário e colofão são pensados para impressão.

---

## 13. Feed RSS

- Template: `templates/feeds/rss.xml`
- Renderer: `app/renderers/feed_rss.py`
- Rota dinâmica: `/feed.xml`
- Snapshot estático: `storage/public/feed.xml` (atualizado na publicação)

---

## 14. Configuração e variáveis de ambiente

Arquivo modelo: `.env.example`. Principais variáveis:

| Variável | Significado |
|----------|-------------|
| `APP_PUBLIC_URL` | URL canônica do zine |
| `HOST_PORT` | Porta no host Docker (4927) |
| `DATABASE_URL` | PostgreSQL |
| `REDIS_URL` / `CELERY_*` | Filas Celery |
| `STORAGE_PATH`, `PUBLIC_PATH`, `MEDIA_PATH` | Caminhos de armazenamento |
| `DEFAULT_USER_*` | Seed do editor padrão |
| `EDITORIAL_SCORE_THRESHOLD` | Limiar de seleção automática |
| `COLLECTION_INTERVAL_HOURS` | Intervalo de coleta |
| `ENABLE_AI_ASSISTANT` | IA desligada no MVP |

Segurança: `ALLOWED_URL_SCHEMES=https`, `BLOCK_PRIVATE_IPS=true`, sessões com `APP_SECRET_KEY`.

---

## 15. Como subir e operar

### 15.1. Docker (recomendado)

```bash
cp .env.example .env
docker compose up --build -d
```

Site: **http://localhost:4927**

### 15.2. Primeiro usuário

```bash
docker compose exec app fedizine create-user --password "sua-senha-segura"
```

Login Mesa: **http://localhost:4927/mesa/login**

### 15.3. CLI editorial

```bash
docker compose exec app fedizine collect
docker compose exec app fedizine score --month 2026-06
docker compose exec app fedizine build-edition --month 2026-06
docker compose exec app fedizine build-pdf --month 2026-06
docker compose exec app fedizine publish --month 2026-06
```

### 15.4. Desenvolvimento local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

---

## 16. Estrutura de diretórios do repositório

```text
zine-murad/
├── app/
│   ├── connectors/       # RSS, ActivityPub
│   ├── core/             # config, database, security, deps
│   ├── editorial/        # scorer, normalizer, dedup
│   ├── models/           # SQLAlchemy
│   ├── renderers/        # web, PDF, RSS
│   ├── schemas/          # Pydantic
│   ├── services/         # coleta, edição, publicação, score
│   ├── utils/
│   ├── web/              # routers público + admin
│   ├── workers/          # Celery
│   ├── cli.py
│   └── main.py
├── templates/            # Jinja2
├── static/css/           # site.css, tema-papel, mesa, print-a5
├── migrations/           # Alembic
├── config/               # platform_registry.yml
├── storage/              # volume Docker (public, media)
├── scripts/              # entrypoint.sh
├── Build_Docs/           # documentação de conceito (README, visual, stack)
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md             # início rápido
└── how.md                # este documento
```

---

## 17. Privacidade e limites

- Coleta apenas conteúdo **público** autorizado pelas fontes configuradas.
- Itens rejeitados não entram na edição publicada.
- Sem coleta de DMs ou mídia privada.
- Tokens e segredos ficam em variáveis de ambiente, nunca no repositório.

---

## 18. Inteligência artificial

Desligada por padrão (`ENABLE_AI_ASSISTANT=false`). Usos futuros possíveis: resumos, títulos sugeridos, agrupamento temático. O MVP funciona **sem IA**.

---

## 19. Estado atual e próximos passos

### Implementado (v0.1)

- Docker Compose completo (app, worker, scheduler, postgres, redis)
- Conectores RSS e ActivityPub básico
- Normalização, pontuação, deduplicação
- Mesa editorial com login
- Site público **visual v3** (colorido, slash pages, hero, grid)
- Edições web + PDF A5 + RSS
- CLI `fedizine`
- Publicação com snapshots em `storage/public/`

### Pendente / melhorias naturais

- Conteúdo real nas slash pages (hoje só lede placeholder)
- Redesign visual da Mesa para alinhar ou contrastar melhor com v3
- URLs multiusuário (`/@slug/YYYY-MM/`)
- Mais conectores especializados (PeerTube API, etc.)
- Republicar snapshots após mudanças de template
- Webfonts display, ilustrações SVG no hero
- IA editorial opcional
- Cadastro público / convites (v0.4+)

---

## 20. O que este projeto não deve virar

```text
clone de rede social
feed infinito
painel de analytics
ferramenta de marketing
CMS empresarial sem alma
agregador de vaidade
```

Se perder a sensação de **casa digital**, **arquivo afetivo** e **publicação com voz própria**, falhou — mesmo que tecnicamente funcione.

---

## 21. Documentos relacionados

| Arquivo | Conteúdo |
|---------|----------|
| `README.md` | Início rápido, comandos essenciais |
| `Build_Docs/README.md` | Visão de produto, filosofia, roadmap conceitual |
| `Build_Docs/visual.md` | Guia visual v3 completo (paleta, componentes, checklist) |
| `Build_Docs/stack(1).md` | Stack e deploy em detalhe |
| `how.md` | Este documento — referência integral do projeto |

---

*Fedizine — uma pequena prensa para o Fediverso.*
