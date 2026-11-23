# Plan — FEAT-002 Cookies do YouTube

## Goal and acceptance criteria

Na VPS o YouTube responde "Sign in to confirm you're not a bot" para parte dos vídeos, tanto por IPv4 quanto por IPv6 e com qualquer `player_client`; o yt-dlp puro também falha. Evidência de 2026-11-23: `_k2ty4A5x1w` é bloqueado e `dQw4w9WgXcQ` passa. Decisão humana: usar cookies de uma **conta descartável** do YouTube.

1. Quando existir um arquivo de cookies (formato Netscape) não vazio em `YOUTUBE_COOKIES_FILE` (padrão `/run/secrets/youtube_cookies`), `info` e `download` usam esses cookies no yt-dlp.
2. O yt-dlp recebe uma **cópia filtrada** do arquivo, criada em um diretório temporário 0700 com o arquivo em 0600 dentro do tmpfs. A cópia é removida ao fim do job; se o job for morto, a varredura de diretórios antigos (10 min) a remove. O original nunca é passado ao yt-dlp, porque ele regrava o cookiefile ao sair.
3. Se o arquivo estiver ausente, vazio, ilegível, malformado, sem nenhuma linha válida ou maior que 1 MiB, o app roda sem cookies, como hoje, sem erro para o usuário. Linhas inválidas são descartadas em silêncio e nunca chegam ao yt-dlp.
4. O conteúdo dos cookies nunca aparece na resposta da API, nos logs do app nem no stdout do worker, nem no repositório, na imagem ou na CI.
5. Com cookies vencidos ou recusados, o erro continua mapeado para `blocked` (502), sem vazar detalhes.
6. Na VPS, com os cookies instalados, `POST /api/info` para `_k2ty4A5x1w` retorna 200. Isso é verificado no Production plan.

## Architecture

- Novo campo `Settings.cookies_file`, lido de `YOUTUBE_COOKIES_FILE` com padrão `/run/secrets/youtube_cookies`.
- No `worker.py`, um context manager `_cookie_copy(settings)`:
  - Abre o arquivo uma única vez com `O_RDONLY|O_NOFOLLOW`, confere com `fstat` que é arquivo regular (`S_ISREG`) e lê no máximo 1 MiB + 1 byte do mesmo descritor, sem TOCTOU nem symlink.
  - Filtra as linhas. Só passam linhas no formato Netscape (7 campos separados por tab, expiração numérica) cujo domínio, sem o prefixo `#HttpOnly_`, seja `youtube.com` ou `google.com` ou termine em `.youtube.com` ou `.google.com`. Comentários e linhas inválidas são descartados.
  - Se sobrar ao menos uma linha, grava `# Netscape HTTP Cookie File` mais as linhas válidas em `tempfile.mkdtemp(prefix="ytdl-")`. A gravação usa `os.open(O_CREAT|O_EXCL|O_WRONLY, 0o600)` e não `shutil.copy`, para não herdar o modo 0400 do original, o que quebraria o save do yt-dlp.
  - Entrega o caminho da cópia e apaga o diretório no `finally`.
  - `base_opts` recebe o caminho opcional e define `cookiefile`.
- `deploy/docker-compose.yml`:
  - Bloco `secrets: youtube_cookies: file: ./youtube-cookies.txt`, montado pelo Compose em `/run/secrets/youtube_cookies`, só leitura e fora da imagem.
  - O arquivo no host pertence ao uid 10001 com permissão 0400.
  - Fora do Swarm, o secret é um bind mount só leitura que mantém dono e modo do host. Se o arquivo não existir, o `compose up` falha, por isso a instalação sempre cria o arquivo, mesmo vazio.
  - Um arquivo vazio desliga a feature.
- O cookie não passa por nenhuma outra fronteira: Deno roda sem permissões, o ffmpeg não recebe cookies e a URL continua canônica, só do YouTube.

## Threat model

- **Ativos e classificação:**
  - Cookies de sessão de uma conta Google **descartável**. São um segredo; quem os tiver age como essa conta no YouTube.
  - Não há dados de usuários do site envolvidos.
- **Entradas controladas pelo atacante:** só a URL e o ID do vídeo, como hoje. Nenhuma entrada do usuário influencia o caminho, o conteúdo ou o uso dos cookies, que vêm apenas da configuração do operador.
- **Invariantes:**
  - **C1** — Cookies só são enviados ao YouTube/Google. Garantido por:
    - `allowed_extractors=["youtube"]` e a URL canônica reconstruída do ID (I1).
    - O filtro de domínio da cópia, que só deixa passar cookies de `youtube.com` e `google.com`.
    - O cookiejar do yt-dlp, que tem escopo de domínio; `googlevideo.com` e `ytimg.com` não recebem cookies.
  - **C2** — O conteúdo dos cookies nunca vai para resposta HTTP, log, stdout do worker, Git, imagem ou CI:
    - O worker emite só o JSON de `public_info` ou um código de erro.
    - Linhas malformadas são descartadas antes do yt-dlp. Sem isso, o yt-dlp imprimiria a linha crua no stderr (`cookies.py` "skipping cookie file entry" e o `LoadError`), e o `jobs.py` grava os últimos 500 bytes do stderr no log do app.
    - O `.dockerignore` é uma allowlist.
    - O `.gitignore` bloqueia `youtube-cookies.txt` e `deploy/*cookies*`.
  - **C3** — O arquivo original nunca é aberto para escrita nem passado ao yt-dlp. Só a cópia efêmera, com 0600 em diretório 0700, é usada.
  - **C4** — Sem cookies, o app degrada para o comportamento atual e não falha. Os cookies não são um controle de segurança, então "fail-open" aqui significa apenas perder o contorno do bloqueio.
  - **C5** — Limites de tamanho e tipo: aceita só arquivo regular de até 1 MiB, aberto com `O_NOFOLLOW` e verificado com `fstat` no mesmo descritor. Diretórios e symlinks são rejeitados, e arquivos fora disso são ignorados.
