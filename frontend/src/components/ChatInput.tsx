import React, { useRef } from "react";
import { Paperclip, Send } from "lucide-react";
import type { Language } from "../types";

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  onSelectPhoto: (base64DataUrl: string) => void;
  lang: Language;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onSelectPhoto,
  lang,
  disabled = false,
}) => {
  const [text, setText] = React.useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || disabled) return;
    onSendMessage(text.trim());
    setText("");
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === "string") {
          onSelectPhoto(reader.result);
        }
      };
      reader.readAsDataURL(file);
    }
    // reset input value so identical files can be selected again if needed
    if (e.target) {
      e.target.value = "";
    }
  };

  const handleInputPaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items || disabled) return;

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image") !== -1) {
        e.preventDefault();
        const file = items[i].getAsFile();
        if (file) {
          const reader = new FileReader();
          reader.onloadend = () => {
            if (typeof reader.result === "string") {
              onSelectPhoto(reader.result);
            }
          };
          reader.readAsDataURL(file);
          break;
        }
      }
    }
  };

  return (
    <footer className="fixed bottom-0 left-0 w-full z-40 bg-[#fff8f1] shadow-[0_-4px_16px_rgba(0,0,0,0.06)] border-t border-outline-variant/40">
      <div className="max-w-5xl mx-auto flex items-center gap-2 sm:gap-3 px-3 sm:px-6 py-2.5 sm:py-3 w-full">
        {/* Hidden File Input for Image attachments */}
        <input
          id="hidden-file-input"
          type="file"
          accept="image/*"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          aria-label="Upload photo or screenshot"
        />

        <button
          id="chat-attach-btn"
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          title={lang === "hi" ? "स्कीम या फोटो जोड़ें (या Ctrl+V दबाएं)" : "Attach photo or screenshot (or press Ctrl+V)"}
          className="p-2 sm:p-2.5 text-[#005f55] hover:bg-[#005f55]/10 active:scale-95 rounded-full transition-colors shrink-0 flex items-center justify-center border border-transparent hover:border-[#005f55]/20"
        >
          <Paperclip className="w-5 h-5 sm:w-6 sm:h-6" />
        </button>

        <form onSubmit={handleSend} className="flex-1 flex items-center gap-2">
          <div className="flex-1 bg-white rounded-full px-4 sm:px-5 py-2 sm:py-2.5 border border-outline-variant/60 shadow-inner flex items-center focus-within:border-[#005f55] focus-within:ring-2 focus-within:ring-[#005f55]/20 transition-all">
            <input
              id="chat-text-input"
              type="text"
              value={text}
              disabled={disabled}
              onChange={(e) => setText(e.target.value)}
              onPaste={handleInputPaste}
              placeholder={
                disabled
                  ? lang === "hi"
                    ? "मित्रा सोच रहा है..."
                    : "Mitra is thinking..."
                  : lang === "hi"
                  ? "कोई भी वित्तीय सवाल पूछें या स्कीम के बारे में बताएं..."
                  : "Ask any financial question or verify a scheme..."
              }
              className="w-full bg-transparent border-none focus:outline-none p-0 text-sm sm:text-base text-[#1e1b17] placeholder-on-surface-variant/70 font-sans"
            />
          </div>

          <button
            id="chat-send-btn"
            type="submit"
            disabled={!text.trim() || disabled}
            aria-label="Send message"
            className={`w-11 h-11 sm:w-12 sm:h-12 rounded-full flex items-center justify-center shrink-0 transition-all shadow-md ${
              text.trim() && !disabled
                ? "bg-[#005f55] text-white hover:bg-[#005f55]/90 active:scale-90 shadow-lg cursor-pointer"
                : "bg-outline-variant/30 text-outline-variant cursor-not-allowed shadow-none"
            }`}
          >
            <Send className="w-5 h-5 ml-0.5" />
          </button>
        </form>
      </div>
    </footer>
  );
};
