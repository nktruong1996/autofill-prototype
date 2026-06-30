import { useEffect, useMemo, useRef, useState } from "react";
import { chatWithDynamicFas, resetDynamicFasSession } from "./api";
import SiteHeader, { TopNav } from "./SiteHeader";
import { loadSchemes } from "./storage";

function makeEmptyAnswers(scheme) {
  return Object.fromEntries(
    (scheme?.questions ?? []).map((question) => [String(question.question_id), ""]),
  );
}

function greetingMessages(scheme) {
  return scheme
    ? [
        {
          role: "assistant",
          content:
            "Hello! Describe your circumstances in your own words. I will suggest answers for you to review before applying them.",
        },
      ]
    : [];
}

function getSessionId(schemeId) {
  const key = `dynamic-fas-session-${schemeId}`;
  let value = sessionStorage.getItem(key);
  if (!value) {
    value = `fas-${schemeId}-${globalThis.crypto?.randomUUID?.() ?? Date.now()}`;
    sessionStorage.setItem(key, value);
  }
  return value;
}

function initialSchemeId(schemes) {
  const requested = Number(new URLSearchParams(window.location.search).get("schemeId"));
  return schemes.some((scheme) => scheme.id === requested)
    ? requested
    : schemes[0]?.id ?? null;
}

