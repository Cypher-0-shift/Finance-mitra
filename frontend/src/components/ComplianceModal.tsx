import React from "react";
import { X, ShieldCheck, Scale, Lock, FileText, AlertTriangle } from "lucide-react";

interface ComplianceModalProps {
  onClose: () => void;
}

export const ComplianceModal: React.FC<ComplianceModalProps> = ({ onClose }) => {
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
            <Scale className="w-6 h-6 text-[#feae2c] shrink-0" />
            <div>
              <h2 className="text-base sm:text-lg font-bold leading-snug">
                कानूनी अस्वीकरण एवं विनियामक अनुपालन <br />
                <span className="text-xs sm:text-sm font-semibold text-amber-200">
                  Regulatory Compliance & SEBI Disclaimer Notice
                </span>
              </h2>
              <p className="text-[11px] sm:text-xs text-emerald-100/90 mt-0.5">
                सेबी (SEBI) और आर०बी०आई० (RBI) दिशानिर्देशों के अनुरूप • Aligned with SEBI & RBI Guidelines
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-white/15 active:scale-90 transition-all text-white shrink-0 ml-2"
            aria-label="Close modal"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content Body — Bilingual Hindi & English */}
        <div className="p-5 sm:p-6 space-y-5 text-sm text-[#1e1b17] leading-relaxed">
          
          {/* Section 1: Non-RIA SEBI Disclaimer */}
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-300/80 text-amber-950 flex flex-col gap-2.5">
            <div className="flex items-center gap-2 font-bold text-amber-900 text-base border-b border-amber-200/80 pb-1.5">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
              <span>
                महत्वपूर्ण विनियामक अस्वीकरण (SEBI) / SEBI Regulatory Disclaimer
              </span>
            </div>
            
            {/* Hindi Paragraph */}
            <p className="font-medium">
              🇮🇳 <strong className="text-amber-950">हिन्दी:</strong> फाइनेंस मित्रा (Finance Mitra) एक आर्टिफिशियल इंटेलिजेंस (AI) आधारित साक्षरता और स्कैम रोकथाम सहायक है। हम सेबी (SEBI) द्वारा पंजीकृत निवेश सलाहकार (RIA - Registered Investment Advisor), वित्तीय संस्था, या बैंक नहीं हैं। हमारे द्वारा दी जाने वाली सभी जानकारी केवल व्यक्तिगत जागरूकता और शिक्षा के उद्देश्य से है, इसे व्यावसायिक वित्तीय या निवेश सलाह के रूप में न लिया जाए।
            </p>
            
            {/* English Paragraph */}
            <p className="text-amber-900 text-xs sm:text-sm pt-1 border-t border-amber-200/50">
              🇬🇧 <strong>English:</strong> Finance Mitra is an AI-powered financial literacy and scam deterrence assistant. We are <strong>NOT</strong> a SEBI Registered Investment Advisor (RIA), licensed financial institution, or bank. All guidance generated is strictly for general educational awareness and fraud prevention, and must NOT be interpreted as binding commercial, investment, or banking advice.
            </p>
          </div>

          {/* Section 2: Zero-Trust Banking Credential Guarantee */}
          <div className="flex items-start gap-3.5 border-t border-slate-200 pt-4">
            <div className="p-2.5 rounded-xl bg-[#005f55]/10 text-[#005f55] shrink-0 mt-0.5">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div className="space-y-2">
              <h3 className="font-bold text-base text-[#005f55]">
                बैंकिंग सुरक्षा और OTP सुरक्षा गारंटी / Banking Safety & OTP Protection Guarantee
              </h3>
              <p className="text-slate-800 text-sm">
                🇮🇳 <strong>हिन्दी:</strong> फाइनेंस मित्रा कभी भी आपसे आपकी बैंक पासवर्ड, एटीएम पिन, यूपीआई पिन, सीवीवी (CVV), या ओटीपी (OTP) नहीं मांगता है। हम किसी भी रूप में धनराशि या पैसे का स्थानांतरण (Money Transfer) नहीं स्वीकारते। यदि कोई व्यक्ति हमारा प्रतिनिधि बनकर पैसे या पिन मांगे, तो तुरंत <strong>1930</strong> (राष्ट्रीय साइबर क्राइम हेल्पलाईन) पर रिपोर्ट करें।
              </p>
              <p className="text-slate-600 text-xs sm:text-sm pt-1 border-t border-slate-100">
                🇬🇧 <strong>English:</strong> Finance Mitra will <strong>NEVER</strong> ask for your banking account numbers, passwords, UPI/ATM PINs, debit card details, or One-Time Passwords (OTPs). We do not solicit or execute money transactions. If any individual attempting to represent this tool asks for financial credentials, report them immediately to the National Cyber Crime Hotline (<strong>1930</strong>) or cybercrime.gov.in.
              </p>
            </div>
          </div>

          {/* Section 3: Data Protection & Privacy */}
          <div className="flex items-start gap-3.5 border-t border-slate-200 pt-4">
            <div className="p-2.5 rounded-xl bg-[#005f55]/10 text-[#005f55] shrink-0 mt-0.5">
              <Lock className="w-6 h-6" />
            </div>
            <div className="space-y-2">
              <h3 className="font-bold text-base text-[#005f55]">
                डेटा सुरक्षा एवं गोपनीयता / Data Protection & End-to-End Privacy
              </h3>
              <p className="text-slate-800 text-sm">
                🇮🇳 <strong>हिन्दी:</strong> आपकी सभी बातचीत, प्रश्न, और अपलोड किए गए स्क्रीनशॉट या रसीदें सुरक्षित रूप से एम्बेड और एन्क्रिप्ट की जाती हैं। हमारे वेब डेमो सिस्टम में किसी प्रकार के व्यक्तिगत पहचान (PII) का स्थायी संग्रह या दुरुपयोग नहीं किया जाता है।
              </p>
              <p className="text-slate-600 text-xs sm:text-sm pt-1 border-t border-slate-100">
                🇬🇧 <strong>English:</strong> All user interactions, queries, and uploaded scam flyers or scheme posters are processed safely with encrypted industry standards. Our web infrastructure uses anonymized session tokens without harvesting personally identifiable information (PII).
              </p>
            </div>
          </div>

          {/* Section 4: AI Accuracy & Authoritative Verification */}
          <div className="flex items-start gap-3.5 border-t border-slate-200 pt-4">
            <div className="p-2.5 rounded-xl bg-[#005f55]/10 text-[#005f55] shrink-0 mt-0.5">
              <FileText className="w-6 h-6" />
            </div>
            <div className="w-full space-y-2">
              <h3 className="font-bold text-base text-[#005f55]">
                AI सटीकता और सरकारी स्रोतों द्वारा सत्यापन / AI Verification
              </h3>
              <p className="text-slate-800 text-sm">
                🇮🇳 <strong>हिन्दी:</strong> चूंकि यह एक AI सिस्टम (LLM) है, जटिल और बदलती वित्तीय नीतियों की सटीक पुष्टि के लिए हमेशा आधिकारिक सरकारी पोर्टल का संदर्भ लें।
              </p>
              <p className="text-slate-600 text-xs sm:text-sm">
                🇬🇧 <strong>English:</strong> As generative AI models (LLMs) evaluate dynamic financial scenarios, users are advised to verify scheme features directly on canonical public portals.
              </p>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs sm:text-sm font-medium pt-2 border-t border-slate-100">
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
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between sm:justify-end gap-3 rounded-b-2xl">
          <span className="text-xs text-slate-500 hidden sm:inline">
            Finance Mitra • AI Financial Literacy & Anti-Fraud Safety
          </span>
          <button
            onClick={onClose}
            className="w-full sm:w-auto px-7 py-2.5 bg-[#005f55] hover:bg-[#004f46] text-white rounded-full font-bold text-sm shadow-md active:scale-95 transition-all flex items-center justify-center gap-2"
          >
            <span>मैंने समझ लिया / I Understand & Accept</span>
          </button>
        </div>
      </div>
    </div>
  );
};

