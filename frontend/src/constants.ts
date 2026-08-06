import type { Message } from "./types";

export const INITIAL_WELCOME_MESSAGE: Message = {
  id: "msg-welcome-init",
  sender: "system",
  textHi: "नमस्ते! 👋 मैं Finance Mitra हूँ — आपका व्यक्तिगत वित्तीय साथी। आप मुझसे पूछ सकते हैं: पैसे कहाँ सुरक्षित रखें, कोई ऑनलाइन निवेश स्कीम सही है या नहीं, या कोई भी वित्तीय सवाल।",
  textEn: "Namaste! 👋 I am Finance Mitra — your personal financial companion. You can ask me: where to safely save money, whether an online investment offer is trustworthy, or any financial question.",
  timestamp: "Just now",
  quickReplies: [
    {
      id: "qr-safe-scheme",
      textHi: "क्या यह स्कीम सेफ है?",
      textEn: "Is this scheme safe?",
      actionTextHi: "मुझे किसी ने एक स्कीम बताई है जिसमें 3 महीने में पैसे दोगुने हो जाएंगे। क्या ये सही है?",
      actionTextEn: "Someone told me about a scheme where money doubles in 3 months. Is this trustworthy?"
    },
    {
      id: "qr-saving-opts",
      textHi: "बचत के लिए सही ऑप्शन",
      textEn: "Safe saving options",
      actionTextHi: "मेरी महीने की कमाई ₹15,000 है। सुरक्षित बचत कहाँ शुरू करूँ?",
      actionTextEn: "My monthly income is ₹15,000. Where should I start saving safely?"
    },
    {
      id: "qr-rbi-rules",
      textHi: "RBI के सुरक्षा निर्देश",
      textEn: "RBI Safety Rules",
      actionTextHi: "ऑनलाइन फ्रॉड और अनजान लोन ऐप्स से बचने के लिए RBI के क्या निर्देश हैं?",
      actionTextEn: "What are the RBI safety guidelines to protect against online financial fraud and instant loan apps?"
    }
  ]
};
