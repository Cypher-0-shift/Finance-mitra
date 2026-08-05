export type Language = "hi" | "en";

export type VerdictType = "safe" | "caution" | "danger" | null;

export interface QuickReply {
  id: string;
  textHi: string;
  textEn: string;
  actionTextHi: string;
  actionTextEn: string;
}

export interface Message {
  id: string;
  sender: "user" | "system";
  textHi: string;
  textEn: string;
  timestamp: string;
  verdict?: VerdictType;
  verdictTitleHi?: string;
  verdictTitleEn?: string;
  verdictDetailHi?: string;
  verdictDetailEn?: string;
  actionAdviceHi?: string;
  actionAdviceEn?: string;
  imageUrl?: string;
  quickReplies?: QuickReply[];
}

export interface DevChatResponse {
  reply_text: string;
  input_type_replied: string;
  verdict?: string | null;
  escalation_recommended: boolean;
  next_action: string;
}
