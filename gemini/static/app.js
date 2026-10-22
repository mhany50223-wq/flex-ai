const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const messages = document.getElementById("messages");
const sendButton = document.getElementById("send-button");
const newChatButton = document.getElementById("new-chat");
let conversation = [];

function cleanAssistantText(text) {
    // سطر الحماية الجديد: لو النص مش موجود أو مش نص، رجعه زي ما هو فوراً
    if (!text || typeof text !== 'string') return text || "";

    return text
        .replace(/\*\*([^*]+)\*\*/g, "$1")
        .replace(/__([^_]+)__/g, "$1")
        .replace(/^#{1,6}\s+/gm, "")
        .trim();
}

function addMessage(text, role, temporary = false) {
	const wrapper = document.createElement("div");
	wrapper.className = `message ${role}-message`;
	if (temporary) wrapper.id = "loading-message";

	const avatar = document.createElement("div");
	avatar.className = "avatar";
	avatar.textContent = role === "user" ? "أنت" : "✦";

	const bubble = document.createElement("div");
	bubble.className = "bubble";
	bubble.textContent = role === "assistant" && !temporary ? cleanAssistantText(text) : text;

	wrapper.append(avatar, bubble);
	if (role === "assistant" && !temporary) {
		const actions = document.createElement("div");
		actions.className = "message-actions";
		const copyButton = document.createElement("button");
		copyButton.className = "copy-button";
		copyButton.type = "button";
		copyButton.title = "Copy response";
		copyButton.setAttribute("aria-label", "Copy response");
		copyButton.textContent = "⧉";
		copyButton.addEventListener("click", async () => {
			try {
				await navigator.clipboard.writeText(bubble.textContent);
				copyButton.textContent = "✓";
				copyButton.classList.add("copied");
				setTimeout(() => {
					copyButton.textContent = "⧉";
					copyButton.classList.remove("copied");
				}, 1400);
			} catch {
				copyButton.textContent = "!";
			}
		});
		actions.appendChild(copyButton);
		wrapper.appendChild(actions);
	}
	messages.appendChild(wrapper);
	messages.scrollTop = messages.scrollHeight;
}

function setLoading(loading) {
	sendButton.disabled = loading;
	input.disabled = loading;
	if (loading) addMessage("FLEX يفكر...", "assistant", true);
	else document.getElementById("loading-message")?.remove();
}

async function sendMessage(message) {
	addMessage(message, "user");
	setLoading(true);

	try {
		const response = await fetch("/api/chat", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ message, conversation }),
		});
		const data = await response.json();
		if (!response.ok) throw new Error(data.error || "تعذر إرسال الرسالة");

		addMessage(data.answer, "assistant");
		conversation.push({ role: "user", content: message });
		conversation.push({ role: "assistant", content: data.answer });
	} catch (error) {
		addMessage(`حدث خطأ: ${error.message}`, "assistant");
	} finally {
		setLoading(false);
		input.disabled = false;
		input.focus();
	}
}

form.addEventListener("submit", (event) => {
	event.preventDefault();
	const message = input.value.trim();
	if (!message || sendButton.disabled) return;
	input.value = "";
	input.style.height = "auto";
	sendMessage(message);
});

input.addEventListener("input", () => {
	input.style.height = "auto";
	input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
});

input.addEventListener("keydown", (event) => {
	if (event.key === "Enter" && !event.shiftKey) {
		event.preventDefault();
		form.requestSubmit();
	}
});

document.querySelectorAll("[data-suggestion]").forEach((button) => {
	button.addEventListener("click", () => {
		input.value = button.dataset.suggestion;
		input.focus();
	});
});

newChatButton.addEventListener("click", () => {
	conversation = [];
	messages.innerHTML = `
		<div class="message assistant-message">
			<div class="avatar">✦</div>
			<div class="bubble">بدأنا محادثة جديدة مع FLEX. كيف يمكنني مساعدتك؟</div>
		</div>`;
	input.value = "";
	input.focus();
});
