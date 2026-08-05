import React, { useState } from "react";
import { X, Send, Sparkles } from "lucide-react";
import type { Language } from "../types";

interface PhotoPreviewModalProps {
  imageUrl: string;
  lang: Language;
  onClose: () => void;
  onSend: (captionHi: string, captionEn: string) => void;
}

export const PhotoPreviewModal: React.FC<PhotoPreviewModalProps> = ({
  imageUrl,
  lang,
  onClose,
  onSend,
}) => {
  const [caption, setCaption] = useState("");

  const handleSend = () => {
    const defaultTextHi = "मैंने इस वित्तीय विज्ञापन/स्कीम की तस्वीर संलग्न की है। कृपया जाँचें कि यह सुरक्षित है या कोई धोखाधड़ी है?";
    const defaultTextEn = "I have attached a photo of this financial offer/scheme. Please inspect if this is safe or potential fraud?";
    
    const submittedHi = caption.trim() ? `${caption.trim()} (Photo attached)` : defaultTextHi;
    const submittedEn = caption.trim() ? `${caption.trim()} (Photo attached)` : defaultTextEn;
    
    onSend(submittedHi, submittedEn);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-white rounded-2xl max-w-md w-full overflow-hidden shadow-2xl flex flex-col transform transition-all border border-outline-variant/30">
        
        {/* Modal Header */}
        <div className="bg-[#005f55] px-4 py-3 text-white flex items-center justify-between">
          <div className="flex items-center gap-2 font-semibold">
            <Sparkles className="w-5 h-5 text-amber-300" />
            <span>{lang === "hi" ? "तस्वीर की जाँच करें (AI OCR)" : "AI OCR Photo Inspection"}</span>
          </div>
          <button
            id="modal-close-btn"
            onClick={onClose}
            aria-label="Close modal"
            className="p-1 rounded-full hover:bg-white/20 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 flex flex-col gap-4 bg-[#ECE5DD]">
          <div className="relative rounded-xl overflow-hidden max-h-72 w-full bg-black/5 flex items-center justify-center border border-black/10 shadow-inner">
            <img
              src={imageUrl}
              alt="Uploaded schema or flyer preview"
              className="max-h-72 w-auto object-contain mx-auto rounded-lg"
            />
          </div>

          <p className="text-xs font-medium text-[#005f55] bg-[#005f55]/10 p-2 rounded-lg text-center">
            {lang === "hi"
              ? "✨ हमारा AI इंजन इस तस्वीर के टेक्स्ट (OCR) और स्कीम दावों का तुरंत विश्लेषण करेगा।"
              : "✨ Our AI vision engine will inspect OCR text and financial claims from this image."}
          </p>

          <div className="flex flex-col">
            <label htmlFor="photo-caption-input" className="text-xs font-semibold text-[#1e1b17] mb-1">
              {lang === "hi" ? "अतिरिक्त प्रश्न (वैकल्पिक):" : "Additional question (optional):"}
            </label>
            <input
              id="photo-caption-input"
              type="text"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder={lang === "hi" ? "जैसे: क्या इसमें निवेश करना सही है?" : "e.g., Should I trust this scheme?"}
              className="w-full px-3 py-2.5 rounded-xl border border-outline-variant bg-white text-on-surface focus:outline-none focus:ring-2 focus:ring-[#005f55] text-sm shadow-sm"
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
            />
          </div>
        </div>

        {/* Modal Actions */}
        <div className="bg-white px-4 py-3 flex items-center justify-end gap-3 border-t border-outline-variant/20">
          <button
            id="modal-cancel-btn"
            onClick={onClose}
            className="px-4 py-2 rounded-full font-semibold text-sm text-on-surface-variant hover:bg-surface-variant transition-colors"
          >
            {lang === "hi" ? "रद्द करें" : "Cancel"}
          </button>
          <button
            id="modal-send-btn"
            onClick={handleSend}
            className="px-5 py-2 rounded-full bg-[#005f55] text-white font-semibold text-sm hover:bg-[#005f55]/90 active:scale-95 transition-all flex items-center gap-2 shadow-md"
          >
            <span>{lang === "hi" ? "जाँच के लिए भेजें" : "Inspect Offer"}</span>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
