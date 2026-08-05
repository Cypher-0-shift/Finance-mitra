import React from "react";
import { Globe, RotateCcw, Scale } from "lucide-react";
import type { Language } from "../types";
import { MitraLogo } from "./MitraLogo";

interface TopAppBarProps {
  currentLang: Language;
  onToggleLang: () => void;
  onResetSession: () => void;
  onOpenCompliance: () => void;
}

export const TopAppBar: React.FC<TopAppBarProps> = ({
  currentLang,
  onToggleLang,
  onResetSession,
  onOpenCompliance,
}) => {
  return (
    <header className="w-full fixed top-0 left-0 z-50 bg-[#005f55] text-white shadow-md">
      <div className="max-w-5xl mx-auto flex items-center justify-between px-3 sm:px-6 py-2.5 sm:py-3 w-full">
        <div className="flex items-center">
          <MitraLogo variant="compact" />
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2.5">
          <button
            onClick={onOpenCompliance}
            title={currentLang === "hi" ? "कानूनी एवं विनियामक अस्वीकरण" : "Regulatory Disclaimer & Legal Notice"}
            className="p-2 sm:px-2.5 sm:py-1.5 rounded-full border border-amber-300/60 bg-amber-400/15 text-amber-200 text-xs font-semibold hover:bg-amber-400/25 active:scale-95 transition-all flex items-center gap-1 shrink-0"
          >
            <Scale className="w-4 h-4 shrink-0 text-amber-300" />
            <span className="hidden md:inline">
              {currentLang === "hi" ? "कानूनी सूचना" : "Legal / SEBI"}
            </span>
          </button>

          <button
            id="header-reset-session"
            onClick={onResetSession}
            title={currentLang === "hi" ? "नई बातचीत शुरू करें" : "Start New Chat"}
            className="p-2 sm:px-3 sm:py-1.5 rounded-full border border-white/30 text-white text-xs font-semibold hover:bg-white/10 active:scale-95 transition-all flex items-center gap-1.5 shrink-0"
          >
            <RotateCcw className="w-4 h-4 shrink-0" />
            <span className="hidden sm:inline">
              {currentLang === "hi" ? "नयी बातचीत" : "Reset Chat"}
            </span>
          </button>

          <button
            id="header-lang-toggle"
            onClick={onToggleLang}
            className="flex items-center gap-1.5 px-3 sm:px-3.5 py-1.5 rounded-full border border-white/40 bg-white/10 text-white text-xs sm:text-sm font-semibold hover:bg-white/20 active:scale-95 transition-all shadow-sm shrink-0"
          >
            <Globe className="w-4 h-4 shrink-0 text-amber-200" />
            <span>{currentLang === "hi" ? "हिन्दी / EN" : "EN / हिन्दी"}</span>
          </button>
        </div>
      </div>
    </header>
  );
};

