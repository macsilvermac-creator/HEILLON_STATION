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
    title: "Comece por aqui",
    description:
      "Descreva o que precisa em linguagem natural. Ex.: «Analisar estes documentos e identificar cláusulas de risco». De seguida use «Planear DAG».",
  },
  {
    target: "[data-tour='mission-approve']",
    title: "Revise e aprove",
    description:
      "O plano EASY propõe nós e agentes. Quando estiver alinhado com o Corpus Normativo, aprove antes de executar a cadeia.",
  },
  {
    target: "[data-tour='verify-link']",
    title: "Verificação pública",
    description:
      "Cada passo relevante gera provas HDR encadeadas. Use o Portal de Verificação para validar integridade.",
  },
  {
    target: "[data-tour='normative-link']",
    title: "Conformidade",
    description: "O Hub Normativo ancora as decisões a frameworks (LGDP, etc.) e permite relatórios de conformidade.",
  },
  {
    target: "[data-tour='docs-link']",
    title: "Documentação",
    description: "Manuais, termos, LGPD e FAQ — tudo na Central de Documentação integrada.",
  },
];

const STORAGE_KEY = "heillon_onboarding_completed";

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

  if (!visible) return null;

  const step = TOUR_STEPS[currentStep];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[150] bg-deep-space-900/80 backdrop-blur-sm"
        aria-modal
        role="dialog"
        aria-labelledby="onboarding-title"
      >
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-8 left-1/2 w-full max-w-lg -translate-x-1/2 px-4"
        >
          <div className="glass-card mx-auto rounded-2xl border border-white/12 p-6">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-sm text-white/50">
                Passo {currentStep + 1} de {TOUR_STEPS.length}
              </span>
              <button
                type="button"
                onClick={finish}
                className="text-sm text-white/40 transition-colors hover:text-white/75"
              >
                Pular tour
              </button>
            </div>
            <h3 id="onboarding-title" className="mb-2 text-xl font-bold text-white">
              {step.title}
            </h3>
            <p className="mb-6 text-sm leading-relaxed text-white/70">{step.description}</p>
            <div className="flex items-center justify-between gap-3">
              <div className="flex gap-1.5">
                {TOUR_STEPS.map((_, i) => (
                  <div
                    key={i}
                    className={`h-2 w-2 rounded-full transition-colors ${i === currentStep ? "bg-gold-500" : "bg-white/20"}`}
                  />
                ))}
              </div>
              <button type="button" onClick={handleNext} className="btn-gold px-6 py-2 text-sm">
                {currentStep < TOUR_STEPS.length - 1 ? "Próximo" : "Concluir"}
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
