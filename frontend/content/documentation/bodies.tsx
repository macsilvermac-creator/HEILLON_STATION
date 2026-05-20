/**
 * Textos institucionais da Central de Documentação (PT-BR) — MVP Heillon Legal.
 * Não substituem parecer jurídico formal; integram onboarding e compliance técnico.
 */

export function BodyManualUsage() {
  return (
    <>
      <h2 id="introducao">Introdução</h2>
      <p>
        Este manual cobre os fluxos essenciais do cockpit web Heillon Legal: conta de operador jurídico, planeamento EASY,
        ingestão segura de evidências, diário das missões, verificação criptográfica e exportação para pacotes forenses / PDF
        executivo onde disponível na sua instância.
      </p>

      <h2 id="conta">1. Registo e autenticação</h2>
      <ol>
        <li>
          Aceda a <strong>Registo</strong> ou <strong>Entrar</strong> na barra superior. O cockpit associa todas as operações ao
          vosso <code className="inline">organization_id</code>.
        </li>
        <li>
          O token actual permanece armazenado no <strong>localStorage</strong> do navegador (MVP); em produções sensíveis
          recomende-se migração para cookies HTTP-only atrás da mesma origem ou reverse proxy segregado — ver{" "}
          <em>Política de Privacidade</em> e infra da vossa casa.
        </li>
      </ol>

      <h2 id="missao">2. Ciclo de vida das missões EASY</h2>
      <h3 id="planeamento">2.1 Planeamento</h3>
      <p>No ecrã <strong>Missão</strong>, descreva a intenção em linguagem natural e indique explicitamente os agentes autorizados.</p>
      <blockquote>
        O <strong>Corpus Normativo</strong> avalia a intenção antes de qualquer execução. Missões marcadas como bloqueadas
        exigem reconfiguração (ex.: remover menções proibidas, acrescentar aprovação humana, ou declarar bases legais).
      </blockquote>
      <h3 id="aprovacao">2.2 Aprovação humana</h3>
      <p>
        Estados <strong>pending</strong> aguardam a acção jurídica <em>Approve</em> antes de minerar HDRs de execução. Em organizações com
        <code className="inline">MISSION_ROUTES_REQUIRE_AUTH=true</code> apenas operadores válidos dentro do tenant conseguem
        continuar — impede leituras cruzadas.
      </p>
      <h3 id="execucao">2.3 Execução</h3>
      <p>
        Após aprovação, o motor EASY invoca cada passo registado sob normas declaradas. Todas as saídas alimentam a geração de{" "}
        <strong>HDR</strong>s imutáveis com carimbos configurados segundo a política temporal da instância.
      </p>

      <h2 id="ingestao-evidencias">3. Evidências e ingestão</h2>
      <p>
        A rota <strong>Evidências</strong> permite carregar artefactos que produzem registos HDR de ingestão ligados ao vosso
        tenant e, opcionalmente, a uma missão já existente. O campo{" "}
        <code className="inline">previous_hdr</code> só é aceite quando o HDR anterior também pertencer à mesma organização —
        mitiga ataques à cadeia de custódia.
      </p>

      <h2 id="verificacao">4. Portal de verificação pública</h2>
      <p>
        Abra <strong>Verificar</strong> para validar hashes e correntes com ou sem conta. Esta área permite partilhar ligações
        verificáveis com magistrados, contrapartes e auditores externos — consulte igualmente{" "}
        <em>/m/verify</em> para leituras em dispositivo móvel.
      </p>

      <h2 id="forense-normativo">5. Pacotes forenses e hub normativo</h2>
      <p>Gere artefactos resumo após execuções concluídas e utilize <strong>Normativo</strong> para relatórios de conformidade contra frameworks activos.</p>

      <h2 id="avisos-legais-docs">Disclaimer</h2>
      <blockquote>A Heillon MVP não substitui assessoria jurídica; apenas documenta comportamento técnico observável pela plataforma.</blockquote>
    </>
  );
}

