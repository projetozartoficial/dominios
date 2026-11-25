/**
 * Página de contato.
 * Com back-end: envia para /api/contato.
 * Sem back-end: abre o programa de e-mail do visitante com a mensagem pronta.
 */

import { iniciarPagina } from "./layout.js";
import { temBackend, urlApi } from "./config.js";
import { escaparHtml } from "./util.js";

const form = document.querySelector("[data-form-contato]");
const caixaMensagem = document.querySelector("[data-mensagem-contato]");

let config = null;

function mostrarMensagem(texto, tipo) {
  caixaMensagem.className = `mensagem mensagem--${tipo}`;
  caixaMensagem.textContent = texto;
}

function lerFormulario() {
  const dados = new FormData(form);
  return {
    nome: String(dados.get("nome") || "").trim(),
    email: String(dados.get("email") || "").trim(),
    assunto: String(dados.get("assunto") || ""),
    mensagem: String(dados.get("mensagem") || "").trim(),
    aceite: dados.get("aceite") === "on",
  };
}

function validar(dados) {
  if (dados.nome.length < 2) return { campo: "nome", erro: "Digite seu nome." };
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(dados.email)) return { campo: "email", erro: "Digite um e-mail válido." };
  if (dados.mensagem.length < 5) return { campo: "mensagem", erro: "Escreva a sua mensagem." };
  if (!dados.aceite) return { campo: "aceite", erro: "Marque a concordância para podermos responder." };
  return null;
}

async function enviar(evento) {
  evento.preventDefault();
  const dados = lerFormulario();
  const problema = validar(dados);

  if (problema) {
    mostrarMensagem(problema.erro, "erro");
    document.getElementById(problema.campo).focus();
    return;
  }

  if (temBackend(config)) {
    try {
      const resposta = await fetch(urlApi(config, "/api/contato"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
      });
      if (!resposta.ok) throw new Error();
      form.reset();
      mostrarMensagem("Mensagem enviada! Respondemos pelo e-mail informado.", "sucesso");
    } catch {
      mostrarMensagem("Não foi possível enviar agora. Tente novamente em instantes.", "erro");
    }
    return;
  }

  const emailEmpresa = config.empresa.email;
  if (!emailEmpresa) {
    mostrarMensagem("O formulário ainda não está ativo. Nenhum dado foi enviado.", "erro");
    return;
  }

  const corpo = `${dados.mensagem}\n\n— ${dados.nome} (${dados.email})`;
  location.href =
    `mailto:${emailEmpresa}?subject=${encodeURIComponent(dados.assunto)}&body=${encodeURIComponent(corpo)}`;
}

async function iniciar() {
  config = await iniciarPagina();

  const email = config.empresa.email;
  document.querySelector("[data-email-empresa]").innerHTML = email
    ? `<a href="mailto:${escaparHtml(email)}">${escaparHtml(email)}</a>`
    : '<span class="pendente">a preencher</span>';

  form.addEventListener("submit", enviar);
}

iniciar();
