/* Ankara Hukuk teması: mobil menü, açık/koyu görünüm, "Bu sayfada" vurgusu. */
(function () {
  "use strict";
  var kok = document.documentElement;
  var govde = document.body;

  /* -- Açık / koyu görünüm ------------------------------------------------ */
  var temaDugme = document.querySelector(".tema-dugme");
  function koyuMu() {
    var t = kok.getAttribute("data-tema");
    if (t) return t === "koyu";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  if (temaDugme) {
    temaDugme.addEventListener("click", function () {
      var yeni = koyuMu() ? "acik" : "koyu";
      kok.setAttribute("data-tema", yeni);
      try { localStorage.setItem("au-tema", yeni); } catch (e) {}
    });
  }

  /* -- Mobil içindekiler paneli ------------------------------------------ */
  var menuDugme = document.querySelector(".menu-dugme");
  var perde = document.querySelector(".perde");
  var panel = document.getElementById("yan-panel");
  function paneliAyarla(acik) {
    govde.classList.toggle("panel-acik", acik);
    if (menuDugme) menuDugme.setAttribute("aria-expanded", acik ? "true" : "false");
    if (perde) perde.hidden = !acik;
  }
  if (menuDugme && panel) {
    menuDugme.addEventListener("click", function () {
      paneliAyarla(!govde.classList.contains("panel-acik"));
    });
    if (perde) perde.addEventListener("click", function () { paneliAyarla(false); });
    panel.addEventListener("click", function (e) {
      if (e.target.closest("a")) paneliAyarla(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") paneliAyarla(false);
    });
  }

  /* Geçerli sayfayı yan panelde görünür kıl */
  if (panel) {
    var gecerli = panel.querySelector("a.current");
    if (gecerli && gecerli.scrollIntoView) {
      var p = panel.getBoundingClientRect(), g = gecerli.getBoundingClientRect();
      if (g.bottom > p.bottom - 40) panel.scrollTop += g.top - p.top - p.height / 3;
    }
  }

  /* -- "Bu sayfada": okunan bölümü vurgula -------------------------------- */
  var yerel = document.querySelector(".bu-sayfada");
  if (yerel) {
    var ogeler = [];
    yerel.querySelectorAll("a[href^='#']").forEach(function (a) {
      var id = decodeURIComponent(a.getAttribute("href").slice(1));
      var bolum = id && document.getElementById(id);
      var baslik = bolum && (bolum.querySelector("h1,h2,h3,h4,h5,h6") || bolum);
      if (baslik) ogeler.push({ a: a, h: baslik });
    });
    var bekliyor = false, etkin = null;
    function guncelle() {
      bekliyor = false;
      var secilen = ogeler.length ? ogeler[0] : null;
      for (var i = 0; i < ogeler.length; i++) {
        if (ogeler[i].h.getBoundingClientRect().top < 130) secilen = ogeler[i]; else break;
      }
      if (secilen === etkin) return;
      if (etkin) etkin.a.classList.remove("etkin");
      etkin = secilen;
      if (etkin) etkin.a.classList.add("etkin");
    }
    window.addEventListener("scroll", function () {
      if (!bekliyor) { bekliyor = true; requestAnimationFrame(guncelle); }
    }, { passive: true });
    guncelle();
  }
})();
