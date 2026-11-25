/**
 * Página "Meu pedido": mostra a situação do pagamento e do registro.
 * O Mercado Pago traz o cliente de volta para cá depois de pagar.
 * Enquanto o pedido estiver em andamento, a página se atualiza sozinha.
 */

import { iniciarPagina } from "./layout.js";
import { temBackend, urlApi } from "./config.js";
import { formatarPreco, escaparHtml } from "./util.js";

const elementos = {
  titulo: document.querySelector("[data-codigo-pedido]"),
  situacao: document.querySelector("[data-situacao]"),
  itens: document.querySelector("[data-itens-pedido]"),
  total: document.querySelector("[data-total-pedido]"),
  valor: document.querySelector("[data-valor-pedido]"),
  form: document.querySelector("[data-form-consulta]"),
  campo: document.querySelector("#codigo"),
};

const TEXTO_ITEM = {
  aguardando: "Aguardando pagamento",
  registrado: "Registrado ✓",
  falhou: "Em processamento",
};

const EM_ANDAMENTO = ["aguardando_pagamento", "pago"];
const INTERVALO = 5000; // atualiza a cada 5 segundos
const TENTATIVAS_MAXIMAS = 36; // por até 3 minutos

let config = null;
let temporizador = null;

function mostrarSituacao(texto) {
  elementos.situacao.textContent = texto;
}

function desenharPedido(pedido) {
  elementos.titulo.textContent = `Pedido ${pedido.codigo}`;
  mostrarSituacao(pedido.statusTexto);

  elementos.itens.innerHTML = pedido.itens
    .map(
      (item) => `
      <li class="item-carrinho">
        <span class="item-carrinho__nome">
          ${escaparHtml(item.dominio)}
          <small>${item.anos} ${item.anos === 1 ? "ano" : "anos"}</small>
        </span>
        <span class="status-item status-item--${escaparHtml(item.status)}">${TEXTO_ITEM[item.status] || escaparHtml(item.status)}</span>
      </li>`
    )
    .join("");

  elementos.valor.textContent = formatarPreco(pedido.total);
  elementos.total.hidden = false;
}

async function carregar(codigo, tentativa = 1) {
  clearTimeout(temporizador);

  try {
    const resposta = await fetch(urlApi(config, `/api/pedidos/${encodeURIComponent(codigo)}`));
    const dados = await resposta.json();

    if (!resposta.ok) {
      throw new Error(dados.erro || "Pedido não encontrado.");
    }

    desenharPedido(dados);

    if (EM_ANDAMENTO.includes(dados.status) && tentativa < TENTATIVAS_MAXIMAS) {
      temporizador = setTimeout(() => carregar(codigo, tentativa + 1), INTERVALO);
    }
  } catch (erro) {
    elementos.itens.innerHTML = "";
    elementos.total.hidden = true;
    mostrarSituacao(erro.message || "Não foi possível consultar agora.");
  }
}

function abrir(codigo) {
  const limpo = codigo.trim().toUpperCase();
  if (!limpo) return;

  const url = new URL(location.href);
  url.searchParams.set("codigo", limpo);
  history.replaceState(null, "", url);

  elementos.titulo.textContent = `Pedido ${limpo}`;
  mostrarSituacao("Carregando…");
  carregar(limpo);
}

async function iniciar() {
  config = await iniciarPagina();

  if (!temBackend(config)) {
    mostrarSituacao("A consulta de pedidos ainda não está ativa.");
    elementos.form.hidden = true;
    return;
  }

  elementos.form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    abrir(elementos.campo.value);
  });

  const codigo = new URLSearchParams(location.search).get("codigo");
  if (codigo) {
    elementos.campo.value = codigo;
    abrir(codigo);
  } else {
    mostrarSituacao("Digite o código do pedido para consultar.");
  }
}

iniciar();
