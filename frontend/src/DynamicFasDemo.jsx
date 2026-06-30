import { useMemo, useState } from "react";

const API_URL = "http://localhost:8001";

const DEFAULT_FIELDS = [
  {
    field_id: "household_condition",
    label: "Household Conditions",
    description: "Household circumstances requiring financial assistance.",
    type: "textarea",
    required: true,
    options: [],
  },
  {
    field_id: "employment_status",
    label: "Employment Status",
    description: "Current work situation of the parent or guardian.",
    type: "select",
    required: true,
    options: [
      "Unemployed",
      "Part-time employed",
      "Full-time employed",
      "Self-employed",
      "Retired",
      "Student",
      "Other",
    ],
  },
  {
    field_id: "monthly_income",
    label: "Monthly Income",
    description: "Approximate monthly household income, if the applicant provides it.",
    type: "text",
    required: true,
    options: [],
  },
  {
    field_id: "application_reason",
    label: "Reason for Applying",
    description: "Why the applicant needs financial assistance.",
    type: "textarea",
    required: true,
    options: [],
  },
  {
    field_id: "household_condition_warranting_fas",
    label: "Household Condition to Warrant FAS Application",
    description:
      "Specific household conditions that justify or warrant the FAS application.",
    type: "textarea",
    required: true,
    options: [],
  },
];

function buildEmptyFormData(fields) {
  return fields.reduce((acc, field) => {
    acc[field.field_id] = "";
    return acc;
  }, {});
}

function DynamicField({ field, value, onChange }) {
  return (
    <label className="dynamic-field">
      <span>
        {field.label}
        {field.required ? <em>Required</em> : null}
      </span>
      {field.description ? <small>{field.description}</small> : null}

      {field.type === "textarea" ? (
        <textarea
          value={value}
          onChange={(event) => onChange(field.field_id, event.target.value)}
        />
      ) : null}

      {field.type === "select" ? (
        <select
          value={value}
          onChange={(event) => onChange(field.field_id, event.target.value)}
        >
          <option value="">Select an option</option>
          {field.options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      ) : null}

      {field.type === "text" ? (
        <input
          value={value}
          onChange={(event) => onChange(field.field_id, event.target.value)}
        />
      ) : null}
    </label>
  );
}

function DynamicFasDemo() {
  const fields = useMemo(() => DEFAULT_FIELDS, []);
  const [sessionId] = useState("dynamic-demo-1");
  const [message, setMessage] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [assistantState, setAssistantState] = useState(null);
  const [suggestedFields, setSuggestedFields] = useState({});
  const [progress, setProgress] = useState({
    completed: 0,
    total: fields.filter((field) => field.required).length,
    required_fields: fields
      .filter((field) => field.required)
      .map((field) => field.field_id),
  });
  const [formData, setFormData] = useState(() => buildEmptyFormData(fields));

  async function sendMessage() {
    if (!message.trim()) return;

    const userMessage = message.trim();
    setChatMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage },
    ]);
    setMessage("");

    const response = await fetch(`${API_URL}/dynamic-fas/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: userMessage,
        fields,
      }),
    });

    const data = await response.json();
    setChatMessages((prev) => [
      ...prev,
      { role: "assistant", content: data.reply },
    ]);
    setAssistantState(data.assistant_state);
    setSuggestedFields(data.suggested_fields);
    setProgress(data.progress);
  }

  function updateFormField(fieldId, value) {
    setFormData((prev) => ({
      ...prev,
      [fieldId]: value,
    }));
  }

  function applySuggestionsToForm() {
    setFormData((prev) => ({
      ...prev,
      ...suggestedFields,
    }));
  }

  async function resetConversation() {
    await fetch(`${API_URL}/dynamic-fas/reset-session`, {
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
    setAssistantState(null);
    setSuggestedFields({});
    setProgress({
      completed: 0,
      total: fields.filter((field) => field.required).length,
      required_fields: fields
        .filter((field) => field.required)
        .map((field) => field.field_id),
    });
    setFormData(buildEmptyFormData(fields));
  }

  return (
    <div className="dynamic-demo">
      <section className="panel">
        <h2>Dynamic Chat Assistant</h2>

        <div className="chat-box">
          {chatMessages.length === 0 ? (
            <p className="muted">
              Start by describing the applicant's situation.
            </p>
          ) : null}
          {chatMessages.map((msg, index) => (
            <div key={`${msg.role}-${index}`} className={`message ${msg.role}`}>
              <strong>{msg.role === "user" ? "You" : "Assistant"}:</strong>{" "}
              {msg.content}
            </div>
          ))}
        </div>

        <div className="input-row">
          <input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") sendMessage();
            }}
            placeholder="Example: I am unemployed and applying because..."
          />
          <button onClick={sendMessage}>Send</button>
          <button onClick={resetConversation}>Reset</button>
        </div>
      </section>

      <section className="panel">
        <h2>Required Progress</h2>
        <p>
          {progress.completed} / {progress.total} required fields completed
        </p>
      </section>

      <section className="panel">
        <h2>Admin Field Definitions</h2>
        <div className="field-definition-list">
          {fields.map((field) => (
            <div key={field.field_id} className="field-definition">
              <strong>{field.label}</strong>
              <code>{field.field_id}</code>
              <span>{field.type}</span>
              {field.required ? <span>required</span> : <span>optional</span>}
            </div>
          ))}
        </div>
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
        <h2>Dynamic FAS Form</h2>
        {fields.map((field) => (
          <DynamicField
            key={field.field_id}
            field={field}
            value={formData[field.field_id] || ""}
            onChange={updateFormField}
          />
        ))}

        <button
          onClick={applySuggestionsToForm}
          disabled={Object.keys(suggestedFields).length === 0}
        >
          Apply Suggestions to Form
        </button>
      </section>

      <section className="panel">
        <h2>Assistant State</h2>
        {assistantState ? (
          <pre>{JSON.stringify(assistantState, null, 2)}</pre>
        ) : (
          <p>No assistant state yet.</p>
        )}
      </section>
    </div>
  );
}

export default DynamicFasDemo;
