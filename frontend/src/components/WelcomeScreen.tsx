import React from "react";
import { Lock, Scale } from "lucide-react";
import type { Language } from "../types";
import { MitraLogo } from "./MitraLogo";

interface WelcomeScreenProps {
  currentLang: Language;
  onSelectLanguage: (lang: Language) => void;
  onStartChat: () => void;
  onOpenCompliance: () => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  currentLang,
  onSelectLanguage,
  onStartChat,
  onOpenCompliance,
}) => {
  const isHi = currentLang === "hi";

  return (
    <div className="bg-surface h-screen w-full overflow-hidden flex flex-col items-center justify-center relative font-sans text-on-surface">
      <div className="watermark-bg" aria-hidden="true" />
      
      <main className="w-full max-w-lg mx-auto px-4 z-10 flex flex-col items-center text-center h-full pt-8 pb-6">
        <div className="mb-3">
          <MitraLogo variant="hero" />
        </div>

        <div className="flex-grow flex flex-col justify-center w-full my-auto">
          <h1 className="text-2xl md:text-3xl font-bold text-primary mb-2 tracking-tight leading-snug">
            {isHi ? "आपके पैसे का सबसे अच्छा दोस्त" : "Your money's best friend"}
          </h1>
          
          <p className="text-base md:text-lg text-on-surface-variant mb-6 max-w-[320px] md:max-w-[400px] mx-auto leading-relaxed">
            {isHi
              ? "पैसे से जुड़े फैसले, बचत लक्ष्य, या किसी ऑनलाइन निवेश की सच्चाई जानने के लिए कुछ भी पूछें।"
              : "Ask anything about money decisions, savings goals, or check if an online investment offer is trustworthy."}
          </p>

          {/* Step 1: Language Selector */}
          <div className="mb-5 w-full max-w-[380px] mx-auto">
            <label className="block text-xs font-bold text-[#005f55] uppercase tracking-wider mb-2">
              {isHi ? "1. अपनी पसंदीदा भाषा चुनें / Select Language" : "1. Select Language / अपनी पसंदीदा भाषा चुनें"}
            </label>
            <div className="grid grid-cols-2 gap-3 p-1.5 bg-slate-100/80 rounded-2xl border border-slate-200 shadow-inner">
              <button
                id="select-lang-hindi"
                onClick={() => onSelectLanguage("hi")}
                className={`py-3 px-4 rounded-xl font-bold text-base transition-all duration-200 flex items-center justify-center gap-1.5 ${
                  isHi
                    ? "bg-[#005f55] text-white shadow-md ring-2 ring-[#feae2c]"
                    : "bg-white text-[#005f55] hover:bg-slate-50 border border-slate-200"
                }`}
              >
                <span>हिन्दी (Hindi)</span>
                {isHi && <span className="text-[#feae2c]">✓</span>}
              </button>
              <button
                id="select-lang-english"
                onClick={() => onSelectLanguage("en")}
                className={`py-3 px-4 rounded-xl font-bold text-base transition-all duration-200 flex items-center justify-center gap-1.5 ${
                  !isHi
                    ? "bg-[#005f55] text-white shadow-md ring-2 ring-[#feae2c]"
                    : "bg-white text-[#005f55] hover:bg-slate-50 border border-slate-200"
                }`}
              >
                <span>English</span>
                {!isHi && <span className="text-[#feae2c]">✓</span>}
              </button>
            </div>
          </div>

          {/* Step 2: Start / Continue Button */}
          <div className="w-full max-w-[380px] mx-auto mb-4">
            <button
              id="btn-start-chat"
              onClick={onStartChat}
              className="w-full bg-gradient-to-r from-[#005f55] to-[#0d7a6e] hover:from-[#004f46] hover:to-[#005f55] text-white font-bold text-lg h-14 rounded-2xl flex items-center justify-center gap-2 shadow-lg hover:shadow-xl active:scale-[0.98] transition-all duration-200 ring-2 ring-[#feae2c]/40"
            >
              <span>{isHi ? "आगे बढ़ें (बातचीत शुरू करें) →" : "Continue to Chat →"}</span>
            </button>
          </div>
        </div>

        <div className="mt-auto pt-3 border-t border-outline-variant/30 w-full max-w-md flex flex-col items-center gap-2.5">
          <p className="text-xs sm:text-sm font-medium text-on-surface-variant/90 flex items-center justify-center gap-1.5">
            <Lock className="w-4 h-4 text-primary shrink-0" />
            <span>{isHi ? "कोई साइन-अप की आवश्यकता नहीं • तुरंत शुरू करें" : "No sign-up needed. Start chatting instantly."}</span>
          </p>
          <button
            onClick={onOpenCompliance}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold text-[#005f55] hover:bg-[#005f55]/10 border border-[#005f55]/30 transition-all shadow-2xs"
          >
            <Scale className="w-3.5 h-3.5" />
            <span>{isHi ? "⚖️ कानूनी सूचना और SEBI अस्वीकरण" : "⚖️ Regulatory Disclaimer & SEBI Notice"}</span>
          </button>
        </div>
      </main>
    </div>
  );
};

