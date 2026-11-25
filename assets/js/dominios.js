/**
 * Regras de domínios: validar o nome digitado, verificar se está livre
 * e montar o link de parceiro (afiliado ou externo).
 */

import { temBackend, urlApi } from "./config.js";

/**
 * Limpa e valida o nome que o visitante digitou.
 *
 * Aceita "Meu Site", "meusite.com" ou "https://www.meusite.com.br".
 * Tira acentos, espaços e o "www", e separa a extensão se ela foi digitada.
 *
 * @param {string} texto - o que foi digitado
 * @param {Array<object>} extensoes - lista do site.json
 * @returns {{ok: true, nome: string, tldDigitado: string|null} | {ok: false, erro: string}}
 */
export function validarNome(texto, extensoes) {
  let nome = texto
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "") // remove acentos: "ação" -> "acao"
    .replace(/^https?:\/\//, "")
    .replace(/^www\./, "")
    .replace(/\/.*$/, "")
    .replace(/\s+/g, "");

  if (!nome) {
    return { ok: false, erro: "Digite um nome para pesquisar." };
  }

  // Se a pessoa digitou a extensão, separa (testa as maiores primeiro: "com.br" antes de "br")
  let tldDigitado = null;
  const tlds = extensoes.map((e) => e.tld).sort((a, b) => b.length - a.length);

  for (const tld of tlds) {
    if (nome.endsWith("." + tld)) {
      tldDigitado = tld;
      nome = nome.slice(0, -(tld.length + 1));
      break;
    }
  }

  // Extensão que o site não oferece (ex.: "meusite.com.br"): pesquisa só o nome
  if (nome.includes(".")) {
    nome = nome.split(".")[0];
  }

  if (!/^[a-z0-9-]+$/.test(nome)) {
    return { ok: false, erro: "Use só letras, números e hífen (-)." };
  }

  if (nome.startsWith("-") || nome.endsWith("-")) {
    return { ok: false, erro: "O nome não pode começar nem terminar com hífen." };
  }

  if (nome.length > 63) {
    return { ok: false, erro: "O nome pode ter no máximo 63 caracteres." };
  }

  return { ok: true, nome, tldDigitado };
}

/**
 * Regras extras de cada extensão. Hoje só o .br tem limite próprio.
 * @returns {string|null} mensagem de erro, ou null se estiver tudo certo
 */
export function regraDaExtensao(nome, tld) {
  if (tld.endsWith("br") && (nome.length < 2 || nome.length > 26)) {
    return "Domínios .br precisam ter entre 2 e 26 caracteres.";
  }
  return null;
}

/**
 * Verifica se um domínio está livre.
 *
 * 1) Com back-end ligado: pergunta ao servidor Python.
 * 2) Sem back-end: consulta direto o RDAP (serviço público dos registros).
 *    Resposta 404 = livre; 200 = já registrado.
 * Se nada responder, devolve "verificar" (o visitante confere no parceiro).
 *
 * @returns {Promise<"disponivel"|"registrado"|"verificar">}
 */
export async function verificarDisponibilidade(dominio, extensao, config) {
  try {
    if (temBackend(config)) {
      const resposta = await fetch(
        urlApi(config, "/api/disponibilidade?dominio=" + encodeURIComponent(dominio))
      );
      if (!resposta.ok) return "verificar";
      const dados = await resposta.json();
      return dados.status;
    }

    if (!extensao.rdap) {
      return "verificar";
    }

    const resposta = await fetch(extensao.rdap + encodeURIComponent(dominio), {
      headers: { Accept: "application/rdap+json" },
    });

    if (resposta.status === 404) return "disponivel";
    if (resposta.ok) return "registrado";
    return "verificar";
  } catch {
    // Sem internet, bloqueio do navegador (CORS) ou serviço fora do ar
    return "verificar";
  }
}

/**
 * Monta o link do parceiro trocando {dominio} pelo domínio pesquisado.
 * @returns {string|null} link pronto, ou null se ainda não foi configurado
 */
export function linkDoParceiro(extensao, dominio) {
  if (!extensao.link || extensao.link.includes("SEU-LINK")) {
    return null;
  }
  return extensao.link.replace("{dominio}", encodeURIComponent(dominio));
}

/** Textos de cada situação, usados nos resultados. */
export const TEXTO_STATUS = {
  carregando: "Verificando…",
  disponivel: "Disponível",
  registrado: "Já registrado",
  verificar: "Confira no parceiro",
};