export function BodyChainCustody() {
  return (
    <>
      <h2 id="o-que-e-hdr">O que é um HDR?</h2>
      <p>
        O <strong>Heillon Decision Record (HDR)</strong> é uma estrutura criptográfica fechada que descreve, passo-a-passo, ocorrências
        relevantes dentro de uma missão EASY: agente utilizado, intenções, resultado normativo aplicado ao momento, fingerprints de entrada
        / saída e metadados de tempo.
      </p>

      <h2 id="integridade-hash">Porque SHA-256?</h2>
      <p>
        Cada payload canónico obtém uma impressão única através de <strong>SHA-256</strong>. Qualquer alteração posterior nos bytes
        arquivados produz diferentes digests quando re-hashed — permite detetar adulterações forensicamente perceptíveis, condição
        básica adotada também em relatórios oficiais de integridade electrónica.
      </p>

      <h2 id="timestamp-rfc3161">Carimbos RFC 3161</h2>
      <p>
        A instância pode emitir solicit <code className="inline">TimeStampToken</code> emitidos conforme RFC 3161 (ou derivados de
        infraestrutura equivalente quando configurada). Em ambientes onde <strong>FORCE_STUB_TIMESTAMP</strong> está desactivado —
        sempre em produções responsáveis — o carimbo reforça a prova temporal para litígios. Quando stubs estão activados (
        apenas laboratório), aparece banner explícito e o comportamento deve ser tratado como <em>não juridicamente vinculante</em>.
      </p>

      <h2 id="encadeamento">Encadeamento append-only</h2>
      <ul>
        <li>Cada ingestão opcionalmente referencia o campo <code className="inline">previous_hdr</code> apontando para o digest anterior.</li>
        <li>RAMOs paralelos dentro da mesma missão marcados na verificação automática são sinal visual de fork intencional.</li>
      </ul>

      <h2 id="verificacao-tecnica">Verificação pública</h2>
      <ol>
        <li>Escolha o identificador de missão ou cole o HDR no portal.</li>
        <li>Compare o digest mostrado com o emitido pela vossa infraestrutura interna quando necessário para dupla conferência.</li>
        <li>Descarregue o pacote forensic/PDF apenas após garantir permissões relativas aos dados tratados.</li>
      </ol>

      <h2 id="valor-juridico">Valor jurídico esperado</h2>
      <blockquote cite="Lei 13.709/2018 · Artigos complementares infra">
        Esta descrição explica apenas o comportamento tecnológico. A decisão judicial final sobre valor probante depende de conjunto
        probatório, perícia oficial e lei processual aplicável.
      </blockquote>
    </>
  );
}

