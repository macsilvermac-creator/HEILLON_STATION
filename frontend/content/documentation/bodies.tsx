/**
 * Textos institucionais da Central de Documentação — Heillon Legal (PT-BR).
 * Atualizado para o Beta Privado — Coletores + Quota + Conta (Mai 2026).
 *
 * Nota de copy: no beta, o selo de tempo ATIVO é o RFC 3161; o selo
 * ICP-Brasil qualificado entra na sequência ("arquitetura pronta").
 */

import {
  ApiBlock,
  Badge,
  Callout,
  FlowDiagram,
  RegTable,
  ScreenFrame,
  StatCard,
  StatGrid,
  Step,
  Steps,
} from "@/components/docs/DocsPrimitives";

// ══════════════════════════════════════════════════════════════════════════════
// QUICKSTART
// ══════════════════════════════════════════════════════════════════════════════

export function BodyQuickstart() {
  return (
    <>
      <Callout variant="tip" title="Início em 5 minutos">
        Este guia leva-o do zero ao primeiro <strong>HDR verificável</strong> em menos de 5 minutos.
        Não é necessária configuração de ambiente — basta criar conta, gerar uma chave de API
        e ativar um coletor.
      </Callout>

      <h2 id="qs-visao">O que é o Heillon Legal?</h2>
      <p>
        O Heillon Legal é o <strong>substrato de auditoria de IA jurídica</strong>: cada vez que
        você usa ChatGPT, Claude, Gemini ou outra IA no trabalho, a plataforma gera um{" "}
        <strong>HDR (Heillon Decision Record)</strong> — um registo imutável com hash SHA-256,
        carimbo temporal RFC 3161 e encadeamento criptográfico. Qualquer decisão pode ser
        auditada, verificada e apresentada como prova técnica.
      </p>

      <Callout variant="info" title="Captura passiva por coletores">
        Você não precisa colar prompts manualmente. Os <strong>coletores</strong> observam o uso
        de IA e geram HDRs em background: a <strong>Extensão do Browser</strong> (Coletor #1) e o{" "}
        <strong>Gateway MCP/API</strong> compatível com OpenAI e Anthropic (Coletor #2). Você
        continua trabalhando normalmente — o Heillon cuida do registo.
      </Callout>

      <StatGrid>
        <StatCard value="2" label="Coletores (Extensão + Gateway)" icon="🛰" />
        <StatCard value="50" label="HDRs/mês no plano grátis" icon="🎟" />
        <StatCard value="RFC 3161" label="Selo de tempo ativo" icon="⏱" />
        <StatCard value="9" label="Jurisdições no corpus" icon="🌍" />
      </StatGrid>

      <h2 id="qs-fluxo">Fluxo rápido (captura passiva)</h2>
      <FlowDiagram steps={[
        { icon: "👤", label: "Criar conta",    sub: "/register" },
        { icon: "🔑", label: "Gerar chave",    sub: "onboarding" },
        { icon: "🛰", label: "Ativar coletor", sub: "Extensão / Gateway" },
        { icon: "💬", label: "Usar IA",        sub: "ChatGPT/Claude/…" },
        { icon: "🔐", label: "HDR gerado",     sub: "em background" },
        { icon: "🔍", label: "Verificar",      sub: "/verification" },
      ]} />

      <h2 id="qs-passo1">Passo 1 — Criar conta de operador</h2>
      <Steps>
        <Step n={1} title="Aceder a /register">
          Clique em <strong>Entrar</strong> na barra superior e depois em <em>Criar conta</em>.
          Preencha nome, e-mail institucional e palavra-passe (mín. 8 caracteres).
        </Step>
        <Step n={2} title="Confirmação automática">
          Após o registo, é autenticado automaticamente. O sistema atribui
          um <code>organization_id</code> único ao seu tenant.
        </Step>
      </Steps>

      <ScreenFrame url="heillon-legal-ui.vercel.app/register">
        <div className="space-y-2 p-2">
          <div className="h-8 w-48 rounded-md bg-white/[0.06] px-3 py-1.5 text-[11px] text-white/40">Nome completo</div>
          <div className="h-8 w-48 rounded-md bg-white/[0.06] px-3 py-1.5 text-[11px] text-white/40">E-mail institucional</div>
          <div className="h-8 w-48 rounded-md bg-white/[0.06] px-3 py-1.5 text-[11px] text-white/40">Palavra-passe</div>
          <div className="mt-2 h-8 w-32 rounded-md text-[11px] font-bold text-[#040810]"
            style={{ background: "linear-gradient(135deg,#EDD97A,#C9A227)", display:"flex", alignItems:"center", justifyContent:"center" }}>
            Criar conta
          </div>
        </div>
      </ScreenFrame>

      <h2 id="qs-passo2">Passo 2 — Gerar a chave de API (onboarding)</h2>
      <p>
        Logo após o registo, o assistente de <strong>onboarding em 3 passos</strong>
        (<code>/conta/onboarding</code>) gera a sua primeira chave de API. A chave conecta
        os coletores à sua conta e tem o formato <code>heillon_live_…</code>.
      </p>
      <Steps>
        <Step n={1} title="Abrir o onboarding">
          Após registar-se é levado a <code>/conta/onboarding</code>. Clique em <em>Próximo</em>.
        </Step>
        <Step n={2} title="Gerar minha chave">
          Clique em <strong>Gerar minha chave</strong>. Copie-a imediatamente — por segurança,
          a chave em texto puro é mostrada uma única vez. Pode revogar e gerar novas em{" "}
          <a href="/conta/api-keys" className="text-gold-300 underline">Chaves de API</a>.
        </Step>
      </Steps>

      <h2 id="qs-passo3">Passo 3 — Ativar um coletor</h2>
      <p>
        Escolha como o Heillon vai observar o seu uso de IA. Os dois coletores são complementares
        — pode usar ambos com a mesma chave.
      </p>
      <Steps>
        <Step n={1} title="Coletor #1 — Extensão do Browser">
          Instale a extensão (Chrome MV3), abra as Opções e cole a chave de API + a URL do servidor.
          A partir daí, cada par pergunta→resposta em ChatGPT, Claude ou Gemini gera um HDR.
        </Step>
        <Step n={2} title="Coletor #2 — Gateway MCP/API">
          Aponte o seu SDK OpenAI/Anthropic para o Gateway do Heillon e envie a chave no header{" "}
          <code>X-Heillon-Api-Key</code>. Cada chamada é auditada e devolve o <code>hdr_id</code>
          nos headers de resposta.
        </Step>
      </Steps>

      <h2 id="qs-passo4">Passo 4 — Verificar publicamente</h2>
      <p>
        Aceda a <strong>/verification</strong> e cole qualquer <code>hdr_id</code>.
        A verificação é <em>pública e sem autenticação</em> — qualquer magistrado,
        contraparte ou auditor pode validar a cadeia criptográfica.
      </p>

      <Callout variant="success" title="Primeiro HDR criado!">
        Parabéns — o seu primeiro Heillon Decision Record está na cadeia.
        Para o fluxo manual de evidências e casos (cockpit web), consulte o{" "}
        <a href="/docs/usage" className="text-gold-300 underline">Manual de Uso</a>; para a base
        criptográfica, o <a href="/docs/chain-of-custody" className="text-gold-300 underline">Manual da Cadeia de Custódia</a>.
      </Callout>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// MANUAL DE USO GERAL
// ══════════════════════════════════════════════════════════════════════════════

export function BodyManualUsage() {
  return (
    <>
      <Callout variant="info">
        Este manual cobre todos os fluxos do cockpit web Heillon Legal — captura passiva por
        coletores, conta, quota e o fluxo manual de casos. Para início rápido, consulte primeiro
        o <a href="/docs/quickstart" className="text-gold-300 underline">Guia de Início Rápido</a>.
      </Callout>

      <Callout variant="tip" title="Dois modos de uso">
        <strong>Captura passiva (recomendado):</strong> ative um coletor e o Heillon registra o
        seu uso de IA automaticamente. <strong>Fluxo manual (cockpit):</strong> ingira evidências
        e crie casos diretamente na plataforma. Ambos produzem o mesmo HDR verificável.
      </Callout>

      <h2 id="autenticacao">1. Autenticação e sessão</h2>
      <p>
        O Heillon Legal usa <strong>cookies HttpOnly</strong> para autenticação —
        o token JWT nunca é exposto ao JavaScript do browser, eliminando a classe
        de ataques XSS sobre credenciais.
      </p>
      <Steps>
        <Step n={1} title="Registar conta">
          Aceda a <code>/register</code>. E-mail institucional + password (bcrypt).
          O sistema atribui <code>organization_id</code> único.
        </Step>
        <Step n={2} title="Entrar">
          Aceda a <code>/login</code> ou clique <strong>Entrar</strong> na topbar.
          O cookie <code>heillon_session</code> é emitido com <code>HttpOnly; Secure; SameSite=Lax</code>.
        </Step>
        <Step n={3} title="Sessão mantida automaticamente">
          Todas as rotas autenticadas usam o cookie. Não é necessário gerir tokens manualmente.
        </Step>
      </Steps>

      <Callout variant="warning" title="Multi-tenant">
        Todas as operações estão isoladas por <code>organization_id</code>.
        Um operador nunca consegue ver missões, evidências ou HDRs de outro tenant.
      </Callout>

      <h2 id="painel">2. Painel (Dashboard)</h2>
      <p>
        O <strong>Painel</strong> (<code>/dashboard</code>) apresenta métricas em tempo real:
        HDRs emitidos, missões ativas, evidências ingeridas e estado dos agentes.
        Os gráficos Recharts carregam de forma lazy para não bloquear o bundle principal.
      </p>

      <ScreenFrame url="heillon-legal-ui.vercel.app/dashboard">
        <div className="grid grid-cols-3 gap-2 p-2">
          {["HDRs emitidos", "Missões ativas", "Evidências"].map((label, i) => (
            <div key={i} className="rounded-lg border border-white/8 bg-white/[0.03] p-3 text-center">
              <div className="text-xl font-bold" style={{ color: "#D4AF37" }}>{["42", "7", "128"][i]}</div>
              <div className="text-[10px] text-white/50">{label}</div>
            </div>
          ))}
        </div>
        <div className="mt-2 h-16 rounded-lg border border-white/8 bg-white/[0.02] p-2">
          <div className="text-[10px] text-white/30">Gráfico HDR por dia (lazy Recharts)</div>
          <div className="mt-1 flex items-end gap-1 h-8">
            {[30, 55, 40, 80, 45, 90, 60].map((h, i) => (
              <div key={i} className="flex-1 rounded-sm" style={{ height: `${h}%`, background: "rgba(212,175,55,0.4)" }} />
            ))}
          </div>
        </div>
      </ScreenFrame>

      <h2 id="evidencias">3. Ingestão de evidências</h2>
      <p>
        A rota <code>/ingestion</code> suporta qualquer ficheiro digital.
        Para <strong>PDF e DOCX</strong>, o sistema extrai automaticamente o texto
        completo (PyMuPDF + python-docx) antes de calcular o hash.
      </p>

      <Steps>
        <Step n={1} title="Escolher ficheiro">
          Arraste para a área de upload ou clique para selecionar.
          Suporte a PDF, DOCX, TXT, imagens e qualquer formato binário.
        </Step>
        <Step n={2} title="Cálculo SHA-256">
          O backend calcula o hash SHA-256 do conteúdo binário exato.
          O hash é determinístico — o mesmo ficheiro produz sempre o mesmo hash.
        </Step>
        <Step n={3} title="HDR de ingestão emitido">
          Um HDR com <code>hdr_type=ingestion</code> é criado e armazenado.
          O campo <code>previous_hdr</code> pode encadear com um HDR anterior da mesma organização.
        </Step>
        <Step n={4} title="Armazenamento WORM">
          O ficheiro é gravado no diretório de evidências com política WORM
          (Write Once, Read Many) — sem possibilidade de modificação posterior.
        </Step>
      </Steps>

      <ApiBlock method="POST" path="/api/v1/ingestion" description="Upload de evidência — multipart/form-data. Retorna hdr_id." auth />

      <h2 id="missoes">4. Casos (Missões EASY) — ciclo completo</h2>
      <Callout variant="info">
        Na navegação, este fluxo aparece como <strong>Casos</strong> (vernáculo jurídico).
        Internamente, o motor de orquestração continua a chamar-se EASY.
      </Callout>

      <FlowDiagram steps={[
        { icon: "📝", label: "DRAFT",     sub: "Planeamento" },
        { icon: "⏳", label: "PENDING",   sub: "Aguarda aprovação" },
        { icon: "✅", label: "APPROVED",  sub: "Pronto p/ execução" },
        { icon: "⚙️", label: "RUNNING",   sub: "EASY executa" },
        { icon: "🏁", label: "COMPLETED", sub: "HDRs gerados" },
      ]} />

      <h3 id="missoes-planear">4.1 Planeamento</h3>
      <p>
        Em <code>/missions</code>, descreva a intenção em linguagem natural e liste
        os agentes autorizados. O motor EASY converte a descrição num DAG
        (grafo acíclico dirigido) de tarefas via <code>lexicon.KEYWORD_AGENT_MAP</code>.
      </p>

      <h3 id="missoes-normativo">4.2 Validação normativa automática</h3>
      <p>
        Antes de qualquer execução, o <strong>Corpus Normativo</strong> (FTS5) avalia
        a intenção da missão. Se a missão violar regras LGPD, CNJ, OAB ou qualquer
        framework ativo, fica bloqueada — <code>HTTP 403</code> em <code>/approve</code>.
      </p>
      <Callout variant="warning" title="Gate normativo não pode ser ignorado">
        Não existe forma de contornar a validação normativa. Missões bloqueadas
        exigem reformulação da intenção ou declaração explícita de base legal válida.
      </Callout>

      <h3 id="missoes-aprovar">4.3 Aprovação humana (human-in-the-loop)</h3>
      <p>
        Toda missão passa por aprovação humana obrigatória. Este gate assegura
        conformidade com CNJ 615/2025 (Judiciário) e OAB Rec. 001/2024 (Advocacia).
      </p>
      <ApiBlock method="POST" path="/api/v1/mission/{id}/approve" description="Aprovar missão — muda estado PENDING→APPROVED." auth />

      <h3 id="missoes-executar">4.4 Execução e geração de HDRs</h3>
      <p>
        Com estado <code>APPROVED</code>, o motor EASY executa cada nó do DAG.
        Cada passo gera um HDR encadeado com carimbo temporal RFC 3161.
        O campo <code>previous_hdr</code> garante a cadeia criptográfica.
      </p>

      <h2 id="verificacao">5. Verificação pública</h2>
      <p>
        Qualquer HDR pode ser verificado sem autenticação em <code>/verification</code>.
        Cole o <code>hdr_id</code> e o sistema valida: hash SHA-256, carimbo TSA,
        encadeamento com HDR anterior e assinatura ICP-Brasil (quando disponível).
      </p>

      <Callout variant="success" title="Verificação por terceiros">
        Magistrados, peritos contrários e auditores externos podem verificar
        qualquer HDR diretamente no portal público — sem conta, sem instalação.
      </Callout>

      <ApiBlock method="GET" path="/api/v1/verify/{hdr_id}" description="Verificação pública — sem autenticação." />
      <ApiBlock method="GET" path="/api/v1/verify/icp/{hdr_id}" description="Verificação com validação da assinatura ICP-Brasil." />

      <h2 id="diario">6. Diário de bordo das missões</h2>
      <p>
        Em <code>/diary</code>, o operador pode registar notas cronológicas vinculadas
        a missões específicas. Cada entrada é armazenada com timestamp imutável
        e associada ao <code>organization_id</code> do tenant.
      </p>

      <h2 id="agentes">7. Modelos de IA (soberania de modelos)</h2>
      <p>
        Em <code>/agent-config</code> (rótulo <strong>Modelos de IA</strong> na navegação),
        configure os modelos que o EASY pode usar:
      </p>
      <ul>
        <li><strong>Ollama</strong> — modelos locais (Llama 3, Mistral, etc.) sem dados saírem do servidor</li>
        <li><strong>OpenAI</strong> — GPT-4o, GPT-4 Turbo via API key do tenant</li>
        <li><strong>Anthropic</strong> — Claude 3.5, Claude 3 via API key do tenant</li>
        <li><strong>Custom</strong> — qualquer endpoint OpenAI-compatible</li>
      </ul>
      <Callout variant="danger" title="Chaves de API encriptadas">
        Todas as chaves de API são encriptadas com Fernet antes de serem armazenadas.
        A chave Fernet do servidor nunca é acessível via API.
      </Callout>

      <h2 id="normativo">8. Normas (corpus normativo) e conformidade</h2>
      <p>
        Em <code>/normative</code> (rótulo <strong>Normas</strong> na navegação), pesquise o
        corpus de regras legais usando busca FTS5 (full-text search). Gere relatórios de
        conformidade LGPD/GDPR para casos específicos e exporte em PDF.
      </p>

      <h2 id="coletores">9. Coletores — captura passiva de IA</h2>
      <p>
        Os <strong>coletores</strong> observam o seu uso de IA e geram HDRs em background, sem
        que você precise colar prompts manualmente. Todos se autenticam pela chave de API
        (<code>heillon_live_…</code>) e respeitam a quota do seu plano.
      </p>

      <h3 id="coletores-extensao">9.1 Coletor #1 — Extensão do Browser</h3>
      <p>
        Extensão Chrome (Manifest V3, compatível com Edge e Brave) que captura conversas em
        ChatGPT, Claude e Gemini. Após instalar, abra as Opções e defina a URL do servidor + a
        chave de API. A chave fica em <code>chrome.storage.local</code> (nunca sincronizada).
      </p>
      <ApiBlock method="GET" path="/api/v1/extension/health" description="Valida a chave e a quota (a extensão revalida a cada ~15 min)." auth />
      <ApiBlock method="POST" path="/api/v1/extension/capture" description="Registra um par pergunta→resposta e devolve o hdr_id." auth />

      <h3 id="coletores-gateway">9.2 Coletor #2 — Gateway MCP/API</h3>
      <p>
        Proxy drop-in compatível com a API OpenAI e com a API Anthropic Messages. Aponte o seu
        SDK para o Gateway e envie a chave no header <code>X-Heillon-Api-Key</code>: cada chamada
        é auditada e o <code>hdr_id</code>, a quota usada e o limite voltam nos headers de resposta.
        Suporta respostas em streaming (SSE).
      </p>
      <ApiBlock method="POST" path="/gateway/v1/chat/completions" description="Proxy OpenAI Chat Completions com auditoria HDR." auth />
      <ApiBlock method="POST" path="/gateway/anthropic/v1/messages" description="Proxy Anthropic Messages com auditoria HDR." auth />

      <Callout variant="warning" title="Console standalone continua ativo">
        Além dos coletores, o console web continua disponível para ingestão manual de
        evidências e criação de casos. Os três caminhos produzem o mesmo HDR verificável.
      </Callout>

      <h2 id="chaves-api">10. Chaves de API</h2>
      <p>
        Em <code>/conta/api-keys</code> você cria, lista e revoga as chaves usadas pelos coletores
        (Extensão, Gateway ou integrações próprias). Por segurança:
      </p>
      <ul>
        <li>A chave em texto puro é exibida <strong>uma única vez</strong>, no momento da criação.</li>
        <li>Depois, apenas o prefixo e a data de último uso (<code>last_used_at</code>) ficam visíveis.</li>
        <li>Revogar uma chave é imediato e não afeta os HDRs já registrados.</li>
      </ul>

      <h2 id="conta-quota">11. Conta, quota e planos</h2>
      <p>
        Em <code>/conta/quota</code> (rótulo <strong>Conta</strong>) acompanhe o uso da sua
        organização no período e quando ele renova. O plano define limite mensal de HDRs,
        retenção e disponibilidade do relatório forense.
      </p>
      <div className="my-5 overflow-x-auto rounded-xl border border-white/10">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-white/8 bg-white/[0.03] text-left text-[10px] uppercase tracking-wider text-white/50">
              <th className="px-4 py-3">Plano</th>
              <th className="px-4 py-3">HDRs/mês</th>
              <th className="px-4 py-3">Retenção</th>
              <th className="px-4 py-3">Usuários</th>
              <th className="px-4 py-3">PDF forense</th>
            </tr>
          </thead>
          <tbody className="text-white/75">
            {[
              ["Free",       "50",        "30 dias",  "1",    "—"],
              ["Pro",        "Ilimitado", "1 ano",    "1",    "✓"],
              ["Team",       "Ilimitado", "5 anos",   "Até 10","✓"],
              ["Enterprise", "Ilimitado", "Indefinida","Sem limite","✓"],
            ].map(([plan, hdr, ret, users, pdf], i) => (
              <tr key={i} className="border-b border-white/6 hover:bg-white/[0.02]">
                <td className="px-4 py-3 font-medium text-gold-300/90">{plan}</td>
                <td className="px-4 py-3">{hdr}</td>
                <td className="px-4 py-3">{ret}</td>
                <td className="px-4 py-3">{users}</td>
                <td className="px-4 py-3">{pdf}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Callout variant="info" title="Quota atingida">
        Ao esgotar a quota do período, os coletores recebem <code>HTTP 402</code> e param de
        registrar até a renovação ou o upgrade de plano. A contratação de planos pagos é feita
        no site institucional — fora do console.
      </Callout>

      <h2 id="conta-eliminar">12. Privacidade e eliminação de conta</h2>
      <p>
        Em <code>/privacy</code> você exerce os direitos do titular (LGPD Art. 18). A
        <strong> auto-eliminação imediata</strong> de conta anonimiza os seus dados pessoais e
        revoga as chaves de API, mas <strong>preserva os HDRs já emitidos</strong> — pelo seu
        valor probatório e pela integridade da cadeia.
      </p>
      <ApiBlock method="DELETE" path="/api/v1/privacy/account" description="Auto-eliminação imediata (Art. 18 VI) — anonimiza, revoga chaves, preserva HDRs." auth />
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// CADEIA DE CUSTÓDIA
// ══════════════════════════════════════════════════════════════════════════════

export function BodyChainCustody() {
  return (
    <>
      <Callout variant="info">
        Este manual explica a arquitetura criptográfica do HDR Ledger —
        a base técnica do valor probatório da plataforma.
      </Callout>

      <h2 id="hdr-o-que-e">O que é um HDR?</h2>
      <p>
        O <strong>Heillon Decision Record (HDR)</strong> é uma estrutura criptográfica fechada
        que documenta, passo-a-passo, ocorrências relevantes dentro de uma missão EASY:
        agente utilizado, intenção, resultado normativo, fingerprints de entrada/saída e metadados de tempo.
      </p>

      <StatGrid>
        <StatCard value="SHA-256" label="Algoritmo de hash" icon="🔐" />
        <StatCard value="RFC 3161" label="Padrão de carimbo" icon="⏱" />
        <StatCard value="CAdES-BES" label="Assinatura ICP-Brasil" icon="📜" />
        <StatCard value="Ed25519" label="Assinatura manifesto" icon="✍" />
      </StatGrid>

      <h2 id="hdr-hash">Por que SHA-256?</h2>
      <p>
        O SHA-256 produz uma impressão digital de 256 bits (64 hex) única para cada conteúdo.
        Qualquer alteração de um único byte produz um hash completamente diferente.
        É o mesmo algoritmo usado por Bitcoin, certificados TLS e sistemas judiciais digitais globais.
      </p>

      <ScreenFrame title="Exemplo de HDR — campos principais">
        <pre className="text-[11px] text-emerald-300 overflow-x-auto">{`{
  "hdr_id":       "a3f8c2d1e4b7...",   // SHA-256 do payload canónico
  "hdr_type":     "execution",
  "mission_id":   "msn_abc123",
  "agent_id":     "LEGAL_ANALYSIS_AGENT",
  "payload_hash": "7b3e9f2c1a0d...",   // SHA-256 do conteúdo
  "timestamp":    "2026-05-25T14:30:00Z",
  "tsa_token":    "MIIBrTCBl...",       // RFC 3161 ICP-Brasil
  "previous_hdr": "d9c4a1b2e3f6...",   // Encadeamento ← HDR anterior
  "normative_check": {
    "allowed": true,
    "framework": "LGPD-BR",
    "rules_matched": ["LEGAL-001", "LEGAL-003"]
  }
}`}</pre>
      </ScreenFrame>

      <h2 id="hdr-tsa">Carimbos temporais RFC 3161</h2>
      <Callout variant="info" title="Selo ativo no beta">
        No beta privado, o selo de tempo <strong>ativo</strong> é o <strong>RFC 3161</strong>, com
        a cadeia de custódia íntegra. A assinatura <strong>ICP-Brasil qualificada</strong>
        (Serpro/Certisign com certificado A1) tem a arquitetura pronta e entra na sequência.
      </Callout>
      <p>
        Quando ativada, o Heillon Legal usa a cadeia de carimbos <strong>ICP-Brasil</strong>:
      </p>
      <ol>
        <li><strong>Certisign</strong> — AC Certisign Múltipla G6 (1ª opção)</li>
        <li><strong>Serpro</strong> — Autoridade Certificadora Serpro (2ª opção)</li>
        <li><strong>FreeTSA</strong> — fallback público RFC 3161</li>
        <li><strong>Stub</strong> — apenas em dev/CI (<code>FORCE_STUB_TIMESTAMP=true</code>)</li>
      </ol>

      <Callout variant="danger" title="Stubs nunca em produção">
        O ambiente de produção rejeita automaticamente <code>FORCE_STUB_TIMESTAMP=true</code>.
        Qualquer HDR com carimbo stub não tem valor probatório e aparece com aviso explícito.
      </Callout>

      <h2 id="hdr-encadeamento">Encadeamento append-only</h2>
      <p>
        Cada HDR referencia o campo <code>previous_hdr</code> do registo anterior da mesma missão.
        Esta cadeia é verificável publicamente — qualquer quebra (hash não correspondente)
        é detectada imediatamente pelo portal de verificação.
      </p>

      <FlowDiagram steps={[
        { icon: "📄", label: "HDR #1", sub: "previous_hdr: null" },
        { icon: "→",  label: "",       sub: "" },
        { icon: "📄", label: "HDR #2", sub: "previous_hdr: #1" },
        { icon: "→",  label: "",       sub: "" },
        { icon: "📄", label: "HDR #3", sub: "previous_hdr: #2" },
        { icon: "🔍", label: "Verificar", sub: "cadeia íntegra" },
      ]} />

      <h2 id="hdr-icp-assinatura">Assinatura ICP-Brasil (CAdES-BES)</h2>
      <p>
        Quando configurado com certificado A1 PKCS#12, o sistema produz assinaturas
        <strong>CAdES-BES</strong> (Cryptographic Message Syntax Advanced Electronic Signature —
        Basic Electronic Signature) conforme MP 2.200-2/2001 e Lei 11.419/2006.
      </p>
      <p>
        O endpoint <code>GET /api/v1/verify/icp/{"{hdr_id}"}</code> valida a assinatura
        ICP-Brasil de forma pública e independente.
      </p>

      <h2 id="hdr-forense">Pacote forense completo</h2>
      <p>
        Após uma missão concluída, gere o pacote forense em <code>/missions/{"{id}"}</code>.
        O pacote inclui:
      </p>
      <ul>
        <li><strong>executive_report.pdf</strong> — Relatório PDF/A-1/B assinado</li>
        <li><strong>chain.json</strong> — Linhagem JSON canónica de todos os HDRs</li>
        <li><strong>manifest_audit.sig</strong> — Assinatura Ed25519 do manifesto</li>
        <li><strong>integrity_hash</strong> — SHA-256 composto do pacote completo</li>
      </ul>

      <h2 id="hdr-valor-juridico">Valor jurídico esperado</h2>
      <Callout variant="warning" title="Nota legal">
        Este sistema fornece evidências técnicas robustas. A decisão final sobre
        valor probatório pertence ao tribunal, com base na lei processual aplicável,
        perícia oficial e conjunto probatório completo. A Heillon não substitui
        assessoria jurídica ou perícia forense certificada.
      </Callout>

      <p>
        O HDR Ledger foi concebido para satisfazer os requisitos de:
      </p>
      <ul>
        <li><strong>Brasil</strong> — Lei 11.419/2006 (processo eletrônico), MP 2.200-2/2001 (ICP-Brasil)</li>
        <li><strong>UE</strong> — eIDAS 2.0 Reg. 2024/1183 (QES, serviços de confiança)</li>
        <li><strong>EUA</strong> — FRE 707 (evidência computadorizada), ESIGN Act</li>
        <li><strong>EAU</strong> — UAE PDPL, UAE AI Charter, UAE PASS</li>
      </ul>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// GUIA LGPD
// ══════════════════════════════════════════════════════════════════════════════

export function BodyLgpd() {
  return (
    <>
      <Callout variant="info">
        O Heillon Legal implementa conformidade técnica LGPD (Fase 14).
        Este guia explica como cada funcionalidade mapeia para a Lei 13.709/2018.
      </Callout>

      <h2 id="lgpd-principios">Princípios LGPD e evidências técnicas</h2>

      <div className="my-5 overflow-x-auto rounded-xl border border-white/10">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-white/8 bg-white/[0.03] text-left text-[10px] uppercase tracking-wider text-white/50">
              <th className="px-4 py-3">Artigo</th>
              <th className="px-4 py-3">Princípio</th>
              <th className="px-4 py-3">Implementação Heillon</th>
            </tr>
          </thead>
          <tbody className="text-white/75">
            {[
              ["Art. 6º, I",    "Finalidade",     "Campos HDR de intenção + corpus normativo verificável"],
              ["Art. 6º, II-III","Adequação/Necessidade","Regras LGPD no corpus + contexto EASY"],
              ["Art. 6º, VI",   "Transparência",  "Portal verificação público + relatório de conformidade"],
              ["Art. 6º, VII",  "Segurança",      "Fernet, TLS, HttpOnly cookie, hash Ed25519"],
              ["Art. 6º, VIII", "Prevenção",      "Corpus normativo bloqueia missões não conformes"],
              ["Art. 6º, IX",   "Não discriminação","Missões auditáveis — decisões explicáveis por HDR"],
              ["Art. 18",       "Direitos do titular","Portal /privacy: exportação ZIP, DPO 15d SLA, incidentes ANPD 72h"],
            ].map(([art, prin, impl], i) => (
              <tr key={i} className="border-b border-white/6 hover:bg-white/[0.02]">
                <td className="px-4 py-3 font-mono text-gold-300/80">{art}</td>
                <td className="px-4 py-3 font-medium text-white/88">{prin}</td>
                <td className="px-4 py-3">{impl}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 id="lgpd-privacy-center">Centro de privacidade (/privacy)</h2>
      <p>
        A página <code>/privacy</code> implementa os direitos do titular (Art. 18) de forma técnica:
      </p>
      <ul>
        <li><strong>Consentimento granular</strong> — opt-in/opt-out por categoria de dados</li>
        <li><strong>RIPD automático</strong> — Relatório de Impacto à Proteção de Dados em PDF/A</li>
        <li><strong>DPO SLA 15 dias</strong> — canal direto com rastreamento de resposta</li>
        <li><strong>Portabilidade ZIP</strong> — exportação completa dos dados do titular</li>
        <li><strong>Incidentes ANPD</strong> — notificação em ≤72h conforme ANPD Res. 15/2024</li>
        <li><strong>Auto-eliminação imediata</strong> — Art. 18 VI: anonimiza dados pessoais e revoga chaves de API, preservando os HDRs já emitidos pelo valor probatório</li>
      </ul>

      <h2 id="lgpd-relatorio">Gerar relatório de conformidade LGPD</h2>
      <Steps>
        <Step n={1} title="Aceder a /normative">
          Clique na aba <strong>Normas</strong> na barra de navegação.
        </Step>
        <Step n={2} title="Inserir mission_id">
          Cole o identificador do caso a auditar.
        </Step>
        <Step n={3} title="Selecionar framework LGPD-BR">
          Escolha o framework <strong>LGPD-BR</strong> no seletor.
        </Step>
        <Step n={4} title="Gerar e exportar PDF">
          Clique em <strong>Gerar relatório</strong>.
          O sistema produz relatório com ancoragem constitucional + download PDF.
        </Step>
      </Steps>

      <Callout variant="warning">
        O controlador/responsável pelo tratamento de dados é sempre a entidade cliente.
        O Heillon Legal fornece os meios técnicos de suporte à prova — não substitui
        o papel do DPO ou a responsabilidade legal da organização.
      </Callout>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// ARQUITETURA DO SISTEMA
// ══════════════════════════════════════════════════════════════════════════════

export function BodyArchitecture() {
  return (
    <>
      <h2 id="arch-visao">Visão geral da arquitetura</h2>
      <p>
        O Heillon Legal é construído com <strong>Domain-Driven Design (DDD)</strong>,
        separando 20+ bounded contexts no backend FastAPI e o cockpit + área de conta no
        frontend Next.js 15. A captura de IA acontece por <strong>coletores</strong> (Extensão e
        Gateway) que escrevem no mesmo HDR Ledger.
      </p>

      <StatGrid>
        <StatCard value="20+" label="Domínios DDD" icon="🏛" />
        <StatCard value="FastAPI" label="Backend Python 3.12" icon="⚡" />
        <StatCard value="Next.js 15" label="Frontend App Router" icon="⚛" />
        <StatCard value="PostgreSQL" label="Base de dados principal" icon="🐘" />
      </StatGrid>

      <h2 id="arch-stack">Stack tecnológico</h2>

      <div className="my-5 overflow-x-auto rounded-xl border border-white/10">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-white/8 bg-white/[0.03] text-left text-[10px] uppercase tracking-wider text-white/50">
              <th className="px-4 py-3">Camada</th>
              <th className="px-4 py-3">Tecnologia</th>
              <th className="px-4 py-3">Propósito</th>
            </tr>
          </thead>
          <tbody className="text-white/75">
            {[
              ["Backend",      "Python 3.12, FastAPI, Pydantic v2", "API REST, lógica de domínio, HDR Ledger"],
              ["Base de dados","PostgreSQL 16 + SQLite (dev)",       "Persistência + migrações SQL incrementais"],
              ["Cache",        "Redis 7",                            "Rate limiting distribuído + fallback memória"],
              ["Frontend",     "Next.js 15 App Router",             "UI cockpit + PWA móvel + proxy cookie-aware"],
              ["UI",           "shadcn/ui, Tailwind CSS",           "Componentes, estilos, paleta gold"],
              ["Animação",     "Framer Motion",                     "Transições de página suaves"],
              ["3D",           "Three.js + @react-three/fiber",     "Hero 3D (frameloop=demand)"],
              ["PDF",          "ReportLab + pikepdf",               "PDF/A-1/B forense com XMP/ICP-Brasil"],
              ["Coletores",    "Extensão Chrome MV3 + Gateway",     "Captura passiva OpenAI/Anthropic + Anthropic Messages (SSE)"],
              ["Observability","Sentry + Postmark + /admin",        "Erros (PII off), e-mail transacional, métricas do beta"],
              ["Deploy",       "Vercel + Docker Compose + Caddy",   "UI edge-deployed + stack local + TLS automático"],
              ["CI/CD",        "GitHub Actions + Playwright",       "ruff, mypy, pytest, security scan + E2E smoke"],
            ].map(([layer, tech, purpose], i) => (
              <tr key={i} className="border-b border-white/6 hover:bg-white/[0.02]">
                <td className="px-4 py-3 font-medium text-white/88">{layer}</td>
                <td className="px-4 py-3 font-mono text-gold-300/80">{tech}</td>
                <td className="px-4 py-3">{purpose}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 id="arch-dominios">Domínios DDD (principais)</h2>
      <div className="my-5 grid gap-3 sm:grid-cols-2">
        {[
          { name: "HDR", desc: "Ledger criptográfico — SHA-256, RFC 3161, ICP-Brasil TSA" },
          { name: "Evidence", desc: "Ingestão WORM — PyMuPDF, python-docx, hashing" },
          { name: "Mission", desc: "OrchestrationEngine EASY — DAG, executores LLM/Stub" },
          { name: "Normative", desc: "Corpus FTS5 — validação pré-execução, 5+ frameworks" },
          { name: "Forensic", desc: "Pacotes forenses — PDF/A, chain.json, Ed25519" },
          { name: "User", desc: "Auth JWT HttpOnly, RBAC, multi-tenant" },
          { name: "Privacy", desc: "LGPD técnica — RIPD, DPO, portabilidade, ANPD" },
          { name: "Signatures", desc: "ICP-Brasil, eIDAS QES, ESIGN, UAE-PASS" },
          { name: "Governance", desc: "CNJ 615/2025, OAB, human approval gates" },
          { name: "EU AI Act", desc: "EU AI Act + GDPR + eIDAS 2.0 + ISO 27001" },
          { name: "USA", desc: "Colorado SB 205, CCPA, ABA Rules, NIST AI RMF" },
          { name: "UAE", desc: "UAE PDPL, DIFC, UAE AI Ethics, UAE PASS" },
          { name: "APAC", desc: "UK GDPR, Singapore PDPA, Australia Privacy Act, Canada C-27" },
          { name: "ISO 42001", desc: "AIMS completo — FRIA, Annex A controls" },
          { name: "Legal Evidence", desc: "FRE 707, citações, alucinações, competência OAB/ABA" },
          { name: "Malpractice", desc: "Insurance Score, Colorado SB 26-189, CCPA ADMT" },
          { name: "Mobile", desc: "Push tokens, PWA stats, rotas /m/*" },
          { name: "HDR ICP", desc: "TSA fallback: Certisign→Serpro→FreeTSA→stub" },
          { name: "Tier/Quota", desc: "Planos Free/Pro/Team/Enterprise, limite mensal, retenção, HTTP 402" },
          { name: "Gateway", desc: "Coletor #2 — proxy OpenAI + Anthropic Messages com auditoria HDR" },
          { name: "API Keys", desc: "Chaves heillon_live_… dos coletores, prefixo + last_used, revogação" },
        ].map(({ name, desc }) => (
          <div key={name} className="rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3">
            <span className="font-semibold text-gold-300">{name}</span>
            <p className="mt-0.5 text-[12px] text-white/60">{desc}</p>
          </div>
        ))}
      </div>

      <h2 id="arch-seguranca">Segurança em camadas</h2>
      <Steps>
        <Step n={1} title="Transporte">
          TLS em toda comunicação. Headers HTTP: <code>HSTS</code>, <code>CSP</code>,
          <code>X-Frame-Options</code>, <code>Referrer-Policy</code>, <code>Permissions-Policy</code>.
        </Step>
        <Step n={2} title="Autenticação">
          JWT em cookie <code>HttpOnly; Secure; SameSite=Lax</code>.
          Senha com bcrypt (custo 12). Proxy Next.js elimina CORS no frontend.
        </Step>
        <Step n={3} title="Autorização">
          RBAC por role (<code>advogado</code> / <code>admin</code>) + isolamento por
          <code>organization_id</code>. RLS PostgreSQL para isolamento a nível de base de dados.
        </Step>
        <Step n={4} title="Chaves de agentes">
          Fernet (AES-128-CBC + HMAC-SHA256) para chaves de API dos modelos LLM.
          Chave Fernet obrigatória em produção, distinta do JWT secret.
        </Step>
        <Step n={5} title="Rate limiting">
          Redis 7 distribuído + fallback em memória para dev. Limites configuráveis por rota.
        </Step>
        <Step n={6} title="Integridade dos dados">
          SHA-256 + RFC 3161 + encadeamento append-only. Stubs proibidos em produção.
        </Step>
      </Steps>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// COBERTURA REGULATÓRIA
// ══════════════════════════════════════════════════════════════════════════════

export function BodyRegulations() {
  const rows = [
    { flag: "🇧🇷", jurisdiction: "Brasil",         diplomas: "LGPD, Marco Civil, ANPD, ICP-Brasil, CNJ 615/2025, OAB",  status: "implemented" as const, phase: "14–16" },
    { flag: "🇪🇺", jurisdiction: "União Europeia",  diplomas: "EU AI Act 2024/1689, GDPR, eIDAS 2.0, ISO 27001",          status: "implemented" as const, phase: "17" },
    { flag: "🇺🇸", jurisdiction: "Estados Unidos",  diplomas: "Colorado SB 205, CCPA/CPRA, ABA Model Rules, NIST AI RMF", status: "implemented" as const, phase: "18" },
    { flag: "🇦🇪", jurisdiction: "EAU",             diplomas: "UAE PDPL Decreto 45/2021, DIFC, UAE AI Ethics, UAE PASS",  status: "implemented" as const, phase: "19" },
    { flag: "🇬🇧", jurisdiction: "Reino Unido",     diplomas: "UK GDPR, Data Protection Act, AI Code of Practice Regs",  status: "implemented" as const, phase: "20" },
    { flag: "🇸🇬", jurisdiction: "Singapura",       diplomas: "PDPA, Agentic AI Framework (jan/2026)",                   status: "implemented" as const, phase: "20" },
    { flag: "🇦🇺", jurisdiction: "Austrália",       diplomas: "Privacy Act 1988 (automated decisions, dez/2026)",        status: "implemented" as const, phase: "20" },
    { flag: "🇨🇦", jurisdiction: "Canadá",          diplomas: "PIPEDA + Bill C-27 (CPPA + AIDA), Quebec Law 25",         status: "implemented" as const, phase: "20" },
    { flag: "🏅", jurisdiction: "ISO 42001:2023",   diplomas: "AIMS completo — AI Management System",                   status: "implemented" as const, phase: "20" },
    { flag: "🏅", jurisdiction: "ISO 27001:2022",   diplomas: "ISMS — certificação completa",                           status: "planned" as const,     phase: "21" },
    { flag: "🏅", jurisdiction: "SOC 2 Type II",    diplomas: "Trust Services Criteria — enterprise EUA/global",        status: "planned" as const,     phase: "21" },
  ];

  return (
    <>
      <Callout variant="info">
        O Heillon Legal é a única plataforma de IA jurídica com cobertura regulatória
        certificada em <strong>7 jurisdições simultâneas</strong> + ISO 42001:2023.
      </Callout>

      <h2 id="reg-mapa">Mapa de conformidade global</h2>
      <RegTable rows={rows} />

      <h2 id="reg-brasil">🇧🇷 Brasil — Fase 14–16</h2>
      <p>
        O Brasil tem o regime mais exigente para o Heillon Legal dado o mercado primário.
        Cobertura inclui:
      </p>
      <ul>
        <li><strong>LGPD</strong> (Lei 13.709/2018) — todos os princípios, direitos do titular, DPO, RIPD</li>
        <li><strong>Marco Civil</strong> (Lei 12.965/2014) — guarda de logs, responsabilidade civil</li>
        <li><strong>ICP-Brasil</strong> (MP 2.200-2/2001) — assinaturas A1 CAdES-BES válidas em juízo</li>
        <li><strong>CNJ Res. 615/2025</strong> — uso de IA no Judiciário, aprovação humana obrigatória</li>
        <li><strong>OAB Rec. 001/2024</strong> — IA na advocacia, responsabilidade do advogado</li>
      </ul>

      <h2 id="reg-eu">🇪🇺 União Europeia — Fase 17</h2>
      <p>
        A UE tem as multas mais elevadas (€35M / 7% faturamento global para EU AI Act).
        Implementado:
      </p>
      <ul>
        <li><strong>EU AI Act</strong> Arts. 8–15 (sistemas de Alto Risco) + Annex IV tech docs</li>
        <li><strong>GDPR</strong> Arts. 5, 13-14, 22, 25 — transparência, DPIA, privacy by design</li>
        <li><strong>eIDAS 2.0</strong> — QES/PAdES-LTA/CAdES-LTA, EUDI Wallet ready</li>
        <li><strong>ISO 27001</strong> — ISMS risk register com score-based assessment</li>
      </ul>

      <h2 id="reg-iso42001">🏅 ISO 42001:2023 — Sistema Definitivo Global</h2>
      <p>
        O <strong>ISO 42001:2023 AIMS</strong> (AI Management System) é o primeiro padrão
        internacional de gestão de IA. O Heillon Legal implementa:
      </p>
      <ul>
        <li>FRIA — Fundamental Rights Impact Assessment (EU AI Act Art. 27)</li>
        <li>Todos os controles Annex A</li>
        <li>Heillon Global Compliance Score — 17 componentes, tiers bronze→platinum</li>
        <li>Malpractice Insurance Score — Colorado SB 26-189, CCPA ADMT</li>
      </ul>

      <Callout variant="tip" title="Score de conformidade">
        O <strong>Heillon Global Compliance Score</strong> agrega automaticamente
        a conformidade em 17 dimensões regulatórias e produz um tier
        (Bronze / Prata / Ouro / Platina) para cada organização.
      </Callout>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// GUIA DO PERITO
// ══════════════════════════════════════════════════════════════════════════════

export function BodyExpertGuide() {
  return (
    <>
      <Callout variant="info">
        Este guia é dirigido a peritos judiciais, auditores forenses e técnicos
        que precisam de apresentar evidências digitais em contexto judicial.
      </Callout>

      <h2 id="perito-workflow">Workflow pericial completo</h2>
      <FlowDiagram steps={[
        { icon: "📄", label: "Ingerir",   sub: "Evidência digital" },
        { icon: "🚀", label: "Missão",    sub: "Análise EASY" },
        { icon: "🔐", label: "HDR",       sub: "Registo imutável" },
        { icon: "📦", label: "Pacote",    sub: "PDF/A + chain.json" },
        { icon: "⚖️", label: "Tribunal",  sub: "Verificação pública" },
      ]} />

      <h2 id="perito-ingestao">1. Ingestão de material probatório</h2>
      <Steps>
        <Step n={1} title="Preservar hash antes de carregar">
          Antes de enviar qualquer ficheiro, calcule o SHA-256 localmente.
          Compare com o hash retornado pela plataforma para confirmar integridade de transmissão.
        </Step>
        <Step n={2} title="Documentar metadados de origem">
          No campo de descrição da ingestão, documente: origem do ficheiro,
          cadeia de custódia prévia (quem entregou, quando, como).
        </Step>
        <Step n={3} title="Guardar hdr_id de ingestão">
          O <code>hdr_id</code> de ingestão é a ancora criptográfica do material.
          Inclua-o no laudo técnico.
        </Step>
      </Steps>

      <Callout variant="warning" title="Integridade da cadeia">
        Nunca ingira versões modificadas ou comprimidas do material original.
        O hash deve corresponder ao ficheiro exato que constitui a prova.
        Qualquer pré-processamento quebra a cadeia de custódia.
      </Callout>

      <h2 id="perito-missao">2. Criação de missão pericial</h2>
      <p>
        A missão EASY documenta o processo analítico do perito de forma auditável.
        Cada passo do raciocínio pericial fica registado num HDR imutável.
      </p>
      <Steps>
        <Step n={1} title="Descrever o objeto da perícia">
          Exemplo: <em>"Perícia técnica em contrato digital — verificar autenticidade,
          integridade e conformidade com requisitos formais do processo nº XXX"</em>.
        </Step>
        <Step n={2} title="Indicar agentes especializados">
          Configure o modelo de IA adequado em <code>/agent-config</code>.
          Documente o modelo utilizado no laudo (exigência OAB Rec. 001/2024).
        </Step>
        <Step n={3} title="Aprovar explicitamente">
          A aprovação humana é o seu endosso técnico de que a análise é válida.
          Este ato fica registado com timestamp e identificador de operador.
        </Step>
      </Steps>

      <h2 id="perito-pacote">3. Exportação do pacote forense</h2>
      <p>
        Após a missão concluída, exporte o pacote forense completo:
      </p>
      <ul>
        <li><strong>executive_report.pdf</strong> — Relatório PDF/A-1/B (admissível como documento eletrônico)</li>
        <li><strong>chain.json</strong> — Linhagem JSON de toda a cadeia HDR</li>
        <li><strong>manifest_audit.sig</strong> — Assinatura Ed25519 do manifesto de integridade</li>
      </ul>
      <Callout variant="tip">
        Inclua no laudo a URL de verificação pública: qualquer perito contrário
        ou magistrado pode validar a cadeia sem instalar software adicional.
      </Callout>

      <h2 id="perito-verificacao">4. Verificação adversarial</h2>
      <p>
        Para verificação em contexto adversarial (quando a contraparte questiona a prova):
      </p>
      <Steps>
        <Step n={1} title="Fornecer hdr_id ao tribunal">
          O magistrado ou perito contrário pode verificar em <code>/verification</code>
          sem qualquer conta ou instalação.
        </Step>
        <Step n={2} title="Demonstrar encadeamento">
          O portal mostra visualmente toda a cadeia de HDRs — raiz → cauda,
          com timestamps RFC 3161 verificáveis externamente.
        </Step>
        <Step n={3} title="Validar assinatura ICP-Brasil">
          Use <code>GET /api/v1/verify/icp/{"{hdr_id}"}</code> para validação
          da assinatura CAdES-BES contra a cadeia de confiança ICP-Brasil.
        </Step>
      </Steps>

      <h2 id="perito-boas-praticas">5. Boas práticas periciais</h2>
      <ul>
        <li>Preserve cadeias sem ramificações não documentadas antes de audiências</li>
        <li>Documente o modelo de IA, versão e configuração utilizada no laudo</li>
        <li>Guarde o pacote forense completo fora da plataforma (backup institucional)</li>
        <li>Inclua sempre o disclaimer de que o HDR é evidência técnica — não substitui perícia judicial certificada</li>
        <li>Em casos de alta relevância, solicite validação de TSA independente da cadeia Certisign</li>
      </ul>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// GUIA DO ADMINISTRADOR
// ══════════════════════════════════════════════════════════════════════════════

export function BodyAdminGuide() {
  return (
    <>
      <Callout variant="danger" title="Guia de administrador">
        Este guia contém informações sensíveis de configuração de produção.
        Restrinja o acesso a operadores com role <code>admin</code>.
      </Callout>

      <h2 id="admin-variaveis">1. Variáveis de ambiente obrigatórias</h2>

      <div className="my-5 overflow-x-auto rounded-xl border border-white/10">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-white/8 bg-white/[0.03] text-left text-[10px] uppercase tracking-wider text-white/50">
              <th className="px-4 py-3">Variável</th>
              <th className="px-4 py-3">Obrigatória</th>
              <th className="px-4 py-3">Notas</th>
            </tr>
          </thead>
          <tbody className="text-white/75">
            {[
              ["AUTH_SECRET_KEY",          "✅ Sim", "≥32 chars, distinta do Fernet, não pode ser o default dev-insecure-*"],
              ["FERNET_ENCRYPTION_KEY",    "✅ Sim", "Base64 URL-safe 32 bytes. Protege chaves de API dos agentes."],
              ["POSTGRES_PASSWORD",        "✅ Sim", "Não pode ser 'changeme'. Use gerador de senhas fortes."],
              ["ENVIRONMENT",             "✅ Sim", "'production' — ativa todas as validações de segurança"],
              ["VERIFICATION_PUBLIC_BASE","✅ Sim", "URL pública da instância. Ex.: https://heillon-legal-ui.vercel.app"],
              ["FORCE_STUB_TIMESTAMP",    "❌ Não", "Deve ser 'false'. Nunca 'true' em produção."],
              ["TSA_PROVIDER",            "Opcional","certisign | serpro | freetsa (default: certisign)"],
              ["MISSION_ROUTES_REQUIRE_AUTH","Opcional","true — exigir JWT em todas as rotas de missão (recomendado)"],
              ["BILLING_WEBHOOK_SECRET",  "Opcional","HMAC-SHA256 do webhook de billing. Vazio = endpoint 503 (desativado). Defina em produção."],
              ["HEILLON_ADMIN_TOKEN",     "Opcional","Token dos endpoints /api/v1/admin/* (header X-Heillon-Admin-Token). ≥24 chars. Vazio = 503."],
              ["SENTRY_DSN",              "Opcional","Captura de erros (PII off). Vazio = SDK não inicializado. Recomendado em produção."],
              ["POSTMARK_SERVER_TOKEN",   "Opcional","E-mail transacional. Vazio = modo stub (apenas loga, não envia)."],
            ].map(([v, req, note], i) => (
              <tr key={i} className="border-b border-white/6 hover:bg-white/[0.02]">
                <td className="px-4 py-3 font-mono text-gold-300/80">{v}</td>
                <td className={`px-4 py-3 font-medium ${req.startsWith("✅") ? "text-emerald-400" : "text-white/50"}`}>{req}</td>
                <td className="px-4 py-3">{note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 id="admin-deploy">2. Deploy com Docker Compose</h2>
      <ScreenFrame title="Stack completa — docker-compose up">
        <pre className="text-[11px] text-emerald-300 overflow-x-auto">{`# Definir variáveis obrigatórias
$env:AUTH_SECRET_KEY    = "sua-chave-jwt-segura-min-32-caracteres"
$env:FERNET_ENCRYPTION_KEY = "sua-chave-fernet-base64-32-bytes"
$env:POSTGRES_PASSWORD  = "senha-postgres-forte"
$env:VERIFICATION_PUBLIC_BASE = "https://sua-instancia.com"

# Subir stack
docker compose up -d

# Verificar saúde
curl http://localhost:8000/health`}</pre>
      </ScreenFrame>

      <Callout variant="warning" title="Ordem de inicialização">
        O backend aguarda PostgreSQL e Redis saudáveis antes de iniciar
        (healthcheck no docker-compose). Aguarde ~30s na primeira inicialização.
      </Callout>

      <h2 id="admin-multi-tenant">3. Gestão multi-tenant</h2>
      <p>
        Cada organização tem um <code>organization_id</code> único. O isolamento
        é garantido em duas camadas:
      </p>
      <ul>
        <li><strong>Aplicação</strong> — todas as queries filtram por <code>organization_id</code></li>
        <li><strong>Base de dados</strong> — RLS (Row Level Security) no PostgreSQL/Supabase</li>
      </ul>
      <Steps>
        <Step n={1} title="Criar organização">
          O primeiro registo cria automaticamente a organização.
          Organizações adicionais requerem criação manual via admin.
        </Step>
        <Step n={2} title="Gerir utilizadores">
          Em <code>/health</code> (admin only), visualize e gerencie utilizadores da organização.
          Atribua roles: <code>advogado</code> (operador) ou <code>admin</code>.
        </Step>
      </Steps>

      <h2 id="admin-agentes">4. Configurar agentes de IA</h2>
      <Steps>
        <Step n={1} title="Aceder a /agent-config">
          Requer autenticação com role <code>admin</code>.
        </Step>
        <Step n={2} title="Adicionar executor">
          Escolha o tipo (Ollama / OpenAI / Anthropic / Custom) e forneça
          a API key. A chave é encriptada imediatamente com Fernet.
        </Step>
        <Step n={3} title="Testar conectividade">
          Use o botão <strong>Testar</strong> para verificar a ligação antes de associar ao tenant.
        </Step>
        <Step n={4} title="Associar à organização">
          O executor fica disponível para todas as missões do tenant após associação.
        </Step>
      </Steps>

      <h2 id="admin-corpus">5. Manutenção do corpus normativo</h2>
      <Callout variant="tip">
        O corpus normativo deve ser atualizado quando há novas regulamentações
        relevantes para o seu setor jurídico. O motor FTS5 indexa automaticamente
        novas regras inseridas via API.
      </Callout>
      <ApiBlock method="POST" path="/api/v1/normative/rules" description="Adicionar nova regra ao corpus normativo." auth />
      <ApiBlock method="GET" path="/api/v1/normative/search?q=lgpd" description="Pesquisa FTS5 no corpus." auth />

      <h2 id="admin-health">6. Health dashboard</h2>
      <p>
        A rota <code>/health</code> (admin only) mostra estado em tempo real:
        PostgreSQL, Redis, TSA provider, e métricas de utilização.
      </p>
      <ApiBlock method="GET" path="/health" description="Liveness check — retorna 200 quando todos os serviços OK." />
      <ApiBlock method="GET" path="/api/v1/health/detailed" description="Painel detalhado com estado de cada serviço." auth />

      <h2 id="admin-coletores">7. Coletores e quota</h2>
      <p>
        Os coletores (Extensão e Gateway) autenticam-se por chave de API e respeitam a quota do
        tier da organização. Não há configuração de servidor por coletor além da chave: o usuário
        gera a sua em <code>/conta/api-keys</code> e acompanha o consumo em <code>/conta/quota</code>.
      </p>
      <ul>
        <li><strong>Tiers:</strong> Free (50 HDRs/mês, retenção 30d), Pro/Team/Enterprise (ilimitado, retenção e usuários crescentes).</li>
        <li><strong>Excedente:</strong> ao esgotar a quota, os coletores recebem <code>HTTP 402</code> até a renovação do período.</li>
        <li><strong>Retenção:</strong> a purga por tier é executada pelo cron <code>scripts/cron_purge_retention.py</code>.</li>
      </ul>

      <h2 id="admin-billing">8. Webhook de billing (mudança de tier)</h2>
      <p>
        A contratação de planos vive no site institucional (fora do console). A mudança de tier
        chega ao backend por um webhook assinado com <code>BILLING_WEBHOOK_SECRET</code>
        (HMAC-SHA256 sobre o corpo bruto). Sem o segredo, o endpoint responde <code>503</code>.
      </p>
      <ApiBlock method="POST" path="/api/v1/billing/webhook" description="Eventos tier_changed / subscription_cancelled / payment_failed (HMAC obrigatório)." />

      <h2 id="admin-painel">9. Painel admin do beta</h2>
      <p>
        Os endpoints <code>/api/v1/admin/*</code> expõem métricas agregadas do beta (sem PII) e
        são protegidos pelo header <code>X-Heillon-Admin-Token</code> (valor de
        <code> HEILLON_ADMIN_TOKEN</code>, distinto do JWT e das chaves de API). Sem token
        configurado, retornam <code>503</code>.
      </p>

      <h2 id="admin-observability">10. Observabilidade e e-mail</h2>
      <ul>
        <li><strong>Sentry</strong> (<code>SENTRY_DSN</code>) — captura de erros com <code>send_default_pii=False</code>; vazio desativa o SDK.</li>
        <li><strong>Postmark</strong> (<code>POSTMARK_SERVER_TOKEN</code>) — e-mail transacional; vazio opera em modo stub (apenas loga).</li>
        <li><strong>Caddy</strong> — TLS automático no deploy via Docker Compose (Caddyfile).</li>
      </ul>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// FAQ
// ══════════════════════════════════════════════════════════════════════════════

export function BodyFAQ() {
  const faqs = [
    {
      section: "Peritos e forenses",
      items: [
        { q: "Como provo integridade anos depois?", a: "Guarde o pacote forense completo (PDF/A + chain.json + manifest.sig) fora da plataforma. O SHA-256 + carimbo RFC 3161 são verificáveis indefinidamente — o algoritmo não expira. Para garantia adicional, faça backup do chain.json num notário digital certificado." },
        { q: "O portal de verificação pública funciona sem conta?", a: "Sim — /verification e GET /api/v1/verify/{hdr_id} são totalmente públicos. Qualquer magistrado, perito contrário ou auditor pode verificar sem instalar nada, criar conta ou contactar a Heillon." },
        { q: "Posso usar o Heillon Legal para perícia em processos judiciais?", a: "O sistema fornece evidências técnicas robustas compatíveis com Lei 11.419/2006 (processo eletrônico) e MP 2.200-2/2001 (ICP-Brasil). A admissibilidade final depende do juiz e da lei processual aplicável. Recomendamos incluir o relatório forense como complemento a laudo de perito certificado pelo tribunal." },
        { q: "O que fazer se a cadeia HDR mostrar ramificação não esperada?", a: "Ramificações (fork) da cadeia são detetadas automaticamente no portal de verificação e aparecem com indicador visual. Documente o fork no laudo explicando o contexto (missões paralelas legítimas). Se suspeitar de adulteração, contacte o administrador e preserve todos os artefactos sem modificação." },
      ],
    },
    {
      section: "Advogados",
      items: [
        { q: "O portal público vale como prova sozinha?", a: "Funciona como reforço tecnológico — evidência técnica de que a IA agiu de determinada forma num determinado momento. Para valor probatório máximo, combine com laudo de perito judicial, a cadeia ICP-Brasil e o relatório de conformidade normativa." },
        { q: "Como citar a plataforma num processo?", a: "Cite: 'Registo HDR [hdr_id] gerado pela plataforma Heillon Legal (hdr.heillon.com), verificável publicamente em /api/v1/verify/[hdr_id], com carimbo temporal ICP-Brasil RFC 3161 emitido em [timestamp].' Anexe o relatório PDF/A exportado." },
        { q: "Posso usar o sistema sem configurar agentes de IA?", a: "Sim. Para ingestão de evidências e geração de HDRs de custódia, não é necessário configurar modelos de IA. Os executores são necessários apenas para missões EASY de análise automatizada." },
        { q: "A plataforma está em conformidade com a OAB Rec. 001/2024?", a: "Sim. O sistema implementa os requisitos da OAB Rec. 001/2024: identificação do modelo usado, aprovação humana obrigatória antes da execução, auditabilidade de todas as decisões IA e responsabilidade do advogado documentada." },
      ],
    },
    {
      section: "Magistrados e auditores",
      items: [
        { q: "Como validar um HDR sem login?", a: "Aceda a heillon-legal-ui.vercel.app/verification, cole o hdr_id e clique Verificar. Ou use diretamente: GET https://[instância]/api/v1/verify/[hdr_id]. Não requer conta." },
        { q: "O carimbo temporal tem validade jurídica no Brasil?", a: "Sim — quando TSA_PROVIDER está configurado como Certisign ou Serpro (ambas ACs ICP-Brasil), o carimbo RFC 3161 tem validade jurídica conforme MP 2.200-2/2001 e Lei 11.419/2006. Carimbos FreeTSA têm validade técnica mas não são ACs ICP-Brasil." },
        { q: "Posso solicitar a linhagem completa de uma missão?", a: "Sim. O pacote forense inclui chain.json com a linhagem JSON canónica de todos os HDRs da missão, verificável pela assinatura Ed25519 do manifesto." },
      ],
    },
    {
      section: "Administradores técnicos",
      items: [
        { q: "Como migrar de SQLite para PostgreSQL?", a: "Defina DATABASE_TYPE=postgresql e configure as variáveis POSTGRES_*. Execute as migrações: uvicorn inicia e aplica migrations/00N_*.sql automaticamente. Para migrar dados existentes, use o script de exportação em scripts/ ou faça backup SQLite antes." },
        { q: "O rate limiting funciona sem Redis?", a: "Sim — há fallback automático para rate limiting em memória. Porém, em múltiplas instâncias, cada instância tem contador independente. Para produção multi-instância, Redis é obrigatório." },
        { q: "Como configurar o carimbo ICP-Brasil Certisign?", a: "Defina TSA_PROVIDER=certisign (default). O sistema usa https://timestamp.certisign.com.br/. Não requer credenciais adicionais. Para Serpro, defina TSA_PROVIDER=serpro." },
        { q: "Como rodar os testes?", a: "cd backend && python -m pytest -q. A suíte usa SQLite em memória — não requer PostgreSQL ou Redis externos. Para E2E: ver docs/E2E-CI.md." },
      ],
    },
    {
      section: "Coletores, conta e quota",
      items: [
        { q: "Qual a diferença entre a Extensão e o Gateway?", a: "São os dois coletores. A Extensão do Browser (Chrome MV3) captura passivamente o uso de ChatGPT/Claude/Gemini na interface web. O Gateway MCP/API é um proxy compatível com OpenAI e Anthropic: você aponta o seu SDK para ele e cada chamada de API vira um HDR. Pode usar ambos com a mesma chave." },
        { q: "Onde gero e revogo minha chave de API?", a: "Em /conta/api-keys. A chave (formato heillon_live_…) é mostrada em texto puro uma única vez, na criação — copie-a na hora. Depois ficam visíveis apenas o prefixo e a data de último uso. Revogar é imediato e não afeta os HDRs já emitidos." },
        { q: "O que acontece quando atinjo o limite do plano?", a: "Ao esgotar a quota do período (no plano Free, 50 HDRs/mês), os coletores recebem HTTP 402 e param de registrar até a renovação ou o upgrade. Acompanhe o consumo em /conta/quota. A contratação de planos é feita no site institucional." },
        { q: "Se eu eliminar minha conta, perco os HDRs?", a: "Não. A auto-eliminação (LGPD Art. 18 VI) anonimiza seus dados pessoais e revoga as chaves de API, mas preserva os HDRs já emitidos — pela integridade da cadeia e pelo valor probatório." },
      ],
    },
  ];

  return (
    <>
      {faqs.map((section) => (
        <section key={section.section}>
          <h2 id={`faq-${section.section.toLowerCase().replace(/\s+/g, "-")}`}>{section.section}</h2>
          <div className="space-y-4">
            {section.items.map((item, i) => (
              <div key={i} className="rounded-xl border border-white/8 bg-white/[0.02] px-5 py-4">
                <p className="font-semibold text-white/92">❓ {item.q}</p>
                <p className="mt-2 text-[13px] leading-relaxed text-white/68">{item.a}</p>
              </div>
            ))}
          </div>
        </section>
      ))}
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// CHANGELOG
// ══════════════════════════════════════════════════════════════════════════════

export function BodyChangelog() {
  const phases = [
    { phase: "Beta Privado (F30)", date: "Mai 2026", badge: "gold" as const, items: ["Production-Ready Sprint para beta privado de advogados", "Deploy: Docker Compose + Caddy (TLS automático) + backup PostgreSQL + bootstrap", "Compliance LGPD: Centro de Privacidade, Termos, banner de cookies, auto-eliminação de conta (preserva HDRs)", "Observabilidade: Sentry (PII off), e-mail Postmark, painel admin /admin (métricas sem PII)", "Console: card de quota no dashboard, nudge de onboarding, banner conta_eliminada no login", "Hardening de estados de UX (loading/erro/vazio)", "Copy: RFC 3161 como selo ativo; ICP-Brasil qualificado posicionado como roadmap"] },
    { phase: "Coletor #2 — Gateway (F31)", date: "Mai 2026", badge: "green" as const, items: ["Gateway MCP/API: proxy drop-in compatível com OpenAI Chat Completions", "Auditoria HDR por chamada + headers de quota (hdr_id, quota usada/limite/tier)", "Streaming SSE", "Compatibilidade com Anthropic Messages (/gateway/anthropic/v1/messages)"] },
    { phase: "Coletor #1 — Extensão (F28)", date: "Mai 2026", badge: "green" as const, items: ["Extensão do Browser (Chrome MV3, PoC) para ChatGPT/Claude/Gemini", "Captura passiva pergunta→resposta → HDR em background", "Endpoints /extension/health (valida chave+quota) e /extension/capture", "Chave de API em chrome.storage.local (nunca sincronizada)"] },
    { phase: "Conta & Quota (F26–F27)", date: "Abr 2026", badge: "green" as const, items: ["Tier & Quota Foundation: planos Free/Pro/Team/Enterprise", "Limite mensal de HDRs, retenção por tier, HTTP 402 ao exceder", "Webhook de billing assinado (HMAC) — precificação no site institucional", "Console: quota visível + onboarding em 3 passos (boas-vindas → chave → coletor)", "Chaves de API heillon_live_… (criação, listagem, revogação)"] },
    { phase: "Hardening & UX (F22–F24)", date: "Mar 2026", badge: "blue" as const, items: ["Auditorias de UX, segurança, backend e frontend (personas + probes)", "Backend/Frontend hardening + gates de CI (a11y/SEO)", "UX Renaming: vernáculo jurídico BR (Casos, Normas, Modelos de IA, Conta)", "Migração python-jose → PyJWT", "Multi-key Fernet com rotação", "Corpus normativo BR expandido"] },
    { phase: "Corpus & CI/CD (F21)", date: "Fev 2026", badge: "blue" as const, items: ["Corpus normativo real: 9 jurisdições, 50+ regras (corpus_seed.py)", "CI/CD: ruff, mypy, testes PostgreSQL, security scan, corpus verify", "deploy.yml — Vercel (frontend) + Docker (backend)"] },
    { phase: "Fase 20", date: "Mai 2026", badge: "gray" as const, items: ["ISO 42001:2023 AIMS completo", "FRIA (EU AI Act Art. 27)", "Legal Evidence FRE 707 + citações + alucinações", "APAC: UK GDPR + Singapore PDPA + Australia Privacy + Canada C-27", "Malpractice Insurance Score + Colorado SB 26-189", "Heillon Global Compliance Score (17 componentes, tiers bronze→platinum)", "65 novos testes (total: 272)"] },
    { phase: "Fase 19", date: "Abr 2026", badge: "green" as const, items: ["UAE PDPL Decreto-Lei 45/2021", "DIFC Data Protection Law + ADGM", "UAE AI Ethics 7 princípios", "UAE AI Seal + Dubai contratos governamentais", "UAE PASS (QES/AES)", "18 testes"] },
    { phase: "Fase 18", date: "Mar 2026", badge: "green" as const, items: ["Colorado AI Act SB 205 (vigente jun/2026)", "CCPA/CPRA + California SB 53", "ABA Formal Opinion 512 (Rules 1.1/1.6/5.3)", "NIST AI RMF 1.0 (GOVERN/MAP/MEASURE/MANAGE)", "ESIGN audit trail", "18 testes"] },
    { phase: "Fase Sig", date: "Fev 2026", badge: "green" as const, items: ["Assinaturas digitais universais", "ICP-Brasil CAdES-BES / eIDAS QES / PAdES-LTA / CAdES-LTA", "ESIGN + UAE-PASS", "Lifecycle: envio→entrega→recebimento→assinatura", "Acks com hash de integridade, revogação admin"] },
    { phase: "Fase 17", date: "Jan 2026", badge: "green" as const, items: ["EU AI Act 2024/1689 (Alto Risco) + Annex IV", "DPIA automático (GDPR + LGPD)", "QES/PAdES-LTA/CAdES-LTA", "ISO 27001 ISMS risk register (score-based)", "21 testes"] },
    { phase: "Fase 16", date: "Dez 2025", badge: "blue" as const, items: ["CNJ Res. 615/2025 — IA no Judiciário", "OAB Rec. 001/2024 — IA na advocacia", "Classificação de risco (low/medium/high/prohibited)", "Human approval gates + AI decision audit log", "OAB disclosure lifecycle", "23 testes"] },
    { phase: "Fases 14–15", date: "Nov 2025", badge: "blue" as const, items: ["LGPD técnica completa: RIPD PDF/A, DPO 15d SLA, portabilidade ZIP", "ICP-Brasil A1 PKCS#12 + CAdES-BES + PDF/A-3 + AF chains.json", "GET /verify/icp/{hdr_id}", "Página /privacy + ANPD 72h", "27 testes"] },
    { phase: "Fase 13", date: "Out 2025", badge: "gray" as const, items: ["ICP-Brasil TSA (Certisign→Serpro→FreeTSA)", "Headers CSP/HSTS/XFO/Referrer-Policy", "Logging JSON estruturado", "Proxy Route Handler cookie-aware", "PyMuPDF + FTS5 normativo", "Página de conformidade LGPD + PDF"] },
    { phase: "Fases 1–12", date: "2024–2025", badge: "gray" as const, items: ["HDR Ledger SHA-256 + RFC 3161", "DDD completo: HDR, Evidence, Mission, Normative, Forensic, User", "Frontend Next.js 15 + PWA móvel", "PostgreSQL + Redis + Docker Compose", "JWT HttpOnly + rate limit + RLS", "E2E CI Playwright", "Health dashboard"] },
  ];

  return (
    <>
      <h2 id="cl-resumo">Estado atual: Beta Privado — Substrato de coletores</h2>
      <StatGrid>
        <StatCard value="2" label="Coletores (Extensão + Gateway)" icon="🛰" />
        <StatCard value="4" label="Planos (Free→Enterprise)" icon="🎟" />
        <StatCard value="20+" label="Domínios DDD" icon="🏛" />
        <StatCard value="9" label="Jurisdições no corpus" icon="🌍" />
      </StatGrid>

      <div className="mt-6 space-y-5">
        {phases.map((p) => (
          <div key={p.phase} className="rounded-xl border border-white/8 bg-white/[0.02] px-5 py-4">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="font-bold text-white/92">{p.phase}</span>
              <Badge variant={p.badge}>{p.date}</Badge>
            </div>
            <ul className="space-y-1 text-[12px] text-white/68">
              {p.items.map((item, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="mt-0.5 text-gold-400/60" aria-hidden>·</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <Callout variant="info" title="Próximo">
        Beta privado com advogados convidados → lançamento público na Chrome Web Store.
        Na sequência (pós-CNPJ): selo ICP-Brasil qualificado (Serpro/Certisign, certificado A1),
        precificação e certificações (ISO 27001, SOC 2 Type II).
      </Callout>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// TERMOS DE USO (mantido para compatibilidade)
// ══════════════════════════════════════════════════════════════════════════════

export function BodyTerms() {
  return (
    <>
      <h2 id="aceitacao">Aceitação e âmbito</h2>
      <p>
        Ao usar o Heillon Legal, concorda com estes Termos relativos ao software
        fornecido no contexto institucional acordado. O uso implica conformidade
        com LGPD, Marco Civil e regulamentações aplicáveis à sua jurisdição.
      </p>
      <h2 id="responsabilidade">Limitação de responsabilidade</h2>
      <p>
        Serviços entregues conforme disponibilidade. SLAs formais requerem contrato enterprise escrito.
        O Heillon Legal fornece meios técnicos de suporte à prova — não substitui assessoria jurídica.
      </p>
      <h2 id="uso-permitido">Uso permitido · Proibições</h2>
      <ul>
        <li>Proibido: violar segredos de justiça, normas AML/CFT, ou tratar dados sem base legal válida</li>
        <li>Proibido: remover disclaimers obrigatórios de relatórios oficiais</li>
        <li>Proibido: usar stubs de timestamp (<code>FORCE_STUB_TIMESTAMP=true</code>) em produção com clientes reais</li>
      </ul>
      <h2 id="lei-aplicavel">Lei aplicável</h2>
      <p>
        Interpretação primária pela ordem jurídica brasileira.
        Contratos enterprise podem variar país/foro mediante escrito assinado.
      </p>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// POLÍTICA DE PRIVACIDADE (mantido para compatibilidade)
// ══════════════════════════════════════════════════════════════════════════════

export function BodyPrivacy() {
  return (
    <>
      <h2 id="categorias">Dados tratados</h2>
      <ul>
        <li>Credenciais: email (bcrypt), role, organization_id</li>
        <li>Metadados de casos, HDR payloads, logs de execução e de captura dos coletores</li>
        <li>Chaves de agentes encriptadas com Fernet (nunca em plaintext)</li>
        <li>Chaves de API dos coletores: apenas hash e prefixo (o texto puro é exibido uma única vez)</li>
        <li>Logs de infraestrutura retidos conforme política de hosting e tier da organização</li>
      </ul>
      <Callout variant="info">
        A <strong>auto-eliminação de conta</strong> (<code>/privacy</code>) anonimiza os dados
        pessoais e revoga as chaves, mas preserva os HDRs já emitidos — pela integridade da
        cadeia e pelo valor probatório.
      </Callout>
      <h2 id="bases">Bases legais de tratamento</h2>
      <p>
        Execução de contrato, obrigações legais (LGPD Art. 7º) e legítimo interesse documentado.
        Controlador/responsável: a entidade cliente.
      </p>
      <h2 id="direitos">Direitos do titular</h2>
      <p>
        Acesse <a href="/privacy" className="text-gold-300 underline">/privacy</a> para
        exercer direitos LGPD Art. 18: acesso, retificação, portabilidade, eliminação e revogação de consentimento.
      </p>
      <Callout variant="info">
        Para DPIA institucional em decisões automatizadas de alto impacto,
        consulte o DPO da sua organização — o escopo excede o SaaS da plataforma.
      </Callout>
    </>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
// GUIA DE CONFORMIDADE (mantido + atualizado)
// ══════════════════════════════════════════════════════════════════════════════

export function BodyComplianceGuide() {
  return (
    <>
      <Callout variant="tip">
        Para a cobertura regulatória completa, consulte o
        <a href="/docs/regulations" className="text-gold-300 underline ml-1">Mapa regulatório global</a>.
      </Callout>

      <h2 id="comp-visao">Visão geral de conformidade</h2>
      <p>
        O Heillon Legal cobre 7 jurisdições regulatórias + ISO 42001:2023 AIMS.
        O <strong>Heillon Global Compliance Score</strong> agrega automaticamente
        a conformidade em 17 dimensões e produz um tier: Bronze / Prata / Ouro / Platina.
      </p>

      <div className="my-5 overflow-x-auto rounded-xl border border-white/10">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-white/8 bg-white/[0.03] text-left text-[10px] uppercase tracking-wider text-white/50">
              <th className="px-4 py-3">Framework</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Fase</th>
            </tr>
          </thead>
          <tbody className="text-white/75">
            {[
              ["LGPD + Marco Civil + ANPD",  "✅ Implementado", "14"],
              ["ICP-Brasil A1 (CAdES-BES)",  "✅ Implementado", "15"],
              ["CNJ 615/2025 + OAB",         "✅ Implementado", "16"],
              ["EU AI Act + GDPR + eIDAS 2.0","✅ Implementado", "17"],
              ["Colorado SB 205 + CCPA + ABA","✅ Implementado", "18"],
              ["UAE PDPL + DIFC + UAE PASS", "✅ Implementado", "19"],
              ["APAC (UK+SG+AU+CA)",          "✅ Implementado", "20"],
              ["ISO 42001:2023 AIMS",         "✅ Implementado", "20"],
              ["ISO 27001:2022 ISMS",         "🟢 Fase 21",      "21"],
              ["SOC 2 Type II",               "🟢 Fase 21",      "21"],
            ].map(([fw, st, ph], i) => (
              <tr key={i} className="border-b border-white/6 hover:bg-white/[0.02]">
                <td className="px-4 py-3 font-medium text-white/88">{fw}</td>
                <td className={`px-4 py-3 font-medium ${st.startsWith("✅") ? "text-emerald-400" : "text-blue-400"}`}>{st}</td>
                <td className="px-4 py-3 text-white/50">{ph}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 id="comp-gerar">Gerar relatório de conformidade</h2>
      <Steps>
        <Step n={1} title="Aceder a /normative">Navegar para a aba Normas.</Step>
        <Step n={2} title="Inserir mission_id">Cole o ID do caso a auditar.</Step>
        <Step n={3} title="Escolher framework">Selecione LGPD-BR, EU AI Act, ISO 42001, etc.</Step>
        <Step n={4} title="Exportar PDF">O relatório inclui ancoragem constitucional e download PDF.</Step>
      </Steps>
    </>
  );
}
