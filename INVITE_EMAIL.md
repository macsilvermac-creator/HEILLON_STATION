# Templates de email para convites do beta

Copie o template apropriado, ajuste os campos `{...}` e envie individualmente
(ou via mail-merge com Mailgun / Sendgrid / Postmark / Resend).

---

## Template A — DPO bancário / Compliance corporativo

**Assunto:** Convite — Beta privado da plataforma que prova em juízo o uso de IA jurídica

> Olá {Nome},
>
> Sou {Seu Nome}, da Heillon Legal. Te convido para o **beta privado** da
> primeira plataforma de **auditoria forense de IA jurídica** com selo
> ICP-Brasil — defensável em juízo, em fiscalização ANPD, em DDQ
> internacional.
>
> **Por que te escolhemos:** {Razão específica — "vi seu post sobre LGPD",
> "indicação de Fulano", "compliance bancário é o nosso ICP #1", etc.}
>
> **A promessa em 1 frase:**
> *"Você usa ChatGPT/Claude normalmente. Nosso substrato grava silenciosamente
> cada interação como HDR criptográfico com timestamp ICP-Brasil. Quando a
> ANPD bater na porta, você abre o relatório e está coberto."*
>
> **O que peço de você (30 dias):**
> - Setup em 5 minutos (extensão Chrome + chave de API)
> - Usar IA jurídica como já faria normalmente
> - Rodar nosso script de validação (`python beta_test.py` — 30 segundos)
> - Preencher template de feedback estruturado ao final
>
> **O que você ganha:**
> - Tier Pro vitalício (equivalente R$ 299/mês) ao final do beta
> - Crédito como Beta Founding User na changelog pública
> - Linha direta com nosso time de produto (Discord privado)
>
> **Acesso e instruções completas:**
> {Link para BETA.md no repo OU PDF anexo}
>
> **Credenciais:**
> - URL do servidor: `{https://api.heillon-beta.com}`
> - Chave de API: `heillon_live_{XXXXXXXXXXXXXXXX}`
> - (anote — não conseguirá ver de novo no console)
>
> Aguardo seu sinal de aceite. Se preferir, agendamos 15 min em
> {calendly link} para alinhar antes.
>
> Abraço,
> {Seu Nome}
> Heillon Legal — beta@heillon.com

---

## Template B — Perito digital / Forense

**Assunto:** {Nome}, podes me ajudar a validar uma cadeia de custódia de IA?

> Olá {Nome},
>
> Vi seu trabalho em {caso/empresa/publicação}. Estou convidando ~50 peritos
> e advogados criminalistas para testar a primeira plataforma BR de cadeia
> de custódia para uso de IA em perícia digital.
>
> Critério técnico que cumprimos:
> - SHA-256 encadeado (igual perícia forense tradicional)
> - RFC 3161 + ICP-Brasil (timestamp qualificado, MP 2.200-2)
> - PDF/A-3 forense com assinatura Ed25519
> - Verificação pública (qualquer juiz/perito confere sem login)
> - Corpus normativo: LGPD + CNJ 615/2025 + OAB 001/2024 + NBC TP 01 + CPP arts. 158-A a 158-F
>
> Beta de 30 dias. Setup em 5 min. Recompensa: acesso vitalício ao tier Pro +
> crédito como Beta Founding User.
>
> Instruções: {link para BETA.md}
> Credenciais: {URL + chave}
>
> Posso contar contigo?
>
> {Seu Nome}
> Heillon Legal

---

## Template C — Banca M&A premium / Direito internacional

**Subject:** {Name}, beta private of the AI legal audit substrate Brazilian clients need

