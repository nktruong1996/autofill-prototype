import { useState } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

function App() {
  const [sessionId] = useState("demo-1");
  const [message, setMessage] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [suggestedFields, setSuggestedFields] = useState({});
  const [progress, setProgress] = useState({ completed: 0, total: 3 });
  const [formData, setFormData] = useState({
  employment_status: "",
  employer_name: "",
  application_reason: "",
  });

  async function sendMessage() {
    if (!message.trim()) return;

    const userMessage = message.trim();

    setChatMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage },
    ]);

    setMessage("");

    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: userMessage,
      }),
    });

    const data = await response.json();

    setChatMessages((prev) => [
      ...prev,
      { role: "assistant", content: data.reply },
    ]);

    setSuggestedFields(data.suggested_fields);
    setProgress(data.progress);
  }

  function applySuggestionsToForm() {
    setFormData((prev) => ({
      ...prev,
      ...suggestedFields,
    }));
  }

  async function resetConversation() {
  await fetch(`${API_URL}/reset-session`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
    }),
  });

  setMessage("");
  setChatMessages([]);
  setSuggestedFields({});
  setProgress({ completed: 0, total: 3 });
  setFormData({
    employment_status: "",
    employer_name: "",
    application_reason: "",
  });
}

  return (
    <div className="app">
      <h1>FAS AI Autofill Demo</h1>

      <section className="panel">
        <h2>Chat Assistant</h2>

        <div className="chat-box">
          {chatMessages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              <strong>{msg.role === "user" ? "You" : "Assistant"}:</strong>{" "}
              {msg.content}
            </div>
          ))}
        </div>

        <div className="input-row">
          <input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Tell me about your employment status..."
          />
          <button onClick={sendMessage}>Send</button>
          <button onClick={resetConversation}>Reset</button>
        </div>
      </section>

      <section className="panel">
        <h2>Progress</h2>
        <p>
          {progress.completed} / {progress.total} fields completed
        </p>
      </section>

      <section className="panel">
        <h2>Suggested Fields</h2>

        {Object.keys(suggestedFields).length === 0 ? (
          <p>No suggestions yet.</p>
        ) : (
          <pre>{JSON.stringify(suggestedFields, null, 2)}</pre>
        )}
      </section>

      <section className="panel">
        <h2>FAS Form</h2>

        <label>
          Employment Status
          <input
            value={formData.employment_status}
            onChange={(e) =>
              setFormData({ ...formData, employment_status: e.target.value })
            }
          />
        </label>

        <label>
          Employer Name
          <input
            value={formData.employer_name}
            onChange={(e) =>
              setFormData({ ...formData, employer_name: e.target.value })
            }
          />
        </label>

        <label>
          Application Reason
          <textarea
            value={formData.application_reason}
            onChange={(e) =>
              setFormData({ ...formData, application_reason: e.target.value })
            }
          />
        </label>

        <button
          onClick={applySuggestionsToForm}
          disabled={Object.keys(suggestedFields).length === 0}
        >
          Apply Suggestions to Form
        </button>
      </section>
    </div>
  );
}

export default App;
