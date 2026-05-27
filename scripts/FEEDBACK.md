# Heillon Legal — Beta Feedback Template

> Copie este arquivo para `feedback_<seu-nome>.md`, preencha, e envie por
> email para **feedback@heillon.com** com o `beta_test_report_<data>.json`
> anexado.

---

## Identificação

- **Nome / Organização:** _________________________________________
- **Papel** (advogado / juiz / DPO / perito / outro): _____________
- **Email para contato:** _________________________________________
- **Data do teste:** ______________________________________________
- **Servidor testado:** ___________________________________________
- **Versão do script:** 0.1.0 (vide `beta_test_report.environment`)

---

## Resultado do script automatizado

Cole o resumo final exibido no terminal pelo `beta_test.py` (ou anexe o
arquivo JSON gerado).

```
Cole aqui as últimas 20 linhas do script (ou descreva)
```

---

## Cenários (faça pelo menos 3 dos 5)

### Cenário 1 — Captura automática invisível

Status: [ ] não fiz · [ ] funcionou perfeito · [ ] funcionou parcialmente · [ ] não funcionou

- **ChatGPT** (`chat.openai.com`): __________ ✓/✗
- **Claude** (`claude.ai`): __________ ✓/✗
- **Gemini** (`gemini.google.com`): __________ ✓/✗

Notas livres (o que viu, o que não viu, o que esperava):
> _________________________________________________________________

**Sua avaliação 0–10**
- O toast atrapalhou seu trabalho? (0 = nem percebi, 10 = horrível) ____
- A captura funcionou sem fricção? (0 = nada, 10 = perfeito) ____
- Você confiaria nisso em juízo? (0 = nunca, 10 = absolutamente) ____

---

### Cenário 2 — Verificação pública

Status: [ ] não fiz · [ ] funcionou · [ ] funcionou parcialmente · [ ] não funcionou

- HDR ID testado: ______________________________________
- Página de verificação acessou sem login? [ ] sim [ ] não
- Conteúdo apresentado foi compreensível? [ ] sim [ ] não

Notas livres:
> _________________________________________________________________

**Sua avaliação 0–10**
- Compreensível para um juiz/perito sem treinamento técnico? ____
- Você apresentaria esta página em juízo? ____

---

### Cenário 3 — Quota e upgrade

Status: [ ] não fiz · [ ] OK · [ ] confuso

- Banner do plano Free apareceu? [ ] sim [ ] não [ ] não cheguei a usar 70%
- CTA "Ver planos" abriu site externo? [ ] sim [ ] não
- Banner pode ser dispensado por 24h? [ ] sim [ ] não

**Sua avaliação 0–10**
- O banner é intrusivo? (0 = nem percebi, 10 = irritante) ____
- O CTA fica claro? ____

**Pergunta importante de pricing:**
- Por quanto VOCÊ pagaria pelo tier Pro (HDRs ilimitados, retenção 1 ano,
  relatório forense PDF/A-3 ICP-Brasil)?
  - [ ] R$ 0 — não pagaria
  - [ ] R$ 1–99/mês
  - [ ] R$ 100–199/mês
  - [ ] R$ 200–399/mês (sweet-spot proposto: R$ 299)
  - [ ] R$ 400–699/mês
  - [ ] R$ 700+/mês
  - [ ] Outro: ___________

---

### Cenário 4 — MCP Gateway (técnico)

Status: [ ] não fiz · [ ] não aplica · [ ] testei OpenAI · [ ] testei Anthropic · [ ] ambos

Latência mensurada:
- Chamada DIRETA ao upstream: __________ ms (referência)
- Chamada via HEILLON Gateway: __________ ms
- Overhead adicionado: __________ ms

Comportamento:
- Stack quebrou em algum lugar? [ ] sim [ ] não
- LangChain/LlamaIndex/SDK seu funcionou sem mudança extra? [ ] sim [ ] não [ ] N/A
- Headers `X-Heillon-Hdr-Id` chegaram na response? [ ] sim [ ] não

**Sua avaliação 0–10**
- Latência aceitável para produção? ____
- Drop-in foi "drop-in" mesmo? ____
- Você usaria isso em produção real? ____

Notas técnicas (stack trace, headers inesperados, comportamento estranho):
```
Cole aqui se aplicável
```

---

### Cenário 5 — Streaming (técnico)

Status: [ ] não fiz · [ ] não aplica · [ ] funcionou · [ ] quebrou

- Stream veio chunk-a-chunk como direto? [ ] sim [ ] não
- HDR foi criado APÓS o `[DONE]`? [ ] sim [ ] não [ ] não consegui verificar
- O comentário `: heillon-hdr-id=...` apareceu no stream? [ ] sim [ ] não [ ] não procurei
- LangChain `agent.stream()` funcionou? [ ] sim [ ] não [ ] N/A

**Sua avaliação 0–10** (se aplica)
- Streaming "transparente" como prometido? ____

---

## Avaliação geral

### Os 3 momentos prometidos — você sentiu?

| Promessa | Sentiu? | Comentário |
|---|---|---|
| "Invisível no uso" (não atrapalha) | [ ] sim [ ] não | |
| "Inevitável em auditoria" (HDR pronto qd precisa) | [ ] sim [ ] não | |
| "Cadeia que vale em juízo" (selo ICP confiável) | [ ] sim [ ] não | |

### NPS

De 0 a 10, quanto você recomendaria o Heillon Legal para um(a) colega
em situação similar à sua?

**Sua nota: ____ / 10**

Por quê?
> _________________________________________________________________
> _________________________________________________________________

### Top 3 problemas / fricções

1. _____________________________________________________________
2. _____________________________________________________________
3. _____________________________________________________________

### Top 3 melhorias que pediria

1. _____________________________________________________________
2. _____________________________________________________________
3. _____________________________________________________________

### Você adotaria isso na sua organização?

- [ ] Sim, em até 30 dias
- [ ] Sim, em 3-6 meses
- [ ] Sim, em 12+ meses
- [ ] Depende de [______________________________]
- [ ] Não, porque [______________________________]

---

## Pergunta livre (a mais importante)

Em 3-5 frases, qual é a MAIOR razão para o Heillon Legal existir, na sua
percepção? (Use suas palavras, não as nossas.)

> _________________________________________________________________
> _________________________________________________________________
> _________________________________________________________________
> _________________________________________________________________

---

## Quer continuar conectado?

- [ ] Sim, me incluam no Discord/Slack privado de beta testers
- [ ] Sim, contatem-me para uma chamada de 30min para discutir
- [ ] Sim, me apresentem a [empresa/colega/órgão: ___________________]
- [ ] Não, prefiro só feedback escrito

---

**Obrigado.** O seu tempo aqui muda diretamente como o produto sai.
— Equipe Heillon Legal
