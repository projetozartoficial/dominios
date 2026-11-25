/**
 * Carrega as configurações do site (nome, logo, empresa, extensões e preços)
 * a partir de dados/site.json. Esse é o ÚNICO arquivo que você precisa editar
 * para mudar nome, logo, preços e links de afiliado.
 */

let configCache = null;

/**
 * Busca o site.json uma única vez e guarda o resultado.
 * @returns {Promise<object>} configurações do site
 */
export async function carregarConfig() {
  if (configCache) {
    return configCache;
  }

  const resposta = await fetch("dados/site.json", { cache: "no-cache" });

  if (!resposta.ok) {
    throw new Error("Não foi possível carregar dados/site.json");
  }

  configCache = await resposta.json();
  return configCache;
}

/**
 * Diz se o back-end (Python) está ligado, ou seja, se api.url foi preenchido.
 * @param {object} config
 * @returns {boolean}
 */
export function temBackend(config) {
  return Boolean(config.api && config.api.url);
}

/**
 * Monta o endereço completo de uma rota do back-end.
 * @param {object} config
 * @param {string} rota - ex.: "/api/pedidos"
 * @returns {string}
 */
export function urlApi(config, rota) {
  return config.api.url.replace(/\/$/, "") + rota;
}
