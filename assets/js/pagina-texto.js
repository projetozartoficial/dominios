/**
 * Páginas de texto (termos, privacidade, cookies, reembolso).
 * Preenche os dados da empresa que aparecem dentro do texto.
 *
 * No HTML, use por exemplo: <span data-empresa="cnpj"></span>
 */

import { iniciarPagina } from "./layout.js";
import { mostrarAvisoCookies } from "./cookies.js";

async function iniciar() {
  const config = await iniciarPagina();

  document.querySelectorAll("[data-empresa]").forEach((elemento) => {
    const valor = config.empresa[elemento.dataset.empresa];
    if (valor) {
      elemento.textContent = valor;
    } else {
      elemento.textContent = "[a preencher]";
      elemento.classList.add("pendente");
    }
  });

  document.querySelector("[data-abrir-cookies]")?.addEventListener("click", () => {
    mostrarAvisoCookies(config);
    document.querySelector(".aviso-cookies [data-aceitar]")?.focus();
  });
}

iniciar();
