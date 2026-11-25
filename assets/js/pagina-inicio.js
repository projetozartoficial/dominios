/**
 * Página inicial: busca de domínios e vitrine de extensões.
 */

import { iniciarPagina } from "./layout.js";
import { adicionarAoCarrinho, estaNoCarrinho } from "./carrinho.js";
import {
  validarNome,
  regraDaExtensao,
  verificarDisponibilidade,
  linkDoParceiro,
  TEXTO_STATUS,
} from "./dominios.js";
import { formatarPreco, escaparHtml, notificar } from "./util.js";

const elementos = {
  form: document.querySelector("[data-form-busca]"),
  campo: document.querySelector("#campo-dominio"),
  erro: document.querySelector("[data-erro-busca]"),
  resultados: document.querySelector("[data-resultados]"),
  tituloResultados: document.querySelector("[data-titulo-resultados]"),
  lista: document.querySelector("[data-lista-resultados]"),
  grade: document.querySelector("[data-grade-extensoes]"),
};

let config = null;

/* ---------- Vitrine de extensões ---------- */

function textoPreco(extensao) {
  if (extensao.modo === "revenda") {
    return `${formatarPreco(extensao.preco)}<small>no 1º ano · renova por ${formatarPreco(extensao.renovacao)}/ano</small>`;
  }
  return `Preço no ${escaparHtml(extensao.parceiro)}<small>a compra é feita no site dele</small>`;
}

function montarVitrine() {
  elementos.grade.innerHTML = config.extensoes
    .map((extensao) => {
      const selo =
        extensao.modo === "revenda"
          ? '<span class="selo selo--revenda">Compra aqui</span>'
          : `<span class="selo">${escaparHtml(extensao.parceiro)}</span>`;

      return `
        <article class="cartao">
          ${selo}
          <h3 class="cartao__tld">.${escaparHtml(extensao.tld)}</h3>
          <p class="cartao__descricao">${escaparHtml(extensao.descricao)}</p>
          <p class="cartao__preco">${textoPreco(extensao)}</p>
        </article>
      `;
    })
    .join("");
}

/* ---------- Resultados da busca ---------- */

function mostrarErro(mensagem) {
  elementos.erro.textContent = mensagem;
  elementos.erro.hidden = !mensagem;
}

/** Monta a área de ação (botão + explicação) de um resultado. */
function montarAcao(extensao, dominio, status) {
  if (status === "carregando") {
    return "";
  }

  if (status === "registrado") {
    return "<span>Esse já tem dono. Experimente outra extensão ou outro nome.</span>";
  }

  if (extensao.modo === "revenda") {
    const aviso =
      status === "verificar"
        ? "<span>A disponibilidade é confirmada antes do pagamento.</span>"
        : "<span>Registro feito por nós.</span>";

    const botao = estaNoCarrinho(dominio)
      ? '<a class="botao botao--secundario botao--pequeno" href="carrinho.html">No carrinho · ver</a>'
      : `<button type="button" class="botao botao--pequeno" data-adicionar="${escaparHtml(dominio)}" data-tld="${escaparHtml(extensao.tld)}">Adicionar ao carrinho</button>`;

    return aviso + botao;
  }

  // Afiliado ou externo: leva para o parceiro
  const link = linkDoParceiro(extensao, dominio);
  const tipo = extensao.modo === "afiliado" ? "Link de parceiro (afiliado)." : "Site oficial do registro.";
  const explicacao = `<span>Você será levado ao ${escaparHtml(extensao.parceiro)}. ${tipo}</span>`;

  if (!link) {
    return `${explicacao}<button type="button" class="botao botao--secundario botao--pequeno" disabled>Link em breve</button>`;
  }

  const rel = extensao.modo === "afiliado" ? "sponsored noopener" : "noopener";
  return `${explicacao}
    <a class="botao botao--pequeno" href="${escaparHtml(link)}" target="_blank" rel="${rel}">
      Registrar no ${escaparHtml(extensao.parceiro)}<span class="somente-leitor"> (abre em nova aba)</span>
    </a>`;
}

function precoDoResultado(extensao) {
  if (extensao.modo === "revenda") {
    return `${formatarPreco(extensao.preco)}<small>renova por ${formatarPreco(extensao.renovacao)}/ano</small>`;
  }
  return `<small>Preço no ${escaparHtml(extensao.parceiro)}</small>`;
}

