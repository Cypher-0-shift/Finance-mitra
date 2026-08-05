import { useState, useEffect, useRef } from "react";
import { WelcomeScreen } from "./components/WelcomeScreen";
import { TopAppBar } from "./components/TopAppBar";
import { MessageBubble } from "./components/MessageBubble";
import { ChatInput } from "./components/ChatInput";
import { PhotoPreviewModal } from "./components/PhotoPreviewModal";
import { ComplianceModal } from "./components/ComplianceModal";
import type { Language, Message, DevChatResponse } from "./types";
import { INITIAL_WELCOME_MESSAGE } from "./constants";

export function App() {
  const [activeScreen, setActiveScreen] = useState<"welcome" | "chat">("welcome");
  const [currentLang, setCurrentLang] = useState<Language>("hi");
  const [messages, setMessages] = useState<Message[]>([INITIAL_WELCOME_MESSAGE]);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [selectedPhotoUrl, setSelectedPhotoUrl] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [isComplianceOpen, setIsComplianceOpen] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Generate or retrieve persistent session ID for chat interaction
    let sid = localStorage.getItem("mitra_session_id");
    if (!sid) {
      sid = "demo_" + Math.random().toString(36).substring(2, 10);
      localStorage.setItem("mitra_session_id", sid);
    }
    setSessionId(sid);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (activeScreen === "chat") {
      scrollToBottom();
    }
  }, [messages, isTyping, activeScreen]);

  // Global clipboard paste handler for Ctrl+V / Cmd+V image pasting anywhere in chat
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      if (activeScreen === "welcome" || isTyping) return;
      
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf("image") !== -1) {
          e.preventDefault();
          const file = items[i].getAsFile();
          if (file) {
            const reader = new FileReader();
            reader.onloadend = () => {
              if (typeof reader.result === "string") {
                setSelectedPhotoUrl(reader.result);
              }
            };
            reader.readAsDataURL(file);
            break;
          }
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [activeScreen, isTyping]);

  const handleSelectLanguage = (lang: Language) => {
    setCurrentLang(lang);
    setActiveScreen("chat");
  };

  const handleToggleLang = () => {
    setCurrentLang((prev) => (prev === "hi" ? "en" : "hi"));
  };

  const handleResetSession = () => {
    const newSid = "demo_" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("mitra_session_id", newSid);
    setSessionId(newSid);
    setMessages([INITIAL_WELCOME_MESSAGE]);
    setActiveScreen("welcome");
  };

  const formatCurrentTime = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  const processIncomingMessage = async (
    textHi: string,
    textEn: string,
    imageUrl?: string
  ) => {
    const time = formatCurrentTime();
    const userMsg: Message = {
      id: "msg-" + Date.now(),
      sender: "user",
      textHi,
      textEn,
      timestamp: time,
      imageUrl,
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    const backendUrl = import.meta.env.VITE_API_URL || "https://financial-mitra.onrender.com";
    const inputPayload = imageUrl
      ? {
          session_id: sessionId,
          message: currentLang === "hi" ? textHi : textEn,
          input_type: "image",
          media_base64: imageUrl.includes(",") ? imageUrl.split(",")[1] : imageUrl,
          language: currentLang,
        }
      : {
          session_id: sessionId,
          message: currentLang === "hi" ? textHi : textEn,
          input_type: "text",
          language: currentLang,
        };

    try {
      // Attempt real network communication with backend /dev/chat endpoint
      const response = await fetch(`${backendUrl}/dev/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(inputPayload),
      });

      if (response.ok) {
        const data: DevChatResponse = await response.json();
        const serverMsg: Message = {
          id: "sys-" + Date.now(),
          sender: "system",
          textHi: data.reply_text,
          textEn: data.reply_text,
          timestamp: formatCurrentTime(),
          verdict:
            data.verdict === "caution"
              ? "caution"
              : data.verdict === "danger"
              ? "danger"
              : data.verdict === "safe"
              ? "safe"
              : null,
          verdictDetailHi: data.verdict ? "AI Scam Verdict" : undefined,
          verdictDetailEn: data.verdict ? "AI Scam Verdict" : undefined,
          actionAdviceHi: data.next_action,
          actionAdviceEn: data.next_action,
        };
        setIsTyping(false);
        setMessages((prev) => [...prev, serverMsg]);
      } else {
        throw new Error(`API returned HTTP ${response.status}`);
      }
    } catch (error) {
      // Handle network or server errors authentically without mock data
      const errorMsg: Message = {
        id: "err-" + Date.now(),
        sender: "system",
        textHi: "क्षम्यताम् (Sorry), अभी हम सर्वर से संपर्क नहीं कर पा रहे हैं। कृपया अपने नेटवर्क या इंटरनेट कनेक्शन की जांच करें और कुछ देर बाद पुनः प्रयास करें। 🙏",
        textEn: "We are currently experiencing difficulties communicating with the Financial Mitra backend server. Please check your connection and try again shortly. 🙏",
        timestamp: formatCurrentTime(),
        verdict: "caution",
        verdictTitleHi: "कनेक्शन त्रुटि (Connection Error)",
        verdictTitleEn: "Connection Error",
        verdictDetailHi: "सर्वर से संपर्क विफल",
        verdictDetailEn: "Server Unreachable",
        actionAdviceHi: "कृपया थोड़ी देर रुकें और फिर से अपना प्रश्न पूछें।",
        actionAdviceEn: "Please wait a moment and submit your inquiry again."
      };
      setIsTyping(false);
      setMessages((prev) => [...prev, errorMsg]);
    }
  };

  const handleSendMessage = (text: string) => {
    processIncomingMessage(text, text);
  };

  const handleSelectQuickReply = (actionHi: string, actionEn: string) => {
    processIncomingMessage(actionHi, actionEn);
  };

  const handleSendPhoto = (captionHi: string, captionEn: string) => {
    if (selectedPhotoUrl) {
      processIncomingMessage(captionHi, captionEn, selectedPhotoUrl);
      setSelectedPhotoUrl(null);
    }
  };

  if (activeScreen === "welcome") {
    return (
      <>
        <WelcomeScreen
          onSelectLanguage={handleSelectLanguage}
          onOpenCompliance={() => setIsComplianceOpen(true)}
        />
        {isComplianceOpen && (
          <ComplianceModal
            lang={currentLang}
            onClose={() => setIsComplianceOpen(false)}
          />
        )}
      </>
    );
  }

  return (
    <div className="min-h-screen flex flex-col font-sans bg-[#ECE5DD] text-[#1e1b17] selection:bg-[#005f55]/20">
      <TopAppBar
        currentLang={currentLang}
        onToggleLang={handleToggleLang}
        onResetSession={handleResetSession}
        onOpenCompliance={() => setIsComplianceOpen(true)}
      />

      {/* Main Conversational Stream */}
      <main className="flex-1 pt-20 pb-24 w-full overflow-y-auto">
        <div className="w-full max-w-5xl mx-auto px-3 sm:px-6 flex flex-col gap-3">
          
          {/* Encryption Trust Banner inside chat */}
          <div className="my-2 p-2 rounded-lg bg-surface-container-low border border-black/5 shadow-2xs max-w-lg mx-auto text-center text-[11px] sm:text-xs text-on-surface-variant font-medium flex items-center justify-center gap-1.5 opacity-85">
            <span>🔒</span>
            <span>
              {currentLang === "hi"
                ? "आपके सभी संदेश और तस्वीरें एंड-टू-एंड সুরক্ষিত और प्राइवेट हैं।"
                : "All conversational messages and uploaded receipts are securely encrypted & protected."}
            </span>
          </div>

          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              lang={currentLang}
              onSelectQuickReply={handleSelectQuickReply}
            />
          ))}

          {/* Animated Typing Dots when AI is generating answer */}
          {isTyping && (
            <div className="flex items-center self-start my-2 max-w-[80%]">
              <div className="bg-white rounded-2xl rounded-tl-xs px-4 py-3 shadow-sm border border-black/5 flex items-center gap-1.5">
                <div className="w-2 h-2 bg-[#005f55] rounded-full typing-dot" />
                <div className="w-2 h-2 bg-[#005f55] rounded-full typing-dot" />
                <div className="w-2 h-2 bg-[#005f55] rounded-full typing-dot" />
              </div>
              <span className="ml-2 text-xs font-semibold text-[#005f55]/80 animate-pulse">
                {currentLang === "hi" ? "मित्रा सोच रहा है..." : "Mitra is evaluating..."}
              </span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Floating Chat Bottom Bar */}
      <ChatInput
        onSendMessage={handleSendMessage}
        onSelectPhoto={(dataUrl) => setSelectedPhotoUrl(dataUrl)}
        lang={currentLang}
        disabled={isTyping}
      />

      {/* Image Preview Modal */}
      {selectedPhotoUrl && (
        <PhotoPreviewModal
          imageUrl={selectedPhotoUrl}
          lang={currentLang}
          onClose={() => setSelectedPhotoUrl(null)}
          onSend={handleSendPhoto}
        />
      )}

      {/* Legal & Regulatory Compliance Modal */}
      {isComplianceOpen && (
        <ComplianceModal
          lang={currentLang}
          onClose={() => setIsComplianceOpen(false)}
        />
      )}
    </div>
  );
}

export default App;
