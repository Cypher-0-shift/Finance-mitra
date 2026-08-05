import React from "react";
import { Lock, Scale } from "lucide-react";
import type { Language } from "../types";
import { MitraLogo } from "./MitraLogo";

interface WelcomeScreenProps {
  onSelectLanguage: (lang: Language) => void;
  onOpenCompliance: () => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  onSelectLanguage,
  onOpenCompliance,
}) => {
  return (
    <div className="bg-surface h-screen w-full overflow-hidden flex flex-col items-center justify-center relative font-sans text-on-surface">
      <div className="watermark-bg" aria-hidden="true" />
      
      <main className="w-full max-w-lg mx-auto px-4 z-10 flex flex-col items-center text-center h-full pt-8 pb-6">
        <div className="mb-3">
          <MitraLogo variant="hero" />
        </div>

        <div className="flex-grow flex flex-col justify-center w-full my-auto">
          <h1 className="text-2xl md:text-3xl font-bold text-primary mb-2 tracking-tight leading-snug">
            Your money's best friend<br />
            <span className="text-on-surface text-3xl md:text-4xl block mt-1">आपके पैसे का सबसे अच्छा दोस्त</span>
          </h1>
          
          <p className="text-base md:text-lg text-on-surface-variant mb-8 max-w-[320px] md:max-w-[400px] mx-auto leading-relaxed">
            Ask anything about money decisions, savings goals, or check if an online investment offer is trustworthy.
          </p>

          <div className="flex flex-col sm:flex-row gap-3.5 w-full max-w-[360px] mx-auto mb-6">
            <button
              id="select-lang-hindi"
              onClick={() => onSelectLanguage("hi")}
              className="flex-1 bg-primary hover:bg-primary/90 text-white font-semibold text-lg h-13 sm:h-14 rounded-full flex items-center justify-center shadow-md active:scale-95 transition-all duration-200 border border-primary/20 hover:shadow-lg"
            >
              हिन्दी (Hindi)
            </button>
            <button
              id="select-lang-english"
              onClick={() => onSelectLanguage("en")}
              className="flex-1 bg-white hover:bg-surface-container-low text-primary font-semibold text-lg h-13 sm:h-14 rounded-full flex items-center justify-center shadow-md active:scale-95 transition-all duration-200 border border-outline-variant hover:shadow-lg"
            >
              English
            </button>
          </div>
        </div>

        <div className="mt-auto pt-3 border-t border-outline-variant/30 w-full max-w-md flex flex-col items-center gap-2.5">
          <p className="text-xs sm:text-sm font-medium text-on-surface-variant/90 flex items-center justify-center gap-1.5">
            <Lock className="w-4 h-4 text-primary shrink-0" />
            <span>No sign-up needed. Start chatting instantly.</span>
          </p>
          <button
            onClick={onOpenCompliance}
            className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-semibold text-[#005f55] hover:bg-[#005f55]/10 border border-[#005f55]/30 transition-all shadow-2xs"
          >
            <Scale className="w-3.5 h-3.5" />
            <span>⚖️ Regulatory Disclaimer & SEBI Notice</span>
          </button>
        </div>
      </main>
    </div>
  );
};

