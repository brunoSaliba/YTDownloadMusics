"use strict";

// Invariant I5: server/YouTube text is only ever written with textContent.
(function () {
  const $ = (id) => document.getElementById(id);
  const form = $("search");
  const input = $("url");
  const searchBtn = $("search-btn");
  const statusEl = $("status");
  const card = $("result");
  const downloadBtn = $("download-btn");
  let current = null;

  function setStatus(text, isError) {
    statusEl.textContent = text || "";
    statusEl.classList.toggle("is-error", Boolean(isError));
  }

  function formatDuration(seconds) {
    const s = Math.max(0, Math.floor(seconds || 0));
    const m = Math.floor(s / 60);
    return m + ":" + String(s % 60).padStart(2, "0");
  }

  async function errorMessage(res) {
    try {
      const data = await res.json();
      if (data && typeof data.detail === "string") return data.detail;
    } catch (_) { /* not JSON */ }
    if (res.status === 429) return "Muitas tentativas. Aguarde um pouco.";
    return "Algo deu errado (" + res.status + "). Tente novamente.";
  }

  function filenameFrom(res, fallback) {
    const header = res.headers.get("Content-Disposition") || "";
    const star = header.match(/filename\*=utf-8''([^;]+)/i);
    if (star) {
      try { return decodeURIComponent(star[1]); } catch (_) { /* ignore */ }
    }
    const plain = header.match(/filename="([^"]+)"/i);
    return plain ? plain[1] : fallback;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const url = input.value.trim();
    if (!url) { setStatus("Cole um link do YouTube.", true); return; }
    card.hidden = true;
    current = null;
    searchBtn.disabled = true;
    setStatus("Buscando…");
    try {
      const res = await fetch("/api/info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url }),
      });
      if (!res.ok) { setStatus(await errorMessage(res), true); return; }
      const info = await res.json();
      current = info;
      $("title").textContent = info.title;
      $("artist").textContent = info.artist;
      $("duration").textContent = formatDuration(info.duration);
      $("thumb").src = info.thumbnail;
      card.hidden = false;
      setStatus("");
    } catch (_) {
      setStatus("Falha de conexão. Tente novamente.", true);
    } finally {
      searchBtn.disabled = false;
    }
  });

  downloadBtn.addEventListener("click", async () => {
    if (!current) return;
    downloadBtn.disabled = true;
    searchBtn.disabled = true;
    setStatus("Baixando e convertendo… pode levar até alguns minutos.");
    try {
      const res = await fetch("/api/download/" + encodeURIComponent(current.id));
      if (!res.ok) { setStatus(await errorMessage(res), true); return; }
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = filenameFrom(res, "audio.mp3");
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(link.href), 10000);
      setStatus("Pronto! Download iniciado.");
    } catch (_) {
      setStatus("Falha de conexão. Tente novamente.", true);
    } finally {
      downloadBtn.disabled = false;
      searchBtn.disabled = false;
    }
  });
})();
