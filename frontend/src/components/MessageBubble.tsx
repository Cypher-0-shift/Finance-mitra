import React from "react";
import { CheckCheck, AlertTriangle, ShieldAlert, ShieldCheck, ChevronRight } from "lucide-react";
import type { Message, Language } from "../types";

interface MessageBubbleProps {
  message: Message;
  lang: Language;
  onSelectQuickReply?: (textHi: string, textEn: string) => void;
}

const renderClickableText = (content: string, isUser: boolean) => {
  if (!content) return null;
  const urlRegex = /(https?:\/\/[^\s()<>]+[^\s`!()\[\]{};:'".,<>?«»“”‘’])/g;
  const parts = content.split(urlRegex);

  return parts.map((part, index) => {
    if (part.match(urlRegex)) {
      return (
        <a
          key={index}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className={`font-semibold underline transition-colors break-all ${
            isUser ? "text-[#004f46] hover:text-black" : "text-blue-600 hover:text-blue-800"
          }`}
        >
          {part}
        </a>
      );
    }
    return <span key={index}>{part}</span>;
  });
};

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  lang,
  onSelectQuickReply,
}) => {
  const isUser = message.sender === "user";
  const text = lang === "hi" ? message.textHi : message.textEn;
  const actionText = lang === "hi" ? message.actionAdviceHi : message.actionAdviceEn;

  return (
    <div className={`flex flex-col w-full my-1.5 ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={`w-fit min-w-[90px] max-w-[88%] md:max-w-[75%] shadow-sm border border-black/5 rounded-2xl transition-all duration-200 overflow-hidden ${
          isUser
            ? "bg-[#DCF8C6] text-on-surface rounded-tr-xs"
            : "bg-white text-on-surface rounded-tl-xs"
        }`}
      >
        {/* Verdict Header Strip */}
        {message.verdict && (
          <div
            className={`px-4 py-2 flex items-center gap-2 font-semibold text-sm break-words ${
              message.verdict === "danger"
                ? "bg-[#ba1a1a] text-white"
                : message.verdict === "caution"
                ? "bg-[#feae2c] text-[#633f00]"
                : "bg-[#005f55]/15 text-[#005f55]"
            }`}
          >
            {message.verdict === "danger" && <ShieldAlert className="w-5 h-5 shrink-0" />}
            {message.verdict === "caution" && <AlertTriangle className="w-5 h-5 shrink-0" />}
            {message.verdict === "safe" && <ShieldCheck className="w-5 h-5 shrink-0" />}
            <span className="truncate">
              {lang === "hi"
                ? message.verdictTitleHi || "विशेष टिप्पणी"
                : message.verdictTitleEn || "Financial Assessment"}
            </span>
          </div>
        )}

        {/* Bubble Inner Content with responsive spacing and word wrap */}
        <div className={`flex flex-col gap-2 ${isUser ? "px-3.5 py-2.5 sm:px-4 sm:py-3" : "px-4 py-3 sm:px-5 sm:py-4"} break-words [word-break:break-word]`}>
          {/* Optional Attached Image Thumbnail */}
          {message.imageUrl && (
            <div className="rounded-xl overflow-hidden border border-outline-variant/30 max-h-60 bg-surface-container w-full">
              <img
                src={message.imageUrl}
                alt="User submission attachment"
                className="w-full h-full object-cover rounded-xl"
              />
            </div>
          )}

          {/* Highlighted Verdict Sub-Heading */}
          {message.verdict && (
            <div className="font-bold text-[#005f55] text-base sm:text-[17px]">
              {lang === "hi" ? message.verdictDetailHi : message.verdictDetailEn}
            </div>
          )}

          {/* Main Message Text */}
          <div className="text-[15px] sm:text-[16px] md:text-[17px] leading-[1.65] whitespace-pre-wrap text-[#1e1b17]">
            {renderClickableText(text || "", isUser)}
          </div>

          {/* Recommended Action Box */}
          {actionText && (
            <div className="mt-1 p-3.5 rounded-xl bg-[#f4ede5] border-l-4 border-[#005f55] text-sm md:text-[15px] leading-relaxed text-[#1e1b17] shadow-2xs">
              <strong className="text-[#005f55] block mb-1 font-semibold">
                {lang === "hi" ? "क्या करें / सलाह:" : "Recommended Action:"}
              </strong>
              <div>{renderClickableText(actionText, isUser)}</div>
            </div>
          )}

          {/* Timestamp & Status Icon in natural flex flow */}
          <div className="flex items-center justify-end gap-1 -mb-1 pt-0.5 opacity-75 text-[11px] font-medium text-on-surface-variant select-none">
            <span>{message.timestamp}</span>
            <CheckCheck
              className={`w-3.5 h-3.5 shrink-0 ${isUser ? "text-[#34b7f1]" : "text-outline"}`}
            />
          </div>
        </div>
      </div>

      {/* Quick Reply Tappable Chips below System Messages */}
      {!isUser && message.quickReplies && message.quickReplies.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-2 max-w-[92%] md:max-w-[80%] pl-1">
          {message.quickReplies.map((qr) => (
            <button
              key={qr.id}
              id={`quick-reply-${qr.id}`}
              onClick={() =>
                onSelectQuickReply &&
                onSelectQuickReply(qr.actionTextHi, qr.actionTextEn)
              }
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border border-[#005f55] bg-white text-[#005f55] hover:bg-[#005f55]/10 active:scale-95 text-xs sm:text-sm font-semibold shadow-sm transition-all"
            >
              <span>{lang === "hi" ? qr.textHi : qr.textEn}</span>
              <ChevronRight className="w-4 h-4 shrink-0 opacity-70" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
