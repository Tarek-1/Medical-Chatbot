// Wait for the page (HTML) to fully load before running this script
document.addEventListener("DOMContentLoaded", () => {

    // ====== Grab all needed elements from the HTML page ======
    const chatBox = document.querySelector(".chat-messages");     // where all messages show
    const chatArea = document.querySelector(".chat-area");        // main chat container
    const welcomeBlock = document.querySelector(".welcome-block"); // the welcome section before chat starts
    const messageInput = document.getElementById("message-input"); // text box for typing
    const sendBtn = document.querySelector(".icon-btn.send");      // send button
    const stopBtn = document.querySelector(".icon-btn.stop");      // stop button
    const form = document.getElementById("chat-form");             // the chat form (input + send)

    // menu buttons
    const clearBtn = document.querySelector(".menu-item.clear");
    const uploadBtn = document.getElementById("upload-btn");
    const voiceBtn = document.getElementById("voice-btn");
    const filesBtn = document.querySelector(".menu-item.files");
    const hamburgerBtn = document.querySelector(".menu-item.hamburger");

    // ====== Variables for chatbot behavior ======
    let isBotResponding = false;  // prevents sending new messages while bot is replying
    let abortController = null;   // helps us stop the fetch request if needed

    // ====== Placeholder text setup ======
    const defaultPlaceholder = "Ask anything...";       // normal placeholder text
    const warningPlaceholder = "Type your message here..."; // shown when input is empty
    messageInput.placeholder = defaultPlaceholder;      // set default when page loads

    // ====== Show warning in input when user sends empty message ======
    function showInputWarning() {
        messageInput.placeholder = warningPlaceholder;
        messageInput.classList.add("warning"); // change color or style (CSS handles it)

        // If user starts typing, remove the warning
        const clearWarning = () => {
            messageInput.placeholder = defaultPlaceholder;
            messageInput.classList.remove("warning");
            messageInput.removeEventListener("input", clearWarning);
        };
        messageInput.addEventListener("input", clearWarning);

        // Auto-remove the warning after 3.5 seconds (just in case)
        setTimeout(() => {
            if (messageInput.classList.contains("warning")) {
                clearWarning();
            }
        }, 3500);
    }

    // ====== Show "Coming soon!" alert for unfinished buttons ======
    function showComingSoon() {
        // Check if alert already exists, otherwise create it
        let alert = document.querySelector(".coming-soon-alert");
        if (!alert) {
            alert = document.createElement("div");
            alert.className = "coming-soon-alert";
            alert.textContent = "Coming soon!";
            document.body.appendChild(alert);
        }

        // Make it visible for a few seconds
        alert.classList.add("show");
        setTimeout(() => alert.classList.remove("show"), 3000);
    }

    // ====== Disable click + show the "Coming soon!" alert ======
    function preventAction(e, btn) {
        e.preventDefault();   // stop button’s default behavior
        e.stopPropagation();  // stop event from affecting anything else
        btn.classList.add("prevent"); // change button appearance (CSS)
        showComingSoon();     // show the popup alert
        setTimeout(() => btn.classList.remove("prevent"), 500); // reset style after half a sec
    }

    // ====== Add a new message to the chat window ======
    function appendMessage(sender, text, isSource = false) {
        const msg = document.createElement("div");
        msg.classList.add("msg");

        if (isSource) {
            // Format and show sources list under bot’s answer
            msg.classList.add("sources");
            const list = text.split('<br>').map(line => line.trim()).filter(Boolean);
            const html = `<strong>Sources:</strong><ul>${list.map(s => `<li>${s}</li>`).join('')}</ul>`;
            msg.innerHTML = html;
        } else if (sender === "You") {
            // User message bubble
            msg.classList.add("user-msg");
            msg.textContent = text;
        } else {
            // Bot message bubble (with markdown support)
            msg.classList.add("bot-msg");
            let html = marked.parse(text);          // convert markdown text to HTML
            html = DOMPurify.sanitize(html);        // clean it to prevent malicious code
            msg.innerHTML = html;
        }

        // Add message to chat box
        chatBox.appendChild(msg);

        // Auto-scroll to the bottom after new message appears
        setTimeout(() => {
            chatArea.scrollTop = chatArea.scrollHeight + 200; // offset for input bar
        }, 50);

    }

    // ====== Switch from welcome screen to chat mode ======
    function activateChatMode() {
        chatArea.classList.add("active");
        welcomeBlock.classList.add("hidden");
    }

    // ====== Send user message and get bot response ======
    async function sendMessage() {
        if (isBotResponding) return; // block if bot is still replying

        const msg = messageInput.value.trim(); // remove spaces

        if (!msg) {
            showInputWarning();
            return;
        }

        // Disable input while waiting for bot
        isBotResponding = true;
        messageInput.disabled = true;
        sendBtn.disabled = true;
        sendBtn.style.opacity = "0.5";
        sendBtn.style.cursor = "not-allowed";
        stopBtn.style.display = "flex";

        // Show user’s message instantly
        appendMessage("You", msg);
        messageInput.value = "";
        activateChatMode();

        // Show typing indicator
        const typing = document.createElement("div");
        typing.className = "msg bot-msg typing";
        typing.textContent = "Bot is typing...";
        chatBox.appendChild(typing);
        chatArea.scrollTop = chatArea.scrollHeight;

        // Allow abortion (stop button)
        abortController = new AbortController();
        const signal = abortController.signal;

        try {
            // Send user message to Flask backend
            const res = await fetch("/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: msg }),
                signal,
            });

            // Wait for JSON reply
            const data = await res.json();
            chatBox.removeChild(typing); // remove typing indicator

            // Show bot reply and sources (if any)
            if (data?.answer) appendMessage("Bot", data.answer);
            if (Array.isArray(data?.sources) && data.sources.length) {
                const list = data.sources.map(s => `${s.source} - page ${s.page}`).join("<br>");
                appendMessage("Bot", list, true);
            }
        } catch (err) {
            // Handle network or abort errors
            chatBox.removeChild(typing);
            if (err.name === "AbortError") {
                appendMessage("Bot", "<i>Response stopped.</i>");
            } else {
                console.error(err);
                appendMessage("Bot", "Error reaching the server.");
            }
        } finally {
            // Re-enable input and buttons
            isBotResponding = false;
            messageInput.disabled = false;
            sendBtn.disabled = false;
            sendBtn.style.opacity = "";
            sendBtn.style.cursor = "";
            stopBtn.style.display = "none";
            abortController = null;
            messageInput.focus();
        }
    }

    // ====== Stop bot response when user clicks "Stop" ======
    function stopResponse() {
        if (!isBotResponding || !abortController) return;
        abortController.abort();
    }

    // ====== Clear all chat messages ======
    async function clearChat() {
        if (isBotResponding) stopResponse();
        try {
            await fetch("/clear", { method: "POST" }); // tell Flask to clear history
        } catch (e) {
            console.error(e);
        }

        // Reset chat area visually
        chatBox.innerHTML = "";
        chatArea.classList.remove("active");
        welcomeBlock.classList.remove("hidden");
        isBotResponding = false;
        stopBtn.style.display = "none";
    }

    // ====== EVENT LISTENERS (User interactions) ======

    // When user submits the form (presses send button)
    form.addEventListener("submit", (e) => {
        e.preventDefault();  // prevent page reload
        sendMessage();       // send the message to backend
    });

    // When user presses Enter key (but not Shift+Enter)
    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Button clicks
    sendBtn?.addEventListener("click", sendMessage);
    stopBtn?.addEventListener("click", stopResponse);
    clearBtn?.addEventListener("click", clearChat);

    // "Coming soon" buttons
    uploadBtn?.addEventListener("click", (e) => preventAction(e, uploadBtn));
    voiceBtn?.addEventListener("click", (e) => preventAction(e, voiceBtn));
    filesBtn?.addEventListener("click", (e) => preventAction(e, filesBtn));
    hamburgerBtn?.addEventListener("click", (e) => preventAction(e, hamburgerBtn));

    // Hide stop button when app first loads
    stopBtn.style.display = "none";
});
