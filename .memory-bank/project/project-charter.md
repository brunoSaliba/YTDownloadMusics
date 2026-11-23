# Project Charter — YT Music Downloader

## Problem / outcome
Site público onde qualquer pessoa cola a URL de um vídeo do YouTube, vê qual música é (título, artista/canal, capa, duração) e baixa o áudio em MP3 com tags. Sucesso = colar URL → prévia → MP3 tocável com capa/título em poucos segundos, sem cadastro.

## Actors
- Visitante anônimo (único papel; sem contas, sem login, sem admin na UI).
- Operador (dono da VPS): deploy via GitHub Actions/GHCR, atualização do yt-dlp.

## Core workflow
1. Colar URL (youtube.com/watch, youtu.be, music.youtube.com, shorts).
2. Servidor valida e mostra metadados do vídeo.
3. Usuário clica "Baixar" → servidor baixa o áudio, converte para MP3, embute tags + capa e entrega o arquivo.

## Scope decisions (human, 2026-11-23)
- Formato: MP3 apenas.
- Identificação: metadados do próprio YouTube (sem serviço externo de reconhecimento).
- Deploy: VPS compartilhada `*.bneli.tech` (padrão GHCR + NGINX no host).
- Limites: duração máxima (padrão 15 min) e sem playlists.

## Out of scope (v1)
Contas, histórico, playlists, outros sites além do YouTube, escolha de formato/qualidade, reconhecimento por fingerprint, armazenamento persistente de arquivos.

## Constraints
- Python, Docker. Sem banco de dados; arquivos temporários apagados após entrega.
- Legal: baixar do YouTube viola os Termos de Serviço do YouTube e pode infringir direitos autorais; risco aceito/gerido pelo dono do projeto (ver plan.md, decisões).
- Operacional: YouTube costuma bloquear IPs de datacenter ("confirm you're not a bot"); o yt-dlp precisa de atualização frequente.