export function BodyLgpd() {
  return (
    <>
      <h2 id="contexto-legal-lgpd">Quadro normativo · Lei 13.709/2018</h2>
      <p>A LGPD regula tratamentos efectuados sobre dados pessoais no Brasil.</p>

      <h2 id="principios-vs-plataforma">Princípios e evidências dentro da Heillon</h2>
      <table>
        <thead>
          <tr>
            <th>Art. referência</th>
            <th>Princípio</th>
            <th>Evidências técnicas</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Finalidade · Art. 6º, I</td>
            <td>Declarar porque se processa dados</td>
            <td>Campos HDR de intento + normativo verificável</td>
          </tr>
          <tr>
            <td>Adequação / Necessidade · II &amp; III</td>
            <td>Garantir mínimos necessários</td>
            <td>Regras LGPD corpus + contexto EASY</td>
          </tr>
          <tr>
            <td>Transparência · VI</td>
            <td>Uso compreensível e auditável</td>
            <td>Portal de verificação e relatório de conformidade</td>
          </tr>
          <tr>
            <td>Segurança · VII</td>
            <td>Evitar incidentes/acessos não autorizados</td>
            <td>Fernet para segredos, TLS na borda org, hashing Ed25519</td>
          </tr>
          <tr>
            <td>Prevenção · VIII</td>
            <td>Detectar tratamentos antes de executá-los maliciosamente</td>
            <td>Corpus normativo EASY que bloqueia/realinhamentos</td>
          </tr>
        </tbody>
      </table>

      <h2 id="relatorios-compliance">Relatório de conformidade</h2>
      <ol>
        <li>Finalize missões HDR com integridade válida na instância.</li>
        <li>Aceda a <strong>/normative</strong> no cockpit autenticado.</li>
        <li>Inserir mission_id válido sob o vosso tenant e gerar relatório contra <strong>LGPD-BR</strong>.</li>
        <li>Guarde também o pacote forensic como anexo institucional se necessário processualmente.</li>
      </ol>

      <h2 id="titular-direitos">Direitos do titular · Art. 18</h2>
      <p>O MVP expõe mecanismos técnicos (exportação/consulta quando implementados pela vossa org). Operacionalmente,</p>
      <ul>
        <li>Designe canal humano oficial para solicitações (email certificado).</li>
        <li>Relacione os pedidos a missões HDR relevantes usando identificadores de missão/arquivo.</li>
      </ul>
      <blockquote>Controlador/responsável do tratamento continua sendo a entidade cliente — a Heillon fornece meios técnicos de suporte à prova.</blockquote>
    </>
  );
}

export function BodyTerms() {
  return (
    <>
      <h2 id="aceitacao">Aceitação e âmbito</h2>
      <p>Use a plataforma apenas se concordar com estes Termos relativos ao software Heillon MVP fornecido no contexto institucional acordado.</p>
      <h2 id="responsabilidade">Limitação de Responsabilidade</h2>
      <p>
        Serviços entregues &quot;tal como estão&quot;; não garantimos continuidade 24×7 antes de SLA contratuais escritos nem resultados jurídicos.
      </p>
      <h2 id="uso-permitido">Uso Permitido · Proibições</h2>
      <ul>
        <li>Violar segredos de justiça, normas AML/CFT pertinentes ao sector ou tratamentos dados sem base legal válida declarada pela entidade cliente.</li>
        <li>Remover disclaimers obrigatórios em relatórios oficiais.</li>
      </ul>
      <h2 id="lei-aplicavel">Lei aplicável</h2>
      <blockquote>Interpretação inicialmente orientada para ordem jurídica brasileira; contratos enterprise podem variar país de foro sob escrito próprio.</blockquote>
    </>
  );
}

export function BodyPrivacy() {
  return (
    <>
      <h2 id="categorias">Dados tratados</h2>
      <ul>
        <li>Credenciais (email bcrypt, roles, organization_id).</li>
        <li>Metadados de missões, HDR payloads, segredos de agentes quando configurados sob Fernet próprio ao tenant.</li>
        <li>Logs infra mantidos segundo política própria de hosting.</li>
      </ul>
      <h2 id="bases">Fundamentos típicos de tratamento MVP</h2>
      <p>Bases legais escolhidas pela entidade (execução de contratos, obrigações legais, legítimo interesse documentado).</p>
      <h2 id="direitos">Direitos e contacto LGPD interno da entidade</h2>
      <p>Forneça e-mail institucional de DPO/controlador aos operadores antes de entrada em produção real.</p>
      <blockquote>Encorajamos DPIA institucional separado sempre que há decisões unicamente automatizadas com alto impacto — excede escopo SaaS MVP puro.</blockquote>
    </>
  );
}

