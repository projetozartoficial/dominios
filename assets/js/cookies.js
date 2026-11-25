/**
 * Aviso de cookies e consentimento (LGPD).
 *
 * - Armazenamento essencial (carrinho e a própria escolha de cookies) sempre funciona.
 * - Cookies de análise (Google Analytics) SÓ são carregados se o visitante aceitar
 *   e se houver um ID em site.json > analytics.googleAnalyticsId.
 * - O visitante pode mudar a escolha a qualquer momento pelo link no rodapé.
 */

import { lerArmazenamento, salvarArmazenamento } from "./util.js";

const CHAVE = "consentimento-cookies";

/** @returns {{analise: boolean, data: string} | null} */
function lerConsentimento() {
  return lerArmazenamento(CHAVE, null);
}

function salvarConsentimento(aceitouAnalise) {
  salvarArmazenamento(CHAVE, {
    analise: aceitouAnalise,
    data: new Date().toISOString(),
  });
}

/**
 * Carrega o Google Analytics. Chamado apenas depois do "Aceitar".
 * @param {string} id - ex.: "G-XXXXXXX"
 */
function carregarAnalytics(id) {
  if (!id || document.querySelector("script[data-analytics]")) {
    return;
  }

  const script = document.createElement("script");
  script.async = true;
  script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(id);
  script.dataset.analytics = "sim";
  document.head.append(script);

  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() {
    window.dataLayer.push(arguments);
  };
  window.gtag("js", new Date());
  window.gtag("config", id, { anonymize_ip: true });
}

function fecharAviso(aviso, focoAnterior) {
  aviso.remove();
  if (focoAnterior && document.contains(focoAnterior)) {
    focoAnterior.focus();
  }
}

/**
 * Mostra a caixa de escolha de cookies.
 * @param {object} config - configurações do site
 */
export function mostrarAvisoCookies(config) {
  document.querySelector(".aviso-cookies")?.remove();
  const focoAnterior = document.activeElement;

  const aviso = document.createElement("section");
  aviso.className = "aviso-cookies";
  aviso.setAttribute("aria-labelledby", "titulo-cookies");
  aviso.innerHTML = `
    <h2 id="titulo-cookies">Sua privacidade</h2>
    <p>
      Usamos armazenamento essencial para o site funcionar (por exemplo, guardar seu carrinho).
      Com a sua permissão, também usamos cookies de análise para entender como o site é usado.
      Saiba mais na <a href="cookies.html">Política de Cookies</a>.
    </p>
    <div class="aviso-cookies__botoes">
      <button type="button" class="botao botao--pequeno" data-aceitar>Aceitar análise</button>
      <button type="button" class="botao botao--secundario botao--pequeno" data-recusar>Só os essenciais</button>
    </div>
  `;

  aviso.querySelector("[data-aceitar]").addEventListener("click", () => {
    salvarConsentimento(true);
    carregarAnalytics(config.analytics?.googleAnalyticsId);
    fecharAviso(aviso, focoAnterior);
  });

  aviso.querySelector("[data-recusar]").addEventListener("click", () => {
    const tinhaAceitado = lerConsentimento()?.analise;
    salvarConsentimento(false);
    fecharAviso(aviso, focoAnterior);
    // Se o Analytics já estava carregado, recarrega a página para desligá-lo
    if (tinhaAceitado && document.querySelector("script[data-analytics]")) {
      location.reload();
    }
  });

  document.body.append(aviso);
}

/**
 * Chamado em toda página: aplica a escolha salva ou pergunta pela primeira vez.
 * @param {object} config
 */
export function iniciarCookies(config) {
  const consentimento = lerConsentimento();

  if (!consentimento) {
    mostrarAvisoCookies(config);
    return;
  }

  if (consentimento.analise) {
    carregarAnalytics(config.analytics?.googleAnalyticsId);
  }
}
