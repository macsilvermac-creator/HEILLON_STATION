"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

interface TourStep {
  target: string;
  title: string;
  description: string;
}

const TOUR_STEPS: TourStep[] = [
  {
    target: "[data-tour='mission-input']",
    title: "Escolha um modelo ou descreva",
    description:
      "Seleccione um modelo pré-configurado (risco contratual, due diligence, LGPD…) ou escreva em linguagem natural o que precisa. De seguida clique em «Iniciar análise».",
  },
  {
    target: "[data-tour='mission-approve']",
    title: "Revise e aprove os passos",
    description:
      "O sistema propõe uma sequência de assistentes de IA. Quando os passos estiverem alinhados com o Corpus Normativo, aprove para liberar a execução.",
  },
  {
    target: "[data-tour='hdr-result']",
    title: "O seu primeiro registo de custódia",
    description:
      "Após executar, cada passo gera um registo HDR imutável com hash SHA-256, carimbo temporal e assinatura criptográfica. Clique no ID para ver a cadeia completa.",
  },
  {
    target: "[data-tour='verify-link']",
    title: "Verificação pública",
    description:
      "Qualquer parte — juiz, perito, contraente — pode validar a integridade da cadeia de custódia no Portal de Verificação sem necessitar de conta.",
  },
  {
    target: "[data-tour='normative-link']",
    title: "Conformidade normativa",
    description:
      "O Hub Normativo ancora cada decisão a frameworks legais (LGPD-BR, CPP Art. 158-A, GDPR). Gere relatórios de conformidade prontos para juntada.",
  },
  {
    target: "[data-tour='docs-link']",
    title: "Central de documentação",
    description:
      "Manuais, termos de uso, política LGPD e FAQ estão disponíveis na Central de Documentação integrada ao produto.",
  },
];

const STORAGE_KEY = "heillon_onboarding_v2_completed";

export function OnboardingTour() {
  const [currentStep, setCurrentStep] = useState(0);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      if (typeof window !== "undefined" && !localStorage.getItem(STORAGE_KEY)) {
        setVisible(true);
      }
    } catch {
      setVisible(true);
    }
  }, []);

  useEffect(() => {
    if (!visible) return;
    const sel = TOUR_STEPS[currentStep]?.target;
    if (!sel) return;
    const el = document.querySelector(sel);
    el?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [currentStep, visible]);

  const finish = useCallback(() => {
    setVisible(false);
    try {
      localStorage.setItem(STORAGE_KEY, "true");
    } catch {
      /* private mode */
    }
  }, []);

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep((s) => s + 1);
    } else {
      finish();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) setCurrentStep((s) => s - 1);
  };

  if (!visible) return null;

  const step = TOUR_STEPS[currentStep];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[150] bg-deep-space-900/75 backdrop-blur-sm"
        aria-modal
        role="dialog"
        aria-labelledby="onboarding-title"
      >
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.22 }}
          className="absolute bottom-8 left-1/2 w-full max-w-lg -translate-x-1/2 px-4"
        >
          <div className="glass-card mx-auto rounded-2xl border border-white/12 p-6">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-xs text-white/40">
                {currentStep + 1} / {TOUR_STEPS.length}
              </span>
              <button
                type="button"
                onClick={finish}
                className="text-xs text-white/35 transition-colors hover:text-white/65"
              >
                Pular tour
              </button>
            </div>

            <h3 id="onboarding-title" className="mb-2 text-xl font-bold text-white">
              {step.title}
            </h3>
            <p className="mb-6 text-sm leading-relaxed text-white/65">{step.description}</p>

            <div className="flex items-center justify-between gap-3">
              <div className="flex gap-1.5">
                {TOUR_STEPS.map((_, i) => (
                  <button
                    key={i}
                    type="button"
                    aria-label={`Ir para passo ${i + 1}`}
                    onClick={() => setCurrentStep(i)}
                    className={`h-2 rounded-full transition-all ${
                      i === currentStep ? "w-5 bg-gold-500" : "w-2 bg-white/20 hover:bg-white/35"
                    }`}
                  />
                ))}
              </div>

              <div className="flex gap-2">
                {currentStep > 0 && (
                  <button
                    type="button"
                    onClick={handlePrev}
                    className="rounded-full border border-white/15 px-4 py-2 text-xs text-white/60 transition-colors hover:border-white/30 hover:text-white"
                  >
                    Anterior
                  </button>
                )}
                <button type="button" onClick={handleNext} className="btn-gold px-5 py-2 text-xs">
                  {currentStep < TOUR_STEPS.length - 1 ? "Próximo →" : "Concluir"}
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