- **Abuso → mitigação → evidência:**

  | Abuso | Mitigação | Evidência |
  |---|---|---|
  | Usar o site para gastar a conta ou provocar ban | Rate limit do NGINX, semáforos 2/2 e limite de 15 min existentes | Já configurados |
  | Fazer o app enviar cookies a outro host (SSRF) | Allowlist de host e extractor (C1) | Testes existentes de `extract_video_id` e `allowed_extractors` |
  | Vazar cookies via mensagem de erro | Saída do worker restrita (C2) | Teste negativo: com um `DownloadError` que contém o valor do cookie, o JSON do worker não o contém |
  | Vazar cookies por linha malformada no stderr ou log | Linhas inválidas descartadas antes do yt-dlp (C2) | Teste negativo: um arquivo com linha malformada contendo um valor secreto gera uma cópia sem essa linha, e o valor não aparece no stderr nem no JSON |
  | Cookie de outro domínio no arquivo | Filtro de domínio (C1) | Teste: uma linha de `evil.com` fica fora da cópia |
  | Corromper ou regravar o original | Uso só da cópia (C3) | Teste: `cookiefile` ≠ original, cópia em 0600 removida após o job, original intacto |
  | Arquivo ausente, enorme ou diretório | Validação (C4/C5) | Teste: em cada caso, sem `cookiefile` |
  | Cópia esquecida após kill por timeout | Diretório `ytdl-` coberto por `sweep_stale_workdirs` | Prefixo idêntico; teste existente da varredura |

- **Raio de dano da credencial:**
  - Só a conta descartável, que nunca deve ser a conta pessoal.
  - Quem tem root na VPS ou acesso ao container consegue ler os cookies. Isso é aceito, porque é o mesmo nível de quem já controla o app.
  - Rotação: `cat novo.txt > youtube-cookies.txt`, que mantém o inode e é lido no próximo job, ou `docker compose restart` depois de um `mv`. O bind mount fica preso ao inode antigo.
  - Revogação: sair da conta em outra sessão invalida os cookies.
- **Risco residual e premissas:**
  - O Google pode banir a conta ou os cookies podem vencer (semanas); o sintoma volta a ser 502 `blocked`.
  - Risco de ToS do YouTube, já aceito em D5.
  - O app não detecta cookies vencidos de forma proativa.

## Production plan

Plano para a VPS `*.bneli.tech`, executado pelo operador com aprovação do Production Gate:

1. Criar a conta descartável e exportar os cookies em uma janela anônima, seguindo o wiki do yt-dlp: fazer login, abrir `youtube.com/robots.txt`, exportar e fechar a janela sem fazer logout.
2. Copiar o arquivo para `/opt/ytdownloadmusics/youtube-cookies.txt`, depois `chown 10001:10001` e `chmod 400`. O arquivo precisa existir, mesmo vazio, ou o `compose up` falha.
3. Baixar o novo `docker-compose.yml` e rodar `docker compose pull && docker compose up -d`.
4. Verificar: `curl -s -X POST http://127.0.0.1:8010/api/info -d '{"url":"https://youtu.be/_k2ty4A5x1w"}' -H 'content-type: application/json'` deve retornar 200, e `docker compose logs web` não deve conter linhas do arquivo.
5. Rollback: `: > youtube-cookies.txt` (o arquivo vazio desliga a feature), ou voltar `IMAGE_TAG` para o SHA anterior.

## Repository write scope

`app/config.py`, `app/worker.py`, `tests/test_worker.py`, `deploy/docker-compose.yml`, `deploy/.env.example`, `.gitignore`, `SECURITY.md`, `.memory-bank/**`, `.tasks/FEAT-002-cookies-do-youtube-para-contornar-bloqueio-de-ip/**`

## Ordered tasks and tests

1. `config.py` + `worker.py`: `cookies_file`, `_cookie_copy`, `cookiefile` em `base_opts`, usado em `run_info` e `run_download`.
2. `tests/test_worker.py`, um teste por critério de aceite mais os negativos dos invariantes:
   - Cópia filtrada usada, em 0600 e removida, com o original intacto e a linha de `evil.com` descartada (critérios 1 e 2, C1, C3).
   - Ausente, vazio, diretório, symlink, maior que 1 MiB ou só com linhas malformadas resulta em sem cookies (critério 3, C5).
   - Linha malformada e erro contendo o valor do cookie não aparecem no stderr nem no JSON (critérios 4 e 5, C2).
3. `deploy/docker-compose.yml` (secret), `.env.example` (comentário), `.gitignore`.
4. Docs: `SECURITY.md` (seção do projeto), `.memory-bank/ops/deploy.md` (instalação com `touch` obrigatório e rotação com `cat >` ou restart), `.memory-bank/system/architecture.md`.

## Plan review

Feita por um revisor independente (subagente novo). Veredito inicial: "Needs changes". Tudo foi incorporado:
- **High:** vazamento de linha malformada via stderr; resolvido com o filtro de formato e o teste negativo.
- **Medium:** malformado passa a degradar para sem cookies; `touch` obrigatório no Compose.
- **Low:** rotação presa ao inode; TOCTOU e symlink resolvidos com `O_NOFOLLOW` + `fstat`; cópia criada com `O_EXCL` 0600.
- **Nit:** filtro de domínio torna C1 verificável.
5. Code review e security review por subagentes novos em `review.md`; CI; PR.

## Dependency / supply-chain changes

Nenhuma. Usa só a opção `cookiefile`, já existente no yt-dlp, e o recurso de secrets do Compose.
