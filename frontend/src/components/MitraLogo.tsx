import React from "react";

interface MitraLogoProps {
  variant?: "hero" | "compact";
  className?: string;
}

export const MitraLogo: React.FC<MitraLogoProps> = ({ variant = "hero", className = "" }) => {
  if (variant === "compact") {
    return (
      <div className={`flex items-center gap-2.5 ${className}`}>
        {/* Compact Emblem */}
        <div className="relative w-9 h-9 rounded-full bg-gradient-to-br from-[#feae2c] to-[#d97706] p-[2px] shadow-sm shrink-0 flex items-center justify-center">
          <div className="w-full h-full rounded-full bg-[#005f55] flex items-center justify-center">
            <svg
              viewBox="0 0 32 32"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="w-5 h-5 text-white"
            >
              {/* Shield/Arch & Rupee Symbol */}
              <path
                d="M16 4C10.5 4 6 7.5 6 12C6 19 14.5 25.5 16 27C17.5 25.5 26 19 26 12C26 7.5 21.5 4 16 4Z"
                fill="url(#goldGradientCompact)"
                fillOpacity="0.15"
                stroke="#feae2c"
                strokeWidth="1.5"
                strokeLinejoin="round"
              />
              <text
                x="16"
                y="19"
                textAnchor="middle"
                fill="#feae2c"
                fontSize="13"
                fontWeight="800"
                fontFamily="sans-serif"
              >
                ₹
              </text>
              <defs>
                <linearGradient id="goldGradientCompact" x1="6" y1="4" x2="26" y2="27" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#feae2c" />
                  <stop offset="1" stopColor="#d97706" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-[#005f55] rounded-full border border-white flex items-center justify-center">
            <svg className="w-2.5 h-2.5 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        </div>

        {/* Compact Wordmark */}
        <div className="flex flex-col">
          <div className="flex items-baseline gap-1">
            <span className="text-lg sm:text-xl font-bold tracking-tight text-white font-sans leading-none">
              Finance
            </span>
            <span className="text-lg sm:text-xl font-extrabold tracking-tight text-[#feae2c] font-sans leading-none">
              Mitra
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 self-baseline mb-0.5 ml-0.5" />
          </div>
          <span className="text-[11px] text-white/80 font-medium tracking-wide">
            AI Companion • आपका मित्र
          </span>
        </div>
      </div>
    );
  }

  // Hero Variant for Welcome Screen
  return (
    <div className={`flex flex-col items-center select-none ${className}`}>
      {/* Hero Vector Emblem */}
      <div className="relative group mb-5">
        <div className="w-28 h-28 sm:w-32 sm:h-32 rounded-3xl bg-gradient-to-tr from-[#005f55] via-[#0d7a6e] to-[#004f46] p-[3px] shadow-xl hover:shadow-2xl transition-all duration-300 transform group-hover:scale-[1.03] flex items-center justify-center ring-4 ring-[#feae2c]/20">
          <div className="w-full h-full rounded-[21px] sm:rounded-[25px] bg-[#fff8f1] flex flex-col items-center justify-center p-3 relative overflow-hidden">
            
            {/* Background geometric pattern in logo card */}
            <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#005f55_1.5px,transparent_1.5px)] [background-size:14px_14px]" />
            
            <svg
              viewBox="0 0 64 64"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              className="w-16 h-16 sm:w-20 sm:h-20 drop-shadow-md z-10"
            >
              {/* Outer Shield Arch */}
              <path
                d="M32 8C20 8 10 16 10 26C10 41 28 54 32 58C36 54 54 41 54 26C54 16 44 8 32 8Z"
                fill="url(#shieldGradient)"
                stroke="#005f55"
                strokeWidth="2.5"
                strokeLinejoin="round"
              />
              
              {/* Inner Gold Shield Accent */}
              <path
                d="M32 12C22 12 14 19 14 27C14 39 29 49 32 53C35 49 50 39 50 27C50 19 42 12 32 12Z"
                fill="url(#goldGradientHero)"
              />

              {/* Glowing Indian Rupee Symbol */}
              <text
                x="32"
                y="40"
                textAnchor="middle"
                fill="white"
                fontSize="28"
                fontWeight="800"
                fontFamily="sans-serif"
                className="drop-shadow"
              >
                ₹
              </text>

              <defs>
                <linearGradient id="shieldGradient" x1="10" y1="8" x2="54" y2="58" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#005f55" />
                  <stop offset="1" stopColor="#0d7a6e" />
                </linearGradient>
                <linearGradient id="goldGradientHero" x1="14" y1="12" x2="50" y2="53" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#feae2c" />
                  <stop offset="1" stopColor="#d97706" />
                </linearGradient>
              </defs>
            </svg>

          </div>
        </div>

        {/* Security & Verification Shield Badge */}
        <div className="absolute -bottom-2 -right-2 bg-[#005f55] text-white px-2.5 py-1 rounded-full shadow-lg border-2 border-white flex items-center gap-1">
          <svg className="w-3.5 h-3.5 text-emerald-400 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span className="text-[11px] font-bold tracking-tight text-white uppercase pr-0.5">Verified</span>
        </div>
      </div>

      {/* Hero Wordmark */}
      <div className="flex flex-col items-center">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#005f55]">
            FINANCE
          </span>
          <span className="text-2xl sm:text-3xl font-black tracking-tight text-[#d97706] bg-gradient-to-r from-[#feae2c] to-[#d97706] bg-clip-text text-transparent">
            MITRA
          </span>
        </div>
        <div className="h-0.5 w-16 bg-gradient-to-r from-transparent via-[#005f55]/40 to-transparent my-1" />
      </div>
    </div>
  );
};
