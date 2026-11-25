/**
 * Carrinho de compras.
 * Fica salvo só no navegador do visitante (localStorage). Isso é armazenamento
 * essencial: sem ele o carrinho esvaziaria a cada página.
 *
 * Cada item tem o formato: { dominio: "meusite.com", tld: "com", anos: 1 }
 */

import { lerArmazenamento, salvarArmazenamento } from "./util.js";

const CHAVE = "carrinho";
export const ANOS_MAXIMO = 5;

/** @returns {Array<{dominio: string, tld: string, anos: number}>} */
export function lerCarrinho() {
  const itens = lerArmazenamento(CHAVE, []);
  return Array.isArray(itens) ? itens : [];
}

function salvarCarrinho(itens) {
  salvarArmazenamento(CHAVE, itens);
  atualizarContador();
}

/**
 * Coloca um domínio no carrinho (se ele ainda não estiver lá).
 * @returns {boolean} true se foi adicionado, false se já estava
 */
export function adicionarAoCarrinho(dominio, tld) {
  const itens = lerCarrinho();

  if (itens.some((item) => item.dominio === dominio)) {
    return false;
  }

  itens.push({ dominio, tld, anos: 1 });
  salvarCarrinho(itens);
  return true;
}

export function removerDoCarrinho(dominio) {
  const itens = lerCarrinho().filter((item) => item.dominio !== dominio);
  salvarCarrinho(itens);
}

export function mudarAnos(dominio, anos) {
  const anosValidos = Math.min(Math.max(Number(anos) || 1, 1), ANOS_MAXIMO);
  const itens = lerCarrinho().map((item) =>
    item.dominio === dominio ? { ...item, anos: anosValidos } : item
  );
  salvarCarrinho(itens);
}

export function esvaziarCarrinho() {
  salvarCarrinho([]);
}

export function estaNoCarrinho(dominio) {
  return lerCarrinho().some((item) => item.dominio === dominio);
}

/**
 * Calcula o valor de um item: primeiro ano pelo preço de registro,
 * anos seguintes pelo preço de renovação.
 * (Esse total é só para mostrar na tela. O back-end recalcula tudo.)
 */
export function calcularItem(item, extensao) {
  if (!extensao || extensao.modo !== "revenda") {
    return 0;
  }
  return extensao.preco + extensao.renovacao * (item.anos - 1);
}

/** Atualiza o número que aparece ao lado de "Carrinho" no menu. */
export function atualizarContador() {
  const total = lerCarrinho().length;
  document.querySelectorAll("[data-contador-carrinho]").forEach((elemento) => {
    elemento.textContent = total;
    elemento.hidden = total === 0;
  });

  const link = document.querySelector("[data-link-carrinho]");
  if (link) {
    link.setAttribute(
      "aria-label",
      total === 1 ? "Carrinho, 1 item" : `Carrinho, ${total} itens`
    );
  }
}
