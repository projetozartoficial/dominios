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
├── pedido.html           Acompanhar pedido (o Mercado Pago traz o cliente de volta para cá)
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
│   ├── pedidos.py            Cria pedidos, recebe o pagamento e manda registrar
│   ├── provedor.py           Dynadot: cria o contato do titular e registra o domínio
│   ├── pagamento.py          Mercado Pago: cobrança (Pix/cartão/boleto) e webhook
│   ├── email_envio.py        E-mails para o cliente e para você (SMTP)
│   ├── banco.py              Banco de dados SQLite (pedidos e contatos)
│   ├── validacao.py          CPF, CNPJ, e-mail e domínio
│   ├── disponibilidade.py    Consulta RDAP
│   ├── http_util.py          Chamadas às APIs externas
│   ├── configuracao.py       Lê site.json e as variáveis de ambiente
│   └── .env.exemplo          Modelo das chaves secretas
├── render.yaml           Publicação do back-end no Render
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
| POST | `/api/pedidos` | Valida o titular, confere disponibilidade, calcula o total e devolve o link do Mercado Pago |
| GET | `/api/pedidos/<codigo>` | Situação do pedido (sem dados pessoais) |
| POST | `/api/pagamento/notificacao` | Aviso do Mercado Pago. Confere a assinatura, consulta o pagamento e registra na Dynadot |
| POST | `/api/contato` | Recebe a mensagem de contato |

Como funciona uma venda:

1. O cliente monta o carrinho e preenche os dados do titular.
2. O servidor recalcula o preço e cria a cobrança no Mercado Pago.
3. O cliente paga no Mercado Pago (Pix, cartão ou boleto) e volta para `pedido.html`.
4. O Mercado Pago avisa o servidor. O servidor confere se o aviso é verdadeiro e se o valor está certo.
5. O servidor cria o contato do titular na Dynadot e registra cada domínio.
6. O cliente recebe um e-mail de confirmação, e você recebe um aviso de venda. Se algum domínio falhar, o aviso diz qual registrar manualmente.

Os pedidos ficam no banco `zart.db`, dentro de `backend/dados/` ou da pasta em `PASTA_DADOS`. Essa pasta fica fora do GitHub pelo `.gitignore`, porque tem dados pessoais.

---

## Como publicar

- **Só afiliado:** a pasta inteira pode ir para o GitHub Pages, sem o back-end.
- **Com revenda:** o back-end precisa de um servidor que rode Python (ex.: Render, Railway ou uma VPS).
  Coloque as chaves no `.env` do servidor e o endereço do site em `ORIGEM_PERMITIDA`.

---

## Como colocar a revenda no ar

O código já está pronto. Faltam as contas, que precisam ser criadas por você:

1. **Dynadot**
   - Crie a conta e coloque saldo. Ela cobra em dólar, do saldo, a cada registro.
   - Em **Tools → API**, gere a chave de produção e a chave do sandbox.
   - Se a Dynadot pedir uma lista de IPs liberados, coloque o IP do servidor.
2. **Mercado Pago**
   - Use a sua conta (de preferência no CNPJ do MEI).
   - Em **Suas integrações**, crie uma aplicação do tipo Checkout Pro e copie o *Access Token*.
   - Em **Webhooks**, coloque `https://SEU-BACKEND/api/pagamento/notificacao`, marque o evento **Pagamentos** e copie a **assinatura secreta**.
3. **Render**
   - No render.com, escolha **New → Blueprint** e selecione este repositório. Ele lê o `render.yaml`.
   - Preencha as chaves em *Environment*.
   - O `render.yaml` usa plano pago com disco, porque sem disco os pedidos somem quando o servidor reinicia. Confira o preço no site do Render.
4. **Ligar o site ao back-end**
   - No `dados/site.json`, coloque em `api.url` o endereço que o Render mostrar.
   - Coloque esse mesmo endereço em `URL_API` no Render.
5. **Testar antes de vender**
   - Deixe `DYNADOT_MODO_TESTE=sim` e use as credenciais **de teste** do Mercado Pago.
   - Faça uma compra completa.
   - Se tudo funcionar, troque para as credenciais de produção e coloque `DYNADOT_MODO_TESTE=nao`.

Outros cuidados:

- **Preços:** a Dynadot cobra em dólar e você cobra em reais. Deixe margem para o câmbio e para a taxa do Mercado Pago.
- **E-mails:** sem o SMTP configurado, a venda funciona, mas os e-mails só aparecem no log do servidor.
- **Afiliados:** troque os `SEU-LINK-DE-AFILIADO` no `site.json` pelos seus links.

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
