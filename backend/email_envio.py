"""
Envio de e-mails (confirmação para o cliente e avisos para você).

Usa SMTP, que funciona com Gmail, Outlook, Zoho, etc. Configure no .env:
    SMTP_SERVIDOR, SMTP_PORTA, SMTP_USUARIO, SMTP_SENHA, EMAIL_REMETENTE, EMAIL_ADMIN

No Gmail, use uma "senha de app" (não a senha normal da conta).
Se o SMTP não estiver configurado, os e-mails só aparecem no log do servidor.
"""

import smtplib
import ssl
from email.message import EmailMessage

from configuracao import (
    EMAIL_ADMIN,
    EMAIL_REMETENTE,
    SMTP_PORTA,
    SMTP_SENHA,
    SMTP_SERVIDOR,
    SMTP_USUARIO,
    URL_SITE,
)


def enviar(para, assunto, texto):
    """
    Envia um e-mail de texto simples.

    Retorna:
        bool: True se foi enviado
    """
    if not para:
        return False

    if not (SMTP_SERVIDOR and SMTP_USUARIO and SMTP_SENHA):
        print(f"[e-mail não enviado: SMTP não configurado] Para: {para} | {assunto}")
        return False

    mensagem = EmailMessage()
    mensagem["From"] = f"Zart Domínios <{EMAIL_REMETENTE}>"
    mensagem["To"] = para
    mensagem["Subject"] = assunto
    mensagem.set_content(texto)

    try:
        contexto = ssl.create_default_context()
        if SMTP_PORTA == 465:
            with smtplib.SMTP_SSL(SMTP_SERVIDOR, SMTP_PORTA, context=contexto, timeout=20) as smtp:
                smtp.login(SMTP_USUARIO, SMTP_SENHA)
                smtp.send_message(mensagem)
        else:
            with smtplib.SMTP(SMTP_SERVIDOR, SMTP_PORTA, timeout=20) as smtp:
                smtp.starttls(context=contexto)
                smtp.login(SMTP_USUARIO, SMTP_SENHA)
                smtp.send_message(mensagem)
        return True
    except (smtplib.SMTPException, OSError) as erro:
        print(f"[falha ao enviar e-mail para {para}] {erro}")
        return False


def _lista_dominios(pedido):
    linhas = []
    for item in pedido["itens"]:
        situacao = {"registrado": "registrado", "falhou": "em processamento"}.get(
            item.get("status"), "aguardando"
        )
        linhas.append(f"  • {item['dominio']} ({item['anos']} ano(s)) — {situacao}")
    return "\n".join(linhas)


def avisar_cliente_pedido_concluido(pedido):
    tudo_certo = all(item.get("status") == "registrado" for item in pedido["itens"])
    complemento = (
        "Tudo certo! Seus domínios já estão registrados no seu nome."
        if tudo_certo
        else "Recebemos seu pagamento. Alguns domínios ainda estão em processamento; "
        "avisaremos assim que tudo estiver concluído."
    )

    texto = (
        f"Olá, {pedido['titular']['nome']}!\n\n"
        f"Pagamento do pedido {pedido['codigo']} confirmado.\n"
        f"{complemento}\n\n"
        f"{_lista_dominios(pedido)}\n\n"
        f"Acompanhe em: {URL_SITE}/pedido.html?codigo={pedido['codigo']}\n\n"
        "Lembre-se: o domínio precisa ser renovado antes de vencer.\n\n"
        "Zart Domínios"
    )
    enviar(pedido["titular"]["email"], f"Pedido {pedido['codigo']} confirmado — Zart Domínios", texto)


def avisar_admin(assunto, texto):
    enviar(EMAIL_ADMIN, f"[Zart Domínios] {assunto}", texto)