/** Atualiza um item da lista quando a verificação termina. */
function atualizarResultado(item, extensao, dominio, status) {
  item.dataset.status = status;
  const statusEl = item.querySelector(".resultado__status");
  statusEl.className = `resultado__status status--${status}`;
  statusEl.textContent =
    status === "verificar" && extensao.modo === "revenda" ? "A confirmar" : TEXTO_STATUS[status];

  const acao = item.querySelector(".resultado__acao");
  acao.innerHTML = montarAcao(extensao, dominio, status);
  acao.hidden = !acao.innerHTML.trim();
}

function criarItem(extensao, nome) {
  const dominio = `${nome}.${extensao.tld}`;
  const erroRegra = regraDaExtensao(nome, extensao.tld);

  const item = document.createElement("li");
  item.className = "resultado";
  item.innerHTML = `
    <span class="resultado__dominio">${escaparHtml(nome)}<span class="tld">.${escaparHtml(extensao.tld)}</span></span>
    <span class="resultado__status status--carregando">${TEXTO_STATUS.carregando}</span>
    <span class="resultado__preco">${precoDoResultado(extensao)}</span>
    <div class="resultado__acao" hidden></div>
  `;

  if (erroRegra) {
    const statusEl = item.querySelector(".resultado__status");
    statusEl.className = "resultado__status status--registrado";
    statusEl.textContent = "Indisponível";
    const acao = item.querySelector(".resultado__acao");
    acao.innerHTML = `<span>${escaparHtml(erroRegra)}</span>`;
    acao.hidden = false;
    return { item, promessa: Promise.resolve() };
  }

  const promessa = verificarDisponibilidade(dominio, extensao, config).then((status) =>
    atualizarResultado(item, extensao, dominio, status)
  );

  return { item, promessa };
}

async function pesquisar(texto) {
  const validacao = validarNome(texto, config.extensoes);

  if (!validacao.ok) {
    mostrarErro(validacao.erro);
    elementos.resultados.hidden = true;
    return;
  }

  mostrarErro("");
  const { nome, tldDigitado } = validacao;

  // A extensão digitada aparece primeiro
  const extensoes = [...config.extensoes].sort((a, b) => {
    if (a.tld === tldDigitado) return -1;
    if (b.tld === tldDigitado) return 1;
    return 0;
  });

  elementos.lista.innerHTML = "";
  elementos.tituloResultados.textContent = `Resultados para "${nome}"`;
  elementos.resultados.hidden = false;

  const verificacoes = extensoes.map((extensao) => {
    const { item, promessa } = criarItem(extensao, nome);
    elementos.lista.append(item);
    return promessa;
  });

  elementos.tituloResultados.focus({ preventScroll: true });
  elementos.resultados.scrollIntoView({ behavior: "smooth", block: "start" });

  // Guarda a busca no endereço (dá para compartilhar o link)
  const url = new URL(location.href);
  url.searchParams.set("dominio", nome + (tldDigitado ? "." + tldDigitado : ""));
  history.replaceState(null, "", url);

  await Promise.all(verificacoes);
}

/* ---------- Eventos ---------- */

function ligarEventos() {
  elementos.form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    pesquisar(elementos.campo.value);
  });

  // Um único "ouvinte" para todos os botões "Adicionar ao carrinho"
  elementos.lista.addEventListener("click", (evento) => {
    const botao = evento.target.closest("[data-adicionar]");
    if (!botao) return;

    const dominio = botao.dataset.adicionar;
    adicionarAoCarrinho(dominio, botao.dataset.tld);
    notificar(`${dominio} foi adicionado ao carrinho.`);

    const link = document.createElement("a");
    link.className = "botao botao--secundario botao--pequeno";
    link.href = "carrinho.html";
    link.textContent = "No carrinho · ver";
    botao.replaceWith(link);
    link.focus();
  });
}

/* ---------- Início ---------- */

async function iniciar() {
  config = await iniciarPagina();
  montarVitrine();
  ligarEventos();

  // Se o endereço já tem ?dominio=..., pesquisa automaticamente
  const buscaInicial = new URLSearchParams(location.search).get("dominio");
  if (buscaInicial) {
    elementos.campo.value = buscaInicial;
    pesquisar(buscaInicial);
  }
}

iniciar();
