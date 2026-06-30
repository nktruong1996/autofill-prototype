import { useMemo, useState } from "react";
import SiteHeader, { TopNav } from "./SiteHeader";
import {
  getNextQuestionId,
  getNextSchemeId,
  loadSchemes,
  saveSchemes,
} from "./storage";

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

export default function ConfigPage() {
  const [schemes, setSchemes] = useState(() => loadSchemes());
  const [selectedId, setSelectedId] = useState(() => loadSchemes()[0]?.id ?? null);
  const [notice, setNotice] = useState("");

  const selectedScheme = useMemo(
    () => schemes.find((scheme) => scheme.id === selectedId),
    [schemes, selectedId],
  );

  function updateSelected(updater) {
    setSchemes((current) =>
      current.map((scheme) =>
        scheme.id === selectedId ? updater(clone(scheme)) : scheme,
      ),
    );
    setNotice("");
  }

  function addScheme() {
    const id = getNextSchemeId(schemes);
    const nextScheme = {
      id,
      name: `New FAS ${id}`,
      questions: [],
    };
    setSchemes((current) => [...current, nextScheme]);
    setSelectedId(id);
    setNotice("");
  }

  function deleteScheme() {
    if (!selectedScheme) return;
    if (!window.confirm(`Delete the “${selectedScheme.name}” configuration?`)) return;

    const remaining = schemes.filter((scheme) => scheme.id !== selectedScheme.id);
    setSchemes(remaining);
    setSelectedId(remaining[0]?.id ?? null);
    saveSchemes(remaining);
    setNotice("Deleted the configuration from this browser.");
  }

  function addQuestion() {
    const questionId = getNextQuestionId(schemes);
    updateSelected((scheme) => ({
      ...scheme,
      questions: [
        ...scheme.questions,
        {
          question_id: questionId,
          question_text: "",
          is_required: true,
        },
      ],
    }));
  }

  function updateQuestion(questionId, patch) {
    updateSelected((scheme) => ({
      ...scheme,
      questions: scheme.questions.map((question) =>
        question.question_id === questionId
          ? { ...question, ...patch }
          : question,
      ),
    }));
  }

  function removeQuestion(questionId) {
    updateSelected((scheme) => ({
      ...scheme,
      questions: scheme.questions.filter(
        (question) => question.question_id !== questionId,
      ),
    }));
  }

  function saveConfiguration(event) {
    event.preventDefault();
    if (!selectedScheme?.name.trim()) {
      setNotice("The FAS name is required.");
      return;
    }
    if (
      selectedScheme.questions.some(
        (question) => !question.question_text.trim(),
      )
    ) {
      setNotice("Please enter content for every question.");
      return;
    }

    saveSchemes(schemes);
    setNotice("Saved the configuration in this browser.");
  }

  return (
    <div className="page-shell">
      <TopNav current="config" />
      <main className="page-content">
        <SiteHeader
          eyebrow="Admin workspace"
          title="Configure FAS Open Questions"
          description="Create additional questions for students to answer when applying. This prototype stores the configuration in localStorage until the .NET integration is available."
          actions={
            <a
              className="button button-primary"
              href={
                selectedScheme
                  ? `/dynamic-fas.html?schemeId=${selectedScheme.id}`
                  : "/dynamic-fas.html"
              }
              onClick={() => saveSchemes(schemes)}
            >
              Open AI Autofill <span aria-hidden="true">→</span>
            </a>
          }
        />

        <div className="config-layout">
          <aside className="scheme-sidebar card">
            <div className="section-heading compact">
              <div>
                <span className="section-kicker">Schemes</span>
                <h2>FAS schemes</h2>
              </div>
              <button
                className="icon-button"
                type="button"
                onClick={addScheme}
                aria-label="Add FAS"
                title="Add FAS"
              >
                +
              </button>
            </div>

            <div className="scheme-list">
              {schemes.map((scheme) => (
                <button
                  key={scheme.id}
                  className={`scheme-item ${scheme.id === selectedId ? "selected" : ""}`}
                  type="button"
                  onClick={() => {
                    setSelectedId(scheme.id);
                    setNotice("");
                  }}
                >
                  <span className="scheme-avatar">F</span>
                  <span>
                    <strong>{scheme.name}</strong>
                    <small>
                      #{scheme.id} · {scheme.questions.length} questions
                    </small>
                  </span>
                </button>
              ))}
              {schemes.length === 0 && (
                <div className="empty-small">
                  No FAS configured. Select + to create one.
                </div>
              )}
            </div>
          </aside>

          <section className="config-editor card">
            {!selectedScheme ? (
              <div className="empty-state">
                <div className="empty-icon">＋</div>
                <h2>Create your first FAS</h2>
                <p>Start by adding a scheme and its open questions.</p>
                <button className="button button-primary" onClick={addScheme}>
                  Add FAS
                </button>
              </div>
            ) : (
              <form onSubmit={saveConfiguration}>
                <div className="editor-toolbar">
                  <div>
                    <span className="section-kicker">Scheme #{selectedScheme.id}</span>
                    <h2>Configuration details</h2>
                  </div>
                  <button
                    className="button button-danger-ghost"
                    type="button"
                    onClick={deleteScheme}
                  >
                    Delete FAS
                  </button>
                </div>

                <label className="field-label" htmlFor="scheme-name">
                  FAS name
                </label>
                <input
                  id="scheme-name"
                  className="text-input"
                  value={selectedScheme.name}
                  maxLength={150}
                  onChange={(event) =>
                    updateSelected((scheme) => ({
                      ...scheme,
                      name: event.target.value,
                    }))
                  }
                />

                <div className="questions-header">
                  <div>
                    <span className="section-kicker">Additional questions</span>
                    <h2>Additional questions</h2>
                    <p>AI may only suggest answers for the questions below.</p>
                  </div>
                  <button
                    className="button button-secondary"
                    type="button"
                    onClick={addQuestion}
                  >
                    + Add question
                  </button>
                </div>

                <div className="question-editor-list">
                  {selectedScheme.questions.map((question, index) => (
                    <article className="question-editor" key={question.question_id}>
                      <div className="question-number">{index + 1}</div>
                      <div className="question-fields">
                        <div className="question-meta-row">
                          <span>ID: {question.question_id}</span>
                          <label className="switch-label">
                            <input
                              type="checkbox"
                              checked={question.is_required}
                              onChange={(event) =>
                                updateQuestion(question.question_id, {
                                  is_required: event.target.checked,
                                })
                              }
                            />
                            <span className="switch" aria-hidden="true" />
                            Required
                          </label>
                        </div>
                        <textarea
                          aria-label={`Question ${index + 1} content`}
                          value={question.question_text}
                          maxLength={500}
                          placeholder="Enter the question shown to the student..."
                          onChange={(event) =>
                            updateQuestion(question.question_id, {
                              question_text: event.target.value,
                            })
                          }
                        />
                        <small>{question.question_text.length}/500 characters</small>
                      </div>
                      <button
                        className="remove-button"
                        type="button"
                        onClick={() => removeQuestion(question.question_id)}
                        aria-label={`Remove question ${index + 1}`}
                        title="Remove question"
                      >
                        ×
                      </button>
                    </article>
                  ))}

                  {selectedScheme.questions.length === 0 && (
                    <div className="questions-empty">
                      No additional questions yet. There is nothing for AI to assist with.
                    </div>
                  )}
                </div>

                {notice && (
                  <div
                    className={`notice ${notice.startsWith("Saved") || notice.startsWith("Deleted") ? "success" : "warning"}`}
                    role="status"
                  >
                    {notice}
                  </div>
                )}

                <div className="form-actions">
                  <span>This configuration is stored only in the current browser.</span>
                  <button className="button button-primary" type="submit">
                    Save configuration
                  </button>
                </div>
              </form>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
