# Zart Domínios

Primeiro projeto do grupo **Zart**. Site para pesquisar e vender domínios (afiliado + revenda).

Funciona de dois jeitos:

- **Revenda** ("Compra aqui"): o cliente compra no seu site, e o registro é feito por um provedor (API).
- **Afiliado / externo** ("Parceiro"): o botão leva ao site do parceiro, e você ganha comissão.

Cores: azul meia-noite `#191970` (principal), azul-escuro e preto.

---

## Estrutura

```
site-dominios/
├── index.html            Página inicial: busca, extensões, como funciona, dúvidas
├── carrinho.html         Carrinho e dados do titular
├── contato.html          Formulário de contato
├── termos.html           Termos de Uso
├── privacidade.html      Política de Privacidade (LGPD)
├── cookies.html          Política de Cookies
├── reembolso.html        Cancelamento e Reembolso
├── dados/
│   └── site.json         ⭐ ÚNICO arquivo de configuração (nome, logo, empresa, preços, links)
├── assets/
│   ├── css/style.css     Todo o visual, dividido em seções numeradas
│   ├── img/              zart-logo.png, favicon.png, apple-touch-icon.png e zart-icone-512.png
│   └── js/
│       ├── config.js         Lê o site.json
│       ├── layout.js         Cabeçalho, rodapé, título e ícone da aba
│       ├── dominios.js       Validação, disponibilidade (RDAP) e links de parceiro
│       ├── carrinho.js       Carrinho salvo no navegador
│       ├── cookies.js        Aviso e consentimento de cookies
│       ├── util.js           Funções pequenas (preço, notificações...)
│       └── pagina-*.js       Código de cada página
├── backend/              Parte de REVENDA, em Python (sem instalar nada)
│   ├── servidor.py           Rotas da API
│   ├── pedidos.py            Cria pedidos e guarda contatos
│   ├── validacao.py          CPF, CNPJ, e-mail e domínio
│   ├── disponibilidade.py    Consulta RDAP
│   ├── provedor.py           ⚠ Integração com o provedor (a completar)
│   ├── pagamento.py          ⚠ Integração com o pagamento (a completar)
│   ├── configuracao.py       Lê site.json e .env
│   └── .env.exemplo          Modelo das chaves secretas
└── docs/requisitos.md    Requisitos, regras de negócio e diagramas UML
```

---

## Como personalizar

Tudo fica em **`dados/site.json`**:

| O que mudar | Onde |
|---|---|
| Nome do site | `identidade.nome` (hoje "Zart Domínios"). `submarca` é o texto ao lado da logo e `grupo` aparece no rodapé |
| Logo | Coloque o arquivo em `assets/img/` e mude `identidade.logo` |
| Ícone da aba (logo na URL) | `identidade.favicon` (coroa + Z). Para celular existe também o `apple-touch-icon.png` |
| Dados da empresa (rodapé e políticas) | `empresa` |
| Preços de revenda | `preco` e `renovacao` de cada extensão |
| Link de afiliado | `link` da extensão. Use `{dominio}` onde entra o domínio pesquisado |
| Ligar o back-end | `api.url` (ex.: `https://api.seudominio.com.br`) |
| Google Analytics | `analytics.googleAnalyticsId` (só carrega se o visitante aceitar) |

Cada extensão tem um `modo`:

- `"revenda"`: aparece com preço e vai para o carrinho.
- `"afiliado"`: botão leva ao parceiro com link de afiliado (`rel="sponsored"`).
- `"externo"`: botão leva a um site oficial sem comissão (ex.: Registro.br para `.com.br`).

> Os preços que estão no `site.json` são **exemplos**. Coloque os seus antes de publicar.
> Confira também se o link do Registro.br abre a busca certa.

---

## Como testar no computador

O site lê o `site.json` com `fetch`, então ele precisa de um servidor (abrir o arquivo direto com dois cliques não funciona):

```bash
cd site-dominios
python -m http.server 8000
```

