const socket = io();

const chatBox = document.getElementById("chatBox");
const topicInput = document.getElementById("topicInput");
const submitBtn = document.getElementById("submitTopic");
const recordBtn = document.getElementById("recordBtn");

// === Socket Events ===
socket.on("connect", () => {
  appendMessage("🟢 Connected to server", "system");
});

socket.on("disconnect", () => {
  appendMessage("🔴 Disconnected from server", "system");
});

socket.on("connect_error", (err) => {
  appendMessage(`❗ Connection error: ${err.message}`, "system");
});

socket.on("bot_response", (data) => {
  console.log("📥 Received from server:", data);
  const msg = data?.text || "[No response text]";
  appendMessage(msg, data?.type === "system" ? "system" : "bot");
});

socket.on("error", (data) => {
  appendMessage(`❗ ${data.message}`, "system");
});

// === Topic Submission ===
if (submitBtn && topicInput) {
  submitBtn.addEventListener("click", () => {
    const topic = topicInput.value.trim();
    if (!topic) return;

    socket.emit("topic", { text: topic });
    appendMessage(`📚 Topic: ${topic}`, "user");
    topicInput.value = "";

    // Prevent rapid double click
    submitBtn.disabled = true;
    setTimeout(() => (submitBtn.disabled = false), 500);
  });
}

// === Speech Recognition ===
if (!window.SpeechRecognition && !window.webkitSpeechRecognition) {
  appendMessage("❗ Speech Recognition not supported", "system");
  if (recordBtn) recordBtn.disabled = true;
}

const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = "en-US";
recognition.interimResults = false;
recognition.maxAlternatives = 1;

recordBtn.addEventListener("click", () => {
  try {
    recognition.start();
    recordBtn.textContent = "🎙 Listening...";
    recordBtn.classList.add("recording");
  } catch (err) {
    appendMessage(`❗ Error starting recognition: ${err.message}`, "system");
  }
});

recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  appendMessage(transcript, "user");
  socket.emit("voice_answer", { audio: transcript });
  recordBtn.textContent = "🎤 Speak a Question";
  recordBtn.classList.remove("recording");
};

recognition.onerror = (event) => {
  appendMessage(`❗ Voice error: ${event.error}`, "system");
  recordBtn.textContent = "🎤 Speak a Question";
  recordBtn.classList.remove("recording");
};

// === Append Message to Chat Box ===
function appendMessage(text, type = "bot") {
  const div = document.createElement("div");
  div.className = `message ${type}`;
  div.textContent = text;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}
