/**
 * Página do carrinho: lista os domínios, calcula o total e envia o pedido
 * para o back-end (quando ele estiver ligado).
 */

import { iniciarPagina } from "./layout.js";
import { temBackend, urlApi } from "./config.js";
import {
  lerCarrinho,
  removerDoCarrinho,
  mudarAnos,
  esvaziarCarrinho,
  calcularItem,
  ANOS_MAXIMO,
} from "./carrinho.js";
import { formatarPreco, escaparHtml, notificar } from "./util.js";

const elementos = {
  itens: document.querySelector("[data-itens]"),
  total: document.querySelector("[data-total]"),
  valorTotal: document.querySelector("[data-valor-total]"),
  painelDados: document.querySelector("[data-painel-dados]"),
  form: document.querySelector("[data-form-pedido]"),
  botao: document.querySelector("[data-botao-finalizar]"),
  mensagem: document.querySelector("[data-mensagem-pedido]"),
};

let config = null;

/** Procura no site.json a extensão de um item. */
function extensaoDo(item) {
  return config.extensoes.find((e) => e.tld === item.tld);
}

/** Itens que podem ser comprados aqui (extensão ainda está em modo revenda). */
function itensValidos() {
  return lerCarrinho().filter((item) => extensaoDo(item)?.modo === "revenda");
}

function opcoesDeAnos(selecionado) {
  let opcoes = "";
  for (let anos = 1; anos <= ANOS_MAXIMO; anos++) {
    const marcado = anos === selecionado ? " selected" : "";
    opcoes += `<option value="${anos}"${marcado}>${anos} ${anos === 1 ? "ano" : "anos"}</option>`;
  }
  return opcoes;
}

function desenharCarrinho() {
  const itens = itensValidos();

  if (itens.length === 0) {
    elementos.itens.innerHTML = `
      <li class="vazio">
        <p>Seu carrinho está vazio.</p>
        <a class="botao" href="index.html">Pesquisar domínios</a>
      </li>`;
    elementos.total.hidden = true;
    elementos.painelDados.hidden = true;
    return;
  }

  elementos.itens.innerHTML = itens
    .map((item) => {
      const extensao = extensaoDo(item);
      const id = "anos-" + item.dominio.replace(/[^a-z0-9]/g, "-");
      return `
        <li class="item-carrinho">
          <span class="item-carrinho__nome">
            ${escaparHtml(item.dominio)}
            <small>${formatarPreco(calcularItem(item, extensao))} · renova por ${formatarPreco(extensao.renovacao)}/ano</small>
          </span>
          <label class="somente-leitor" for="${id}">Período de ${escaparHtml(item.dominio)}</label>
          <select id="${id}" data-anos="${escaparHtml(item.dominio)}">${opcoesDeAnos(item.anos)}</select>
          <button type="button" class="botao-remover" data-remover="${escaparHtml(item.dominio)}">
            Remover<span class="somente-leitor"> ${escaparHtml(item.dominio)}</span>
          </button>
        </li>`;
    })
    .join("");

  const total = itens.reduce((soma, item) => soma + calcularItem(item, extensaoDo(item)), 0);
  elementos.valorTotal.textContent = formatarPreco(total);
  elementos.total.hidden = false;
  elementos.painelDados.hidden = false;
}

/* ---------- Validação do formulário ---------- */

function mostrarMensagem(texto, tipo) {
  elementos.mensagem.className = `mensagem mensagem--${tipo}`;
  elementos.mensagem.textContent = texto;
}

/** Confere os campos e devolve o primeiro problema encontrado (ou null). */
function validarFormulario(dados) {
  if (dados.nome.length < 3) {
    return { campo: "nome", erro: "Digite o nome completo ou a razão social." };
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(dados.email)) {
    return { campo: "email", erro: "Digite um e-mail válido." };
  }
  const digitos = dados.documento.replace(/\D/g, "");
  if (digitos.length !== 11 && digitos.length !== 14) {
    return { campo: "documento", erro: "O CPF tem 11 dígitos e o CNPJ tem 14." };
  }
  if (!dados.aceite) {
    return { campo: "aceite", erro: "Para continuar, aceite os termos e as políticas." };
  }
  return null;
}

async function enviarPedido(evento) {
  evento.preventDefault();

  const formulario = new FormData(elementos.form);
  const dados = {
    nome: String(formulario.get("nome") || "").trim(),
    email: String(formulario.get("email") || "").trim(),
    documento: String(formulario.get("documento") || "").trim(),
    aceite: formulario.get("aceite") === "on",
  };

  const problema = validarFormulario(dados);
  if (problema) {
    mostrarMensagem(problema.erro, "erro");
    document.getElementById(problema.campo).focus();
    return;
  }

  if (!temBackend(config)) {
    mostrarMensagem(
      "Os pagamentos ainda não estão ativos neste site. Nenhum dado foi enviado.",
      "erro"
    );
    return;
  }

  elementos.botao.disabled = true;
  mostrarMensagem("Enviando pedido…", "info");

  try {
    const resposta = await fetch(urlApi(config, "/api/pedidos"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        titular: {
          nome: dados.nome,
          email: dados.email,
          documento: dados.documento.replace(/\D/g, ""),
        },
        aceiteTermos: dados.aceite,
        itens: itensValidos().map(({ dominio, anos }) => ({ dominio, anos })),
      }),
    });

    const resultado = await resposta.json();

    if (!resposta.ok) {
      throw new Error(resultado.erro || "Não foi possível criar o pedido.");
    }

    esvaziarCarrinho();

    if (resultado.pagamentoUrl) {
      location.href = resultado.pagamentoUrl;
      return;
    }

    desenharCarrinho();
    mostrarMensagem(`Pedido ${resultado.pedido} criado! Guarde este código para acompanhar a compra.`, "sucesso");
  } catch (erro) {
    mostrarMensagem(erro.message, "erro");
  } finally {
    elementos.botao.disabled = false;
  }
}

/* ---------- Eventos ---------- */

function ligarEventos() {
  elementos.itens.addEventListener("change", (evento) => {
    const seletor = evento.target.closest("[data-anos]");
    if (!seletor) return;
    mudarAnos(seletor.dataset.anos, seletor.value);
    desenharCarrinho();
    document.getElementById(seletor.id)?.focus();
  });

  elementos.itens.addEventListener("click", (evento) => {
    const botao = evento.target.closest("[data-remover]");
    if (!botao) return;
    removerDoCarrinho(botao.dataset.remover);
    notificar(`${botao.dataset.remover} foi removido do carrinho.`);
    desenharCarrinho();
    elementos.itens.querySelector("button, a, select")?.focus();
  });

  elementos.form.addEventListener("submit", enviarPedido);
}

async function iniciar() {
  config = await iniciarPagina();
  desenharCarrinho();
  ligarEventos();
}

iniciar();