Abra `http://localhost:8000`.

### Back-end (revenda)

```bash
cd site-dominios/backend
copy .env.exemplo .env       # no Windows  (no Linux/Mac: cp .env.exemplo .env)
python servidor.py
```

Depois coloque `"url": "http://localhost:8080"` em `api` no `site.json`.

Rotas:

| Método | Rota | O que faz |
|---|---|---|
| GET | `/api/disponibilidade?dominio=x.com` | Diz se o domínio está livre |
| POST | `/api/pedidos` | Valida o titular, confere disponibilidade, calcula o total e cria o pedido |
| POST | `/api/contato` | Recebe a mensagem de contato |

Os pedidos ficam em `backend/dados/` (fora do GitHub pelo `.gitignore`, porque têm dados pessoais).

---

## Como publicar

- **Só afiliado:** a pasta inteira pode ir para o GitHub Pages, sem o back-end.
- **Com revenda:** o back-end precisa de um servidor que rode Python (ex.: Render, Railway ou uma VPS).
  Coloque as chaves no `.env` do servidor e o endereço do site em `ORIGEM_PERMITIDA`.

---

## O que falta para vender de verdade

1. Escolher o provedor de revenda e completar `backend/provedor.py` com a API dele.
2. Escolher o serviço de pagamento e completar `backend/pagamento.py`. Falta também a rota que recebe a confirmação do pagamento (webhook) e só então chama `registrar_dominio()`.
3. Enviar e-mails (confirmação do pedido e aviso de renovação).
4. Preencher os dados da empresa no `site.json`. Enquanto estiverem vazios, aparecem em amarelo como "a preencher".
5. Pedir para um advogado revisar os textos legais. Eles são modelos.

---

## Checklist para não ter problema (17 itens)

| # | Item | Situação |
|---|---|---|
| 1 | Política de privacidade | ✅ `privacidade.html` |
| 2 | Termos de serviço | ✅ `termos.html` |
| 3 | Aviso de cookies | ✅ Caixa de escolha na primeira visita + "Preferências de cookies" no rodapé |
| 4 | Política de reembolso | ✅ `reembolso.html`, com os 7 dias do art. 49 do CDC |
| 5 | Formulários na LGPD | ✅ Caixa de consentimento e link para a política em todos os formulários |
| 6 | Só dados necessários | ✅ Compra: nome, e-mail e CPF/CNPJ. Contato: nome, e-mail e mensagem |
| 7 | Scripts de tracking | ✅ Nenhum por padrão. O Analytics só carrega depois do "Aceitar" |
| 8 | Acessibilidade | ✅ Link "Pular para o conteúdo", `label` em todos os campos, avisos lidos por leitores de tela |
| 9 | Alt nas imagens | ✅ Sem imagens de conteúdo. A logo ao lado do nome usa `alt=""` porque o nome já está escrito |
| 10 | Contraste corrigido | ✅ Todos os textos com contraste de 5,5:1 ou mais (mínimo exigido: 4,5:1) |
| 11 | Navegação por teclado | ✅ Contorno de foco visível, menu fecha com Esc, tudo funciona com Tab e Enter |
| 12 | Sem avaliações falsas | ✅ O site não tem depoimentos |
| 13 | Sem promessas sem comprovação | ✅ Sem "o mais barato" ou "o melhor". Só compromissos que o site cumpre |
| 14 | Copyright das imagens | ✅ Só ícones próprios em SVG, sem fontes ou imagens de terceiros |
| 15 | Dados da empresa | ⚠ O lugar já está pronto no rodapé e nas políticas: **preencha no `site.json`** |
| 16 | Conformidade LGPD | ✅ Base legal, compartilhamento, prazos e direitos do titular explicados. ⚠ Falta nomear o encarregado (DPO) |
| 17 | Riscos jurídicos | ⚠ Links de afiliado identificados, uso de marcas de terceiros proibido nos termos. **Falta a revisão de um advogado** |
