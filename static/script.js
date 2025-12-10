// Wait for DOM to load before running logic
document.addEventListener("DOMContentLoaded", () => {

    // ====== Element references ======
    const chatBox = document.querySelector(".chat-messages");     // container for all messages
    const chatArea = document.querySelector(".chat-area");        // scrollable chat area
    const welcomeBlock = document.querySelector(".welcome-block"); // initial welcome UI
    const messageInput = document.getElementById("message-input"); // text input field
    const sendBtn = document.querySelector(".icon-btn.send");      // send message button
    const stopBtn = document.querySelector(".icon-btn.stop");      // stop/abort button
    const form = document.getElementById("chat-form");             // form element
    const clearBtn = document.querySelector(".menu-item.clear");
    const uploadBtn = document.getElementById("upload-btn");
    const voiceBtn = document.getElementById("voice-btn");
    const filesBtn = document.querySelector(".menu-item.files");
    const hamburgerBtn = document.querySelector(".menu-item.hamburger");
    const sidebar = document.querySelector(".sidebar");
    const mainContent = document.querySelector(".main-content");

    // ====== State variables ======
    let isBotResponding = false;    // prevents user from sending multiple messages during response
    let abortController = null;     // controller used to stop fetch request

    // ====== Placeholder setup ======
    const defaultPlaceholder = "Ask anything...";
    const warningPlaceholder = "Type your message here...";
    messageInput.placeholder = defaultPlaceholder;

    // Show temporary red placeholder if user tries to send empty input
    function showInputWarning() {
        messageInput.placeholder = warningPlaceholder;
        messageInput.classList.add("warning");

        const clearWarning = () => {
            messageInput.placeholder = defaultPlaceholder;
            messageInput.classList.remove("warning");
            messageInput.removeEventListener("input", clearWarning);
        };
        messageInput.addEventListener("input", clearWarning);

        setTimeout(() => {
            if (messageInput.classList.contains("warning")) clearWarning();
        }, 3500);
    }

    // Generic "coming soon" popup for unfinished buttons
    function showComingSoon() {
        let alert = document.querySelector(".coming-soon-alert");

        // Create once, reuse later
        if (!alert) {
            alert = document.createElement("div");
            alert.className = "coming-soon-alert";
            alert.textContent = "Coming soon!";
            document.body.appendChild(alert);
        }

        alert.classList.add("show");
        setTimeout(() => alert.classList.remove("show"), 3000);
    }

    // Helper for blocking unimplemented buttons
    function preventAction(e, btn) {
        e.preventDefault();
        e.stopPropagation();
        btn.classList.add("prevent");
        showComingSoon();
        setTimeout(() => btn.classList.remove("prevent"), 500);
    }

    // Append a message to the chat window
    function appendMessage(sender, text, isSource = false) {
        const msg = document.createElement("div");
        msg.classList.add("msg");

        if (isSource) {
            // Render list of sources
            msg.classList.add("sources");
            const list = text.split('<br>').map(line => line.trim()).filter(Boolean);
            msg.innerHTML = `<strong>Sources:</strong><ul>${list.map(s => `<li>${s}</li>`).join('')}</ul>`;
        } else if (sender === "You") {
            msg.classList.add("user-msg");
            msg.textContent = text;
        } else {
            // Bot message (markdown allowed)
            msg.classList.add("bot-msg");
            let html = marked.parse(text);
            html = DOMPurify.sanitize(html);
            msg.innerHTML = html;
        }

        chatBox.appendChild(msg);
        scrollToBottom();
        adjustChatPadding();
    }

    // Smooth scrolling to latest message
    function scrollToBottom() {
        setTimeout(() => {
            chatArea.scrollTop = chatArea.scrollHeight + 200;
        }, 40);
    }

    // Adjust bottom padding so messages don’t hide behind input bar
    function adjustChatPadding() {
        const inputBar = document.querySelector(".chat-form.pill-input");
        const bottomSpace = inputBar.offsetHeight + 40;
        chatBox.style.paddingBottom = bottomSpace + "px";
    }

    window.addEventListener("resize", adjustChatPadding);
    setInterval(adjustChatPadding, 400); // safety check for layout shifts
    adjustChatPadding();

    // Hide welcome block once first message is sent
    function activateChatMode() {
        chatArea.classList.add("active");
        welcomeBlock.classList.add("hidden");
    }

    // Send message handler
    async function sendMessage() {
        if (isBotResponding) return;

        const msg = messageInput.value.trim();
        if (!msg) {
            showInputWarning();
            return;
        }

        isBotResponding = true;

        // Desktop: disable input during request
        // Mobile: keep enabled (avoids keyboard closing)
        if (window.innerWidth > 768) {
            messageInput.disabled = true;
        }

        sendBtn.disabled = true;
        sendBtn.style.opacity = "0.5";
        sendBtn.style.cursor = "not-allowed";
        stopBtn.style.display = "flex";

        appendMessage("You", msg);
        messageInput.value = "";
        activateChatMode();

        // Temporary typing indicator
        const typing = document.createElement("div");
        typing.className = "msg bot-msg typing";
        typing.textContent = "Bot is typing...";
        chatBox.appendChild(typing);
        scrollToBottom();

        abortController = new AbortController();
        const signal = abortController.signal;

        try {
            const res = await fetch("/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: msg }),
                signal,
            });

            const data = await res.json();
            chatBox.removeChild(typing);

            if (data?.answer) appendMessage("Bot", data.answer);

            if (Array.isArray(data?.sources) && data.sources.length) {

                const list = data.sources.map(s => {
                    let src = s.source;

                    // Convert Windows paths to normal
                    src = src.replace(/\\/g, "/");

                    // Extract filename only: data/Medical_book.pdf → Medical_book.pdf
                    let name = src.split("/").pop();

                    // Remove .pdf extension
                    name = name.replace(/\.pdf$/i, "");

                    return `${name} - page ${s.page}`;
                }).join("<br>");

                appendMessage("Bot", list, true);
            }


        } catch (err) {
            chatBox.removeChild(typing);
            appendMessage("Bot", err.name === "AbortError"
                ? "<i>Response stopped.</i>"
                : "Error reaching the server.");
        } finally {
            isBotResponding = false;

            // Desktop: return focus safely
            if (window.innerWidth > 768) {
                messageInput.disabled = false;
                messageInput.focus();
            } else {
                // Mobile: keep input enabled but don't force keyboard open
                messageInput.disabled = false;
            }

            sendBtn.disabled = false;
            sendBtn.style.opacity = "";
            sendBtn.style.cursor = "";
            stopBtn.style.display = "none";
            abortController = null;
        }
    }

    // Abort the bot's reply (used for stop button)
    function stopResponse() {
        if (isBotResponding && abortController) abortController.abort();
    }

    // Clear chat and reset UI
    async function clearChat() {
        if (isBotResponding) stopResponse();
        try { await fetch("/clear", { method: "POST" }); }
        catch (e) { console.error(e); }

        chatBox.innerHTML = "";
        chatArea.classList.remove("active");
        welcomeBlock.classList.remove("hidden");
        isBotResponding = false;
        stopBtn.style.display = "none";
        adjustChatPadding();
    }

    // ====== Event bindings ======
    form.addEventListener("submit", e => {
        e.preventDefault();
        sendMessage();
    });

    messageInput.addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn?.addEventListener("click", sendMessage);
    stopBtn?.addEventListener("click", stopResponse);
    clearBtn?.addEventListener("click", clearChat);
    uploadBtn?.addEventListener("click", e => preventAction(e, uploadBtn));
    voiceBtn?.addEventListener("click", e => preventAction(e, voiceBtn));
    filesBtn?.addEventListener("click", e => preventAction(e, filesBtn));

    // ====== Sidebar logic (desktop + mobile) ======
    function isMobile() {
        return window.innerWidth <= 768;
    }

    // Toggle sidebar depending on device type
    hamburgerBtn.addEventListener("click", () => {
        if (isMobile()) {
            sidebar.classList.toggle("mobile-open");  // mobile drawer
        } else {
            sidebar.classList.toggle("collapsed");    // desktop collapse mode
        }
    });

    // Close sidebar when tapping outside (mobile only)
    document.addEventListener("click", (e) => {
        if (!isMobile()) return;

        const clickedInsideSidebar = sidebar.contains(e.target);
        const clickedHamburger = hamburgerBtn.contains(e.target);

        if (!clickedInsideSidebar && !clickedHamburger) {
            sidebar.classList.remove("mobile-open");
        }
    });

    // Stop button hidden by default
    stopBtn.style.display = "none";

    adjustChatPadding();
});
