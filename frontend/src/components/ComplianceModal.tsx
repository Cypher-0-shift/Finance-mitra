import React from "react";
import { X, ShieldCheck, Scale, Lock, FileText, AlertTriangle } from "lucide-react";
import type { Language } from "../types";

interface ComplianceModalProps {
  lang: Language;
  onClose: () => void;
}

export const ComplianceModal: React.FC<ComplianceModalProps> = ({ lang, onClose }) => {
  const isHi = lang === "hi";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-3 sm:p-4 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl w-full max-w-2xl max-h-[88vh] overflow-y-auto shadow-2xl border border-black/10 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 bg-[#005f55] text-white px-5 py-4 flex items-center justify-between shadow-md rounded-t-2xl">
          <div className="flex items-center gap-2.5">
            <Scale className="w-6 h-6 text-amber-300 shrink-0" />
            <div>
              <h2 className="text-base sm:text-lg font-bold">
                {isHi
                  ? "कानूनी अस्वीकरण एवं विनियामक अनुपालन"
                  : "Regulatory Compliance & Legal Disclaimer"}
              </h2>
              <p className="text-xs text-amber-100 opacity-90">
                {isHi
                  ? "सेबी (SEBI) और आर०बी०आई० (RBI) दिशानिर्देशों के अनुरूप"
                  : "Aligned with SEBI & RBI Educational Guidelines"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-white/15 active:scale-90 transition-all text-white"
            aria-label="Close modal"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 sm:p-6 space-y-5 text-sm sm:text-[15px] text-[#1e1b17] leading-relaxed">
          
          {/* Section 1: Non-RIA SEBI Disclaimer */}
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-300/80 text-amber-950 flex flex-col gap-2">
            <div className="flex items-center gap-2 font-bold text-amber-900 text-base">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
              <span>
                {isHi ? "महत्वपूर्ण विनियामक अस्वीकरण (SEBI)" : "Important SEBI Regulatory Disclaimer"}
              </span>
            </div>
            <p>
              {isHi
                ? "फाइनेंशियल मित्रा (Financial Mitra) एक आर्टिफिशियल इंटेलिजेंस (AI) आधारित साक्षरता और स्कैम रोकथाम सहायक है। हम सेबी (SEBI) द्वारा पंजीकृत निवेश सलाहकार (RIA - Registered Investment Advisor), वित्तीय संस्था, या बैंक नहीं हैं। हमारे द्वारा दी जाने वाली सभी जानकारी केवल व्यक्तिगत जागरूकता और शिक्षा के उद्देश्य से है, इसे व्यावसायिक वित्तीय या निवेश सलाह के रूप में न लिया जाए।"
                : "Financial Mitra is an AI-powered financial literacy and scam deterrence assistant. We are NOT a SEBI Registered Investment Advisor (RIA), licensed financial institution, or bank. All guidance generated is strictly for general educational awareness and fraud prevention, and must NOT be interpreted as binding commercial, investment, or banking advice."}
            </p>
          </div>

          {/* Section 2: Zero-Trust Banking Credential Guarantee */}
          <div className="flex items-start gap-3.5 border-t border-outline-variant/30 pt-4">
            <div className="p-2.5 rounded-xl bg-[#005f55]/10 text-[#005f55] shrink-0 mt-0.5">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#005f55] mb-1">
                {isHi ? "बैंकिंग सुरक्षा और OTP सुरक्षा गारंटी" : "Banking Safety & OTP Protection Guarantee"}
              </h3>
              <p className="text-on-surface-variant">
                {isHi
                  ? "फाइनेंशियल मित्रा कभी भी आपसे आपकी बैंक पासवर्ड, एटीएम पिन, यूपीआई पिन, सीवीवी (CVV), या ओटीपी (OTP) नहीं मांगता है। हम किसी भी रूप में धनराशि या पैसे का स्थानांतरण (Money Transfer) नहीं स्वीकारते। यदि कोई व्यक्ति हमारा प्रतिनिधि बनकर पैसे या पिन मांगे, तो तुरंत 1930 (राष्ट्रीय साइबर क्राइम हेल्पलाईन) पर रिपोर्ट करें।"
                  : "Financial Mitra will NEVER ask for your banking account numbers, passwords, UPI/ATM PINs, debit card details, or One-Time Passwords (OTPs). We do not solicit or execute money transactions. If any individual attempting to represent this tool asks for financial credentials, report them immediately to the National Cyber Crime Hotline (1930) or cybercrime.gov.in."}
              </p>
            </div>
          </div>

          {/* Section 3: Data Protection & Privacy */}
          <div className="flex items-start gap-3.5 border-t border-outline-variant/30 pt-4">
            <div className="p-2.5 rounded-xl bg-[#005f55]/10 text-[#005f55] shrink-0 mt-0.5">
              <Lock className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#005f55] mb-1">
                {isHi ? "डेटा सुरक्षा एवं गोपनीयता (Data Privacy)" : "Data Protection & End-to-End Privacy"}
              </h3>
              <p className="text-on-surface-variant">
                {isHi
                  ? "आपकी सभी बातचीत, प्रश्न, और अपलोड किए गए स्क्रीनशॉट या रसीदें सुरक्षित रूप से एम्बेड और एन्क्रिप्ट की जाती हैं। हमारे वेब डेमो सिस्टम में किसी प्रकार के व्यक्तिगत पहचान (PII) का स्थायी संग्रह या दुरुपयोग नहीं किया जाता है।"
                  : "All user interactions, queries, and uploaded scam flyers or scheme posters are processed safely with encrypted industry standards. Our public testing web infrastructure uses anonymized session tokens without harvesting personally identifiable information (PII)."}
              </p>
            </div>
          </div>

          {/* Section 4: AI Accuracy & Authoritative Verification */}
          <div className="flex items-start gap-3.5 border-t border-outline-variant/30 pt-4">
            <div className="p-2.5 rounded-xl bg-[#005f55]/10 text-[#005f55] shrink-0 mt-0.5">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#005f55] mb-1">
                {isHi ? "AI सटीकता और सरकारी स्रोतों द्वारा सत्यापन" : "AI Limitations & Governmental Verification"}
              </h3>
              <p className="text-on-surface-variant mb-2">
                {isHi
                  ? "चूंकि यह एक AI सिस्टम (LLM) है, जटिल और बदलती वित्तीय नीतियों की सटीक पुष्टि के लिए हमेशा आधिकारिक सरकारी पोर्टल का संदर्भ लें। हम किसी भी वित्तीय निर्णय या नुकसान के लिए कानूनी रूप से उत्तरदायी नहीं हैं:"
                  : "As generative AI reasoning models (LLMs) evaluate dynamic financial scenarios, users are advised to verify all critical scheme features directly on canonical public portals. Financial Mitra accepts no fiscal liability for personal decisions based on automated evaluations:"}
              </p>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs sm:text-sm font-medium pt-1">
                <li>
                  <a
                    href="https://www.rbi.org.in"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-700 hover:underline inline-flex items-center gap-1"
                  >
                    • Reserve Bank of India (RBI) ↗
                  </a>
                </li>
                <li>
                  <a
                    href="https://www.sebi.gov.in"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-700 hover:underline inline-flex items-center gap-1"
                  >
                    • SEBI Official Portal ↗
                  </a>
                </li>
                <li>
                  <a
                    href="https://cybercrime.gov.in"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-700 hover:underline inline-flex items-center gap-1"
                  >
                    • National Cyber Crime (1930) ↗
                  </a>
                </li>
                <li>
                  <a
                    href="https://sancharsaathi.gov.in"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-700 hover:underline inline-flex items-center gap-1"
                  >
                    • Sanchar Saathi Spam Report ↗
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-surface-container-low border-t border-outline-variant/40 flex items-center justify-end rounded-b-2xl">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-[#005f55] text-white rounded-full font-semibold text-sm hover:bg-[#005f55]/90 active:scale-95 transition-all shadow-sm"
          >
            {isHi ? "मैंने समझ लिया / बंद करें" : "I Understand & Acknowledge"}
          </button>
        </div>
      </div>
    </div>
  );
};