export default function AiPage() {
  const [schemes] = useState(() => loadSchemes());
  const [selectedId, setSelectedId] = useState(() => initialSchemeId(loadSchemes()));
  const selectedScheme = useMemo(
    () => schemes.find((scheme) => scheme.id === selectedId),
    [schemes, selectedId],
  );
  const [answers, setAnswers] = useState(() =>
    makeEmptyAnswers(schemes.find((scheme) => scheme.id === selectedId)),
  );
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState(() => greetingMessages(selectedScheme));
  const [suggestions, setSuggestions] = useState({});
  const [assistantState, setAssistantState] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [confirmation, setConfirmation] = useState(null);
  const [status, setStatus] = useState("");
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const visibleSuggestions = useMemo(
    () =>
      Object.entries(suggestions).filter(([questionId]) =>
        selectedScheme?.questions.some(
          (question) => String(question.question_id) === questionId,
        ),
      ),
    [selectedScheme, suggestions],
  );

  const progress = useMemo(() => {
    const required = selectedScheme?.questions.filter(
      (question) => question.is_required,
    ) ?? [];
    const completed = required.filter((question) => {
      const key = String(question.question_id);
      return answers[key]?.trim() || suggestions[key]?.trim();
    }).length;
    return { completed, total: required.length };
  }, [answers, selectedScheme, suggestions]);

  function changeScheme(event) {
    const nextId = Number(event.target.value);
    const nextScheme = schemes.find((scheme) => scheme.id === nextId);
    setSelectedId(nextId);
    setAnswers(makeEmptyAnswers(nextScheme));
    setSuggestions({});
    setAssistantState(null);
    setMessages(greetingMessages(nextScheme));
    setError("");
    setStatus("");
    const url = new URL(window.location.href);
    url.searchParams.set("schemeId", String(nextId));
    window.history.replaceState({}, "", url);
  }

  async function sendMessage(event, quickMessage) {
    event?.preventDefault();
    const userMessage = (quickMessage ?? message).trim();
    if (!userMessage || !selectedScheme || isLoading) return;

    setMessages((current) => [
      ...current,
      { role: "user", content: userMessage },
    ]);
    setMessage("");
    setError("");
    setStatus("");
    setIsLoading(true);

    try {
      const data = await chatWithDynamicFas({
        session_id: getSessionId(selectedScheme.id),
        fas_scheme_id: selectedScheme.id,
        message: userMessage,
        questions: selectedScheme.questions,
        current_answers: answers,
      });
      setMessages((current) => [
        ...current,
        { role: "assistant", content: data.reply },
      ]);
      setSuggestions(data.suggested_fields ?? {});
      setAssistantState(data.assistant_state ?? null);
    } catch (requestError) {
      setError(
        `${requestError.message}. Make sure the Python service is running on port 8000.`,
      );
    } finally {
      setIsLoading(false);
    }
  }

  function questionFor(questionId) {
    return selectedScheme.questions.find(
      (question) => String(question.question_id) === String(questionId),
    );
  }

  function commitSuggestion(questionId, value) {
    setAnswers((current) => ({ ...current, [questionId]: value }));
    setSuggestions((current) => {
      const next = { ...current };
      delete next[questionId];
      return next;
    });
    setStatus("Applied the suggestion to the form. The data has not been submitted.");
  }

  function applySuggestion(questionId, value) {
    const currentValue = answers[questionId]?.trim();
    const wasConfirmedByChat =
      assistantState?.questions?.[questionId]?.source === "confirmed_update";

    if (currentValue && currentValue !== value && !wasConfirmedByChat) {
      setConfirmation({
        questionId,
        currentValue,
        newValue: value,
      });
      return;
    }

    commitSuggestion(questionId, value);
  }

  function applyAllSuggestions() {
    const conflicts = [];
    let applied = 0;

    for (const [questionId, value] of visibleSuggestions) {
      const currentValue = answers[questionId]?.trim();
      const wasConfirmedByChat =
        assistantState?.questions?.[questionId]?.source === "confirmed_update";
      if (currentValue && currentValue !== value && !wasConfirmedByChat) {
        conflicts.push({ questionId, currentValue, newValue: value });
      } else {
        commitSuggestion(questionId, value);
        applied += 1;
      }
    }

    if (conflicts.length) {
      setConfirmation(conflicts[0]);
      setStatus(
        `Applied ${applied} suggestions. ${conflicts.length} changes still require individual confirmation.`,
      );
    }
  }

  function rejectSuggestion(questionId) {
    setSuggestions((current) => {
      const next = { ...current };
      delete next[questionId];
      return next;
    });
    setStatus("Dismissed the suggestion. The form answer was not changed.");
  }

  async function resetAssistant() {
    if (!selectedScheme) return;
    setError("");
    try {
      await resetDynamicFasSession(getSessionId(selectedScheme.id));
    } catch (requestError) {
      setError(requestError.message);
      return;
    }
    setSuggestions({});
    setAssistantState(null);
    setMessages([
      {
        role: "assistant",
        content:
          "The assistant session has been reset. Your existing form answers have been preserved.",
      },
    ]);
    setStatus("Reset the conversation without changing the form data.");
  }

  if (!selectedScheme) {
    return (
      <div className="page-shell">
        <TopNav current="ai" />
        <main className="page-content">
          <div className="empty-state card standalone-empty">
            <div className="empty-icon">?</div>
            <h1>No FAS configuration found</h1>
            <p>Create at least one FAS and an additional question before using AI.</p>
            <a className="button button-primary" href="/fas-config.html">
              Go to configuration
            </a>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <TopNav current="ai" />
      <main className="page-content">
        <SiteHeader
          eyebrow="Student application"
          title="AI Autofill for Additional Questions"
          description="AI only creates suggestions. You decide which content is applied to the FAS application."
          actions={
            <div className="header-control-group">
              <label htmlFor="scheme-select">Selected FAS</label>
              <select id="scheme-select" value={selectedId} onChange={changeScheme}>
                {schemes.map((scheme) => (
                  <option key={scheme.id} value={scheme.id}>
                    {scheme.name}
                  </option>
                ))}
              </select>
            </div>
          }
        />

        <section className="progress-card card" aria-label="Progress">
          <div className="progress-copy">
            <span className="progress-icon">✓</span>
            <div>
              <strong>Required question progress</strong>
              <span>
                Completed {progress.completed}/{progress.total} questions
              </span>
            </div>
          </div>
          <div className="progress-track" aria-hidden="true">
            <span
              style={{
                width: `${progress.total ? (progress.completed / progress.total) * 100 : 100}%`,
              }}
            />
          </div>
        </section>

        <div className="ai-layout">
          <section className="application-panel card">
            <div className="section-heading">
              <div>
                <span className="section-kicker">AdditionalQuestionAnswers</span>
                <h2>{selectedScheme.name}</h2>
                <p>Review and edit the answers before submitting the application.</p>
              </div>
              <span className="draft-badge">Draft</span>
            </div>

            <div className="application-questions">
              {selectedScheme.questions.map((question, index) => {
                const key = String(question.question_id);
                return (
                  <label className="application-question" key={question.question_id}>
                    <span>
                      <b>{index + 1}.</b> {question.question_text}
                      {question.is_required && <em>*</em>}
                    </span>
                    <textarea
                      value={answers[key] ?? ""}
                      placeholder="Enter your answer..."
                      onChange={(event) => {
                        setAnswers((current) => ({
                          ...current,
                          [key]: event.target.value,
                        }));
                        setStatus("");
                      }}
                    />
                    <small>
                      {question.is_required ? "Required" : "Optional"} · ID {question.question_id}
                    </small>
                  </label>
                );
              })}
            </div>

            <div className="form-footer-note">
              <span className="shield-icon">◇</span>
              <span>
                This prototype does not send or store application data. Submission
                will be added during the .NET integration.
              </span>
            </div>
          </section>

          <aside className="assistant-panel card">
            <div className="assistant-header">
              <div className="assistant-identity">
                <span className="assistant-avatar">AI</span>
                <div>
                  <strong>FAS Assistant</strong>
                  <span><i /> Ready to help</span>
                </div>
              </div>
              <button
                className="text-button"
                type="button"
                onClick={resetAssistant}
                disabled={isLoading}
              >
                Reset
              </button>
            </div>

            <div className="chat-messages" aria-live="polite">
              {messages.map((chatMessage, index) => (
                <div
                  className={`chat-message ${chatMessage.role}`}
                  key={`${chatMessage.role}-${index}`}
                >
                  {chatMessage.role === "assistant" && (
                    <span className="mini-avatar">AI</span>
                  )}
                  <div>{chatMessage.content}</div>
                </div>
              ))}
              {isLoading && (
                <div className="chat-message assistant">
                  <span className="mini-avatar">AI</span>
                  <div className="typing" aria-label="AI is processing">
                    <i /><i /><i />
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div className="quick-prompts">
              {["My family income has recently decreased", "My father recently lost his job"].map(
                (quickPrompt) => (
                  <button
                    key={quickPrompt}
                    type="button"
                    disabled={isLoading}
                    onClick={() => sendMessage(null, quickPrompt)}
                  >
                    {quickPrompt}
                  </button>
                ),
              )}
            </div>

            <form className="chat-composer" onSubmit={sendMessage}>
              <textarea
                value={message}
                placeholder="Describe your circumstances..."
                onChange={(event) => setMessage(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage(event);
                  }
                }}
              />
              <button
                type="submit"
                aria-label="Send message"
                disabled={!message.trim() || isLoading}
              >
                ↑
              </button>
            </form>
          </aside>
        </div>

        <section className="suggestions-section card">
          <div className="section-heading suggestions-heading">
            <div>
              <span className="section-kicker">AI suggestions</span>
              <h2>Suggestions awaiting your review</h2>
              <p>Nothing is automatically written to the form.</p>
            </div>
            {visibleSuggestions.length > 1 && (
              <button
                className="button button-primary"
                type="button"
                onClick={applyAllSuggestions}
              >
                Apply all
              </button>
            )}
          </div>

          {visibleSuggestions.length === 0 ? (
            <div className="suggestions-empty">
              <span>✦</span>
              <div>
                <strong>No suggestions yet</strong>
                <p>Chat with AI to receive suggestions for these questions.</p>
              </div>
            </div>
          ) : (
            <div className="suggestion-grid">
              {visibleSuggestions.map(([questionId, value]) => {
                const question = questionFor(questionId);
                return (
                  <article className="suggestion-card" key={questionId}>
                    <span className="suggestion-label">Question {questionId}</span>
                    <h3>{question?.question_text}</h3>
                    <blockquote>{value}</blockquote>
                    <div className="suggestion-actions">
                      <button
                        className="button button-primary"
                        type="button"
                        onClick={() => applySuggestion(questionId, value)}
                      >
                        Apply
                      </button>
                      <button
                        className="button button-ghost"
                        type="button"
                        onClick={() => rejectSuggestion(questionId)}
                      >
                        Dismiss
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}

          {status && <div className="notice success" role="status">{status}</div>}
          {error && <div className="notice error" role="alert">{error}</div>}
        </section>
      </main>

      {confirmation && (
        <div className="modal-backdrop" role="presentation">
          <div className="confirm-modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
            <span className="modal-icon">!</span>
            <h2 id="confirm-title">Confirm answer update</h2>
            <p>{questionFor(confirmation.questionId)?.question_text}</p>
            <div className="comparison-grid">
              <div>
                <span>Current answer</span>
                <p>{confirmation.currentValue}</p>
              </div>
              <div className="new-value">
                <span>New suggestion</span>
                <p>{confirmation.newValue}</p>
              </div>
            </div>
            <div className="modal-actions">
              <button
                className="button button-ghost"
                type="button"
                onClick={() => setConfirmation(null)}
              >
                Keep current answer
              </button>
              <button
                className="button button-primary"
                type="button"
                onClick={() => {
                  commitSuggestion(
                    confirmation.questionId,
                    confirmation.newValue,
                  );
                  setConfirmation(null);
                }}
              >
                Confirm update
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