> Hi {Name},
>
> Quick context: I'm running the beta of **Heillon Legal**, an AI-audit
> substrate that produces cryptographic chain-of-custody for every prompt /
> response in ChatGPT, Claude, Gemini and OpenAI-compatible APIs. With
> ICP-Brasil qualified timestamps — defensible in BR jurisdiction AND
> compatible with eIDAS QES for EU clients.
>
> I'm inviting ~50 lawyers/firms doing cross-border M&A and Big Law-style work
> because:
> - DDQs increasingly ask for AI-audit evidence
> - EU AI Act (Aug/2026 enforcement) requires it for high-risk uses
> - Your firm shows up in {topo-of-mind / specific case / publication}
>
> 30-day private beta, no cost. 5-minute setup. You get lifetime Pro tier
> (R$ 299/mo equivalent) + Founding User credit in our changelog.
>
> Full details + credentials: {BETA.md link}
> Or 15-min call: {calendly}
>
> Best,
> {Your Name}
> Heillon Legal · beta@heillon.com

---

## Template D — Procurador estadual / federal

**Assunto:** {Nome}, beta privado — auditoria de IA para TCE/TCU em peças da PGE

> {Nome},
>
> {Cargo} na PGE-{UF}/PFN/AGU, te convido para o beta privado do Heillon
> Legal — sistema BR de auditoria forense de uso de IA em peças jurídicas.
>
> O cenário que cobrimos:
> - Lei 14.129/2021 cobra rastreabilidade de IA em atos administrativos
> - TCE-{UF} pode requerer histórico de uso de IA em execuções fiscais
> - CNMP Res. 181 (paralelo) traz preocupações similares
>
> O que entregamos:
> - Cada análise feita com IA gera HDR (Heillon Detailed Record) imutável
> - Selo ICP-Brasil em cada relatório forense
> - Verificação pública (TCE/MP/defesa podem auditar sem login)
> - Corpus normativo embutido: LGPD + Marco Civil + CPC + leis específicas
>
> Beta gratuito de 30 dias. Setup em 5 min. Inclui recompensa vitalícia.
>
> Detalhes: {BETA.md link} · Credenciais: {URL + chave}
>
> Atenciosamente,
> {Seu Nome} · Heillon Legal

---

## Template E — Quick follow-up (sem resposta em 7 dias)

**Assunto:** {Nome}, ainda dá pra entrar no beta — fechamos em {data}

> Oi {Nome},
>
> Sei que sua agenda é apertada. Só pra confirmar: o slot do beta privado
> do Heillon Legal continua reservado pra você até {data}.
>
> Em 30 segundos do seu tempo:
> - Você ganha tier Pro vitalício (R$ 299/mês equivalente)
> - Tudo que pedimos é 5 min de setup + 15 min testando + 15 min de feedback
> - Já temos {X de Y} confirmados; sua presença completaria o painel
>
> Topa? Basta responder "sim" que eu mando a chave.
>
> {Seu Nome}

---

## Boas práticas operacionais

1. **Envio em batches de 10/dia** — evita filtros anti-spam e dá vazão pra suporte
2. **Personalize cada `{Razão específica}`** — copy-paste mata conversão
3. **Use endereço pessoal** (`{seu-nome}@heillon.com`), não `noreply@`
4. **Reply em até 2h em horário comercial** — beta tester escolheu falar com você
5. **Log de quem aceitou** — planilha com: nome, email, data aceite, data ativação, data feedback recebido
6. **NDA opcional** — para DPOs bancários, ofereça assinar NDA antes do envio da chave (boa-fé)
7. **Templates anti-spam** — não use palavras tipo "GRÁTIS", "100%", excesso de !!!
8. **CTA único por email** — peça UMA coisa: "responda sim" ou "abra o link"

## Métricas a monitorar

- **Taxa de abertura** (>40% indica bom subject + remetente)
- **Taxa de aceite** (>20% indica boa relevância do alvo)
- **Tempo até ativação** (média: 24-48h após aceite)
- **Tempo até primeiro HDR** (média: < 1h após ativação)
- **Taxa de feedback** (>70% dos ativos)
- **NPS** (alvo > +30 para beta inicial)

Use `/api/v1/admin/beta-metrics` (endpoint criado em F30) para snapshot
em tempo real.
