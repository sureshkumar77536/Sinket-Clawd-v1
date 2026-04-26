# 🌟 SINKET CLAWD v1 - Complete Guide

SINKET CLAWD ek bohot hi smooth aur mast terminal-based AI chat UI hai. Yeh mobile (Termius) aur PC dono ki screen par ekdum perfect fit hota hai. Is guide mein bataya gaya hai ki ise install kaise karna hai aur use kaise karna hai.

---

## 🚀 1. Installation (VPS ya Termius mein kaise dalein?)

Is tool ko apne VPS ya terminal mein install karna bohot aasan hai. Bas apna terminal open karna hai aur yeh ek single command paste karke **Enter** dabana hai:

```bash
git clone https://github.com/sureshkumar77536/Sinket-Clawd-v1.git ~/.sinket_clawd && bash ~/.sinket_clawd/install.sh
```

Yeh command kya karegi?
- GitHub se saari files download karegi.
- Python aur zaroori requirements (jaise rich library UI ke liye) install karegi.
- Ek global command `sinkwd` banayegi taaki isko kahin se bhi chalaya jaa sake.

---

## ⚙️ 2. First Time Setup (API Kaise Set Karein?)

Install hone ke baad, tool ko start karne ke liye terminal mein type karna hai:

```bash
sinkwd
```

Jab pehli baar `sinkwd` type karke enter karenge, toh ek mast Cyan Theme UI open hoga aur API Setup poochega:

- **Base URL:** Yahan par AI provider ka link daalna hai (Jaise: `https://api.openai.com/v1` ya koi bhi custom OpenAI compatible URL).
- **Model Name:** Jo model use karna hai uska exact naam daalna hai (Jaise: `gpt-4`, `claude-3-opus`, ya custom model name).
- **API Token/Key:** Provider ki API key daalni hai (Agar koi provider key nahi maangta, toh bas khali chhod kar Enter daba dena hai).

Bas! Setup save ho jayega aur SINKET CLAWD chat ke liye ready ho jayega.

---

## ⌨️ 3. Chat Commands (Slash / Commands ka kya kaam hai?)

Jab chat chal rahi ho, toh kuch special settings change karne ke liye in commands ka use kiya jaa sakta hai. Inhe directly **You -** wale prompt mein type karna hai:

### 🔹 `/provider`
**Kya hota hai:** Agar purana AI model, API key ya Base URL change karke naya lagana ho, toh yeh command daalni hai. Yeh wapas Setup screen open kar dega.

**Special Trick:** Agar galti se `/provider` type kar diya hai aur wapas chat mein aana hai, toh Base URL mangne par bas `exit` likh kar enter daba dena hai. Chat wahin se continue ho jayegi.

### 🔹 `/update`
**Kya hota hai:** Agar GitHub par is tool ka koi naya code ya update aaya hai, toh bas yeh command type karni hai.

**Fayda:** Yeh command background mein automatically naya code download karke tool ko restart kar degi. Aur sabse acchi baat, isse setup data aur purani chat history delete nahi hogi.

### 🔹 `/clear`
**Kya hota hai:** Yeh command poori chat history aur AI ki memory ko saaf kar deti hai.

**Kab use karein:** Jab kisi naye topic par baat karni ho aur pichli baaton ka context hatana ho, tab iska use karna hai. Screen fresh ho jayegi.

### 🔹 `/exit`
**Kya hota hai:** SINKET CLAWD ko band karne ke liye. Yeh aapko wapas normal terminal screen par bhej dega.

---

## 🔒 Data Safety

Tension lene ki zaroorat nahi hai. Jo bhi API key, URL ya chat ki baatein hoti hain, woh VPS ke andar hi background hidden files (`.sinket_config.json` aur `.sinket_history.json`) mein safe rehti hain. Tool update ya restart hone par data udta nahi hai.
