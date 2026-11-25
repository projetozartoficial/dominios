/**
 * Funções pequenas usadas em várias partes do site.
 */

const formatador = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

/**
 * Formata um número como dinheiro em reais.
 * @param {number} valor - ex.: 69.9
 * @returns {string} ex.: "R$ 69,90"
 */
export function formatarPreco(valor) {
  return formatador.format(valor);
}

/**
 * Evita que um texto digitado pelo usuário vire HTML na página.
 * @param {string} texto
 * @returns {string} texto seguro para usar dentro de innerHTML
 */
export function escaparHtml(texto) {
  return String(texto)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

let temporizador = null;

/**
 * Mostra uma mensagem curta no rodapé da tela, lida também por leitores de tela.
 * @param {string} texto
 */
export function notificar(texto) {
  let caixa = document.querySelector(".notificacao");

  if (!caixa) {
    caixa = document.createElement("div");
    caixa.className = "notificacao";
    caixa.setAttribute("role", "status");
    caixa.setAttribute("aria-live", "polite");
    document.body.append(caixa);
  }

  caixa.textContent = texto;
  caixa.hidden = false;

  clearTimeout(temporizador);
  temporizador = setTimeout(() => {
    caixa.hidden = true;
  }, 3500);
}

/**
 * Lê um valor do localStorage sem quebrar o site se o navegador bloquear o acesso.
 * @param {string} chave
 * @param {*} padrao - valor devolvido se não houver nada salvo
 */
export function lerArmazenamento(chave, padrao) {
  try {
    const valor = localStorage.getItem(chave);
    return valor === null ? padrao : JSON.parse(valor);
  } catch {
    return padrao;
  }
}

/**
 * Salva um valor no localStorage (silenciosamente ignora se estiver bloqueado).
 * @param {string} chave
 * @param {*} valor
 */
export function salvarArmazenamento(chave, valor) {
  try {
    localStorage.setItem(chave, JSON.stringify(valor));
  } catch {
    /* navegação privada ou armazenamento bloqueado: o site continua funcionando */
  }
}
