# Fedizine — Guia de uso

Este documento é para **quem edita e publica** o zine: instalação, Editorial Desk, fluxo mensal e atalhos pela linha de comando.

---

## O que você faz aqui

O Fedizine transforma atividade do Fediverso (RSS e ActivityPub) em uma **edição mensal**:

1. Você aponta **fontes** (perfis, feeds, instâncias).
2. O sistema **coleta fragmentos** (posts, fotos, links, etc.).
3. Você **curadoria** o que entra na edição.
4. Você **monta a issue**, gera **prova/PDF** e **publica** na web.

A timeline é contínua; o zine é um número com começo e fim.

---

## Primeira vez

### 1. Subir o ambiente

```bash
cp .env.example .env
# Edite .env com sua URL pública, senhas e e-mail do editor
docker compose up --build -d
```

Abra:

- Site público: `http://localhost:4927` (ou a porta em `HOST_PORT`)
- Editorial Desk: `http://localhost:4927/desk/login`

### 2. Criar o usuário editor

```bash
docker compose exec app fedizine create-user --password "sua-senha-segura"
```

Os dados padrão vêm do `.env` (`DEFAULT_USER_EMAIL`, `DEFAULT_USER_NAME`, `DEFAULT_USER_SLUG`). Você pode sobrescrever na criação:

```bash
docker compose exec app fedizine create-user \
  --email voce@seu.dominio \
  --name "Seu Nome" \
  --slug voce \
  --password "sua-senha-segura"
```

### 3. Entrar no Editorial Desk

1. Acesse `/desk/login`.
2. Use o e-mail e a senha cadastrados.
3. A home do desk mostra a **issue do mês corrente** (`YYYY-MM`) e contadores de fragmentos.

---

## Fluxo editorial (recomendado)

Ordem prática para cada mês:

```text
Sources → Collect → Fragments → Issues → Proof → Publish
```

### Sources (`/desk/sources`)

Aqui você cadastra de onde o Fedizine puxa conteúdo.

| Campo | Uso |
|-------|-----|
| Name | Nome amigável (ex.: "Meu Mastodon") |
| Platform | `mastodon`, `activitypub`, `rss`, `pixelfed`, `lemmy`, `peertube`, `bookwyrm`, etc. |
| Source type | Em geral `feed` |
| URL | Perfil ActivityPub, feed RSS/Atom ou URL da fonte |
| Handle | Opcional; útil para marcar conteúdo próprio na pontuação |

**Collect** em uma fonte dispara coleta em background (Celery). Os novos itens aparecem em **Fragments**.

Também existe coleta agendada: todo dia às 06:00 (timezone do Celery) roda coleta para todos os usuários ativos.

### Fragments (`/desk/fragments`)

Lista de itens coletados. Filtros por status:

| Status | Significado |
|--------|-------------|
| candidate | Recém-coletado; aguardando decisão |
| selected | Entra na edição |
| featured | Entra na edição com destaque |
| ignored | Descartado |

Em cada cartão:

- **Include** — marca como `selected`
- **Feature** — marca como `featured`
- **Ignore** — descarta
- **View original** — abre o post na origem

A pontuação automática (`score`) sugere seção e prioridade; você decide o que fica.

### Issues (`/desk/issues`)

Monta o rascunho da edição do **mês atual** a partir dos fragmentos `selected` e `featured`.

- **Build issue** — re-pontua itens do período e adiciona ao draft o que ainda não está na issue.
- A lista mostra seções e ordem dos fragmentos incluídos.

### Proof (`/desk/proof`)

Revisão antes de ir ao ar.

- **Generate PDF** — gera `zine.pdf` (A5) com WeasyPrint.
- **Publish** — publica a issue na web e atualiza home, RSS e snapshots em `storage/public/`.

Requisito: pelo menos **um fragmento** na issue; caso contrário a publicação é recusada.

Após publicar, você é redirecionado para `/{YYYY-MM}/` (ex.: `/2026-06/`).

---

## Site público (o que o leitor vê)

| URL | Conteúdo |
|-----|----------|
| `/` | Home com issue atual, arquivo e atalhos |
| `/{YYYY-MM}/` | Edição publicada do mês |
| `/{YYYY-MM}/zine.pdf` | PDF da edição |
| `/archive/` | Todas as edições publicadas |
| `/feed.xml` | RSS das edições |
| `/about/`, `/now/`, `/uses/`, `/links/` | Slash pages (texto placeholder, editável no código) |
| `/colophon/` | Colofão / créditos |

A interface pública está em **inglês**. O Editorial Desk também.

---

## Linha de comando (alternativa ao desk)

Útil para scripts, cron ou quando prefere o terminal:

```bash
# Coletar de todas as fontes
docker compose exec app fedizine collect

# Coletar uma fonte específica
docker compose exec app fedizine collect --source <uuid-da-fonte>

# Pontuar fragmentos do mês
docker compose exec app fedizine score --month 2026-06

# Montar issue
docker compose exec app fedizine build-edition --month 2026-06

# Só gerar PDF
docker compose exec app fedizine build-pdf --month 2026-06

# Publicar (web + PDF + RSS + home)
docker compose exec app fedizine publish --month 2026-06
```

Use `--user <slug>` se houver mais de um editor no banco.

---

## Ritmo mensal sugerido

1. **Início do mês** — revise fontes; rode collect (ou espere o agendamento).
2. **Durante o mês** — passe em Fragments: include, feature, ignore.
3. **Fim do mês** — Build issue → Proof → Generate PDF → leia a prova → Publish.
4. **Opcional** — baixe o PDF, compartilhe o link `/YYYY-MM/`, confira o RSS.

O desk sempre trabalha com a issue do **mês calendário atual** (`datetime.now()` → `YYYY-MM`). Para publicar outro período, use o CLI com `--month`.

---

## Dicas e limites

- **URLs externas** — só esquemas permitidos em `ALLOWED_URL_SCHEMES` (padrão: `https`). IPs privados são bloqueados se `BLOCK_PRIVATE_IPS=true`.
- **Cadastro público** — desligado por padrão (`ENABLE_PUBLIC_SIGNUP=false`). Novos editores só via CLI.
- **Snapshots** — após `publish`, HTML e PDF ficam em `storage/public/`. O app também serve edições dinâmicas do banco quando publicadas.
- **Rotas antigas** — `/mesa/*` não existe mais (404). Use `/desk/*`.

---

## Problemas comuns

| Sintoma | O que verificar |
|---------|------------------|
| Login falha | Usuário criado? E-mail correto? `fedizine create-user` |
| Collect não traz nada | URL da fonte, plataforma, rede; logs do worker: `docker compose logs worker` |
| Publish sem itens | Inclua fragmentos (Include/Feature) e rode Build issue |
| PDF 404 | Rode Generate PDF ou `fedizine build-pdf` antes de publicar |
| Site mostra dados antigos | Rode `publish` de novo; confira `APP_PUBLIC_URL` no `.env` |

Para arquitetura, stack e aparência visual, veja [how.md](how.md).