export function BodyComplianceGuide() {
  return (
    <>
      <h2 id="visao-compliance">Visionamento</h2>
      <p>Use o relatório automatizado apenas como primeira camada técnico-jurídica de conforto antes de relatórios lega-assistidos externos.</p>
      <table>
        <thead>
          <tr>
            <th>Quadro futuro/near</th>
            <th>Estado atual</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>LGPD</td>
            <td>Implementado primeira âncora (LGPD-BR)</td>
          </tr>
          <tr>
            <td>EU AI Act</td>
            <td>Patterns prontos p/ extensões via mesmos registos/frameworks</td>
          </tr>
          <tr>
            <td>ISO/IEC 42001</td>
            <td>Placeholder — alinhar requisitos AIMS com relatórios anexados</td>
          </tr>
        </tbody>
      </table>
    </>
  );
}

export function BodyExpertGuide() {
  return (
    <>
      <h2 id="perito-visao">Visão especializada pericial</h2>
      <p>Use ingestão sempre com metadatos explicativos suficientes e guarde relatórios de conformidade lado-a-lado com laudos externos.</p>
      <ul>
        <li>Preserve cadeias sem ramificações paralelas antes de audiências onde integridade será questionada adversarialmente.</li>
        <li>Documente método de hashing e infra de carimbo no corpo textual do relatório tribunal.</li>
      </ul>
    </>
  );
}

export function BodyAdminGuide() {
  return (
    <>
      <h2 id="tenant">Multi-tenant e segredos</h2>
      <p>Inicialize sempre <strong>MISSION_ROUTES_REQUIRE_AUTH=true</strong> antes de onboarding real de escritórios múltiplos.</p>
      <ul>
        <li>Distribua apenas chaves Ferrnet distintos do JWT em produções.</li>
        <li>Revogue tokens comprometidos e regenere chaves modelo LLM sempre que há suspeita de vazamento <em>credential stuffing</em>.</li>
      </ul>
      <blockquote>Administradores garantem atualização continuada do Corpus conforme atualizações legais setoriais e internas.</blockquote>
    </>
  );
}

export function BodyFAQ() {
  return (
    <>
      <h2 id="faq-peritos">Perfis · Peritos</h2>
      <p><strong>P: Como provo integridade anos depois?</strong> R: Guarde blobs binários evidência + relatório PDF oficial + registos infra.</p>

      <h2 id="faq-adv">Advogados</h2>
      <p><strong>P: O portal público vale como prova sozinha?</strong> R: Funciona como reforço tecnológico; processo deve considerar lei probatória geral aplicável.</p>

      <h2 id="faq-juizes">Juízes · auditores externos</h2>
      <p><strong>P: Como validam sem login?</strong> R: Via missão pública onde permitido pela controladora + digestos.</p>

      <h2 id="faq-admin">Administradores tecnológicos</h2>
      <p><strong>P: Há quotas de API aplicadas dentro do próprio servidor?</strong> R: MVP desactivou rate-limit integrado lentidão OpenAPI — mitigue via proxy frontal.</p>
    </>
  );
}

export function BodyChangelog() {
  return (
    <>
      <h2 id="fases-overview">Cronologia até Fase 10</h2>
      <ul>
        <li><strong>Fases 1-4:</strong> Núcleo HDR, ingestão inicial, EASY missões MVP.</li>
        <li><strong>Fases 5-6:</strong> Forensic PDF pipelines e melhorias UX elite.</li>
        <li><strong>Fase 7:</strong> Auditoria segurança (base para hardening Fase 9).</li>
        <li><strong>Fase 8:</strong> Shell mobile PWA, rotas <code className="inline">/m</code>, bridging push tokens.</li>
        <li><strong>Fase 9:</strong> Endurecer config (stubs timestamps, JWT vs Fernet, ingestão chained), Âncoras normativas + LGPD relatórios.</li>
        <li><strong>Fase 10 (actual):</strong> Central Docs integrada obrigando transparência de produto institucional.</li>
      </ul>
      <blockquote>Semântica semver independente será publicada após ciclo QA externo institucional — este changelog funcional descreve entregáveis roadmap interno até Maio de 2026.</blockquote>
    </>
  );
}
