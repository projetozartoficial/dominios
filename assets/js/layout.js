/**
 * Partes que se repetem em todas as páginas: cabeçalho, rodapé,
 * título da aba e ícone (favicon). Assim, mudar o nome ou a logo
 * no site.json atualiza o site inteiro de uma vez.
 */

import { carregarConfig } from "./config.js";
import { atualizarContador } from "./carrinho.js";
import { iniciarCookies, mostrarAvisoCookies } from "./cookies.js";
import { escaparHtml } from "./util.js";

const LINKS_MENU = [
  { texto: "Início", href: "index.html", pagina: "inicio" },
  { texto: "Extensões", href: "index.html#extensoes" },
  { texto: "Como funciona", href: "index.html#como-funciona" },
  { texto: "Dúvidas", href: "index.html#duvidas" },
  { texto: "Contato", href: "contato.html", pagina: "contato" },
];

/** Coloca o nome do site no título da aba e a logo como ícone da aba. */
function aplicarIdentidade(identidade) {
  const tituloPagina = document.body.dataset.titulo;
  document.title = tituloPagina ? `${tituloPagina} | ${identidade.nome}` : identidade.nome;

  let icone = document.querySelector("link[rel='icon']");
  if (!icone) {
    icone = document.createElement("link");
    icone.rel = "icon";
    document.head.append(icone);
  }
  icone.type = identidade.favicon.endsWith(".svg") ? "image/svg+xml" : "image/png";
  icone.href = identidade.favicon;

  document.querySelectorAll("[data-site-nome]").forEach((elemento) => {
    elemento.textContent = identidade.nome;
  });
}

function montarCabecalho(identidade) {
  const paginaAtual = document.body.dataset.pagina;
  const cabecalho = document.querySelector("[data-cabecalho]");
  if (!cabecalho) return;

  const itens = LINKS_MENU.map((link) => {
    const atual = link.pagina && link.pagina === paginaAtual ? ' aria-current="page"' : "";
    return `<li><a href="${link.href}"${atual}>${link.texto}</a></li>`;
  }).join("");

  const carrinhoAtual = paginaAtual === "carrinho" ? ' aria-current="page"' : "";

  cabecalho.className = "cabecalho";
  cabecalho.innerHTML = `
    <div class="container cabecalho__conteudo">
      <a class="marca" href="index.html" aria-label="${escaparHtml(identidade.nome)}, página inicial">
        <img class="marca__logo" src="${escaparHtml(identidade.logo)}" alt="${escaparHtml(identidade.logoAlt || "")}">
        ${identidade.submarca ? `<span class="marca__sub">${escaparHtml(identidade.submarca)}</span>` : ""}
      </a>

      <button type="button" class="botao botao--secundario botao--pequeno botao-menu"
              aria-expanded="false" aria-controls="menu-principal">Menu</button>

      <nav aria-label="Menu principal">
        <ul class="menu" id="menu-principal">
          ${itens}
          <li>
            <a href="carrinho.html" data-link-carrinho${carrinhoAtual}>
              Carrinho <span class="contador-carrinho" data-contador-carrinho aria-hidden="true" hidden>0</span>
            </a>
          </li>
        </ul>
      </nav>
    </div>
  `;

  // Menu do celular: abre e fecha, e fecha com Esc
  const botao = cabecalho.querySelector(".botao-menu");
  const menu = cabecalho.querySelector(".menu");

  const fechar = () => {
    menu.classList.remove("menu--aberto");
    botao.setAttribute("aria-expanded", "false");
  };

  botao.addEventListener("click", () => {
    const aberto = menu.classList.toggle("menu--aberto");
    botao.setAttribute("aria-expanded", String(aberto));
  });

  menu.addEventListener("click", (evento) => {
    if (evento.target.closest("a")) fechar();
  });

  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && menu.classList.contains("menu--aberto")) {
      fechar();
      botao.focus();
    }
  });
}

/** Mostra um dado da empresa, ou um aviso amarelo se ainda não foi preenchido. */
function dado(valor, rotulo) {
  return valor
    ? escaparHtml(valor)
    : `<span class="pendente">${rotulo} a preencher</span>`;
}

function montarRodape(config) {
  const { identidade, empresa } = config;
  const rodape = document.querySelector("[data-rodape]");
  if (!rodape) return;

  const temAfiliado = config.extensoes.some((e) => e.modo !== "revenda");
  const email = empresa.email
    ? `<a href="mailto:${escaparHtml(empresa.email)}">${escaparHtml(empresa.email)}</a>`
    : dado("", "E-mail");

  rodape.className = "rodape";
  rodape.innerHTML = `
    <div class="container">
      <div class="rodape__grade">
        <div class="rodape__empresa">
          <img class="rodape__logo" src="${escaparHtml(identidade.logo)}" alt="${escaparHtml(identidade.logoAlt || "")}">
          <h2>${escaparHtml(identidade.nome)}</h2>
          ${identidade.grupo ? `<p class="rodape__grupo">Um projeto do grupo ${escaparHtml(identidade.grupo)}.</p>` : ""}
          <p>${dado(empresa.razaoSocial, "Razão social")}</p>
          <p>CNPJ: ${dado(empresa.cnpj, "CNPJ")}</p>
          <p>${dado(empresa.endereco, "Endereço")}</p>
          <p>${email}</p>
        </div>

        <div>
          <h2>Informações legais</h2>
          <ul>
            <li><a href="termos.html">Termos de Uso</a></li>
            <li><a href="privacidade.html">Política de Privacidade</a></li>
            <li><a href="cookies.html">Política de Cookies</a></li>
            <li><a href="reembolso.html">Cancelamento e Reembolso</a></li>
            <li><button type="button" class="botao-link" data-preferencias-cookies>Preferências de cookies</button></li>
          </ul>
        </div>

        <div>
          <h2>Ajuda</h2>
          <ul>
            <li><a href="index.html#duvidas">Dúvidas frequentes</a></li>
            <li><a href="contato.html">Fale com a gente</a></li>
            <li><a href="privacidade.html#seus-direitos">Seus direitos (LGPD)</a></li>
          </ul>
        </div>
      </div>

      <div class="rodape__base">
        <p>© ${new Date().getFullYear()} ${escaparHtml(identidade.nome)}. Todos os direitos reservados.</p>
        ${temAfiliado ? "<p>Alguns links levam a parceiros e podem nos render comissão, sem custo extra para você.</p>" : ""}
      </div>
    </div>
  `;

  rodape.querySelector("[data-preferencias-cookies]").addEventListener("click", () => {
    mostrarAvisoCookies(config);
    document.querySelector(".aviso-cookies [data-aceitar]")?.focus();
  });
}

/**
 * Prepara qualquer página do site. Toda página chama isso primeiro.
 * @returns {Promise<object>} as configurações, para a página usar
 */
export async function iniciarPagina() {
  const config = await carregarConfig();
  aplicarIdentidade(config.identidade);
  montarCabecalho(config.identidade);
  montarRodape(config);
  atualizarContador();
  iniciarCookies(config);
  return config;
}
