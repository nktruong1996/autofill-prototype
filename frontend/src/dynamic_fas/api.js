// Use the Vite same-origin proxy by default. This also lets one ngrok tunnel
// expose both the React UI and the local Python API without mixed-content or
// localhost-on-the-teammate-machine problems.
const API_URL = import.meta.env.VITE_API_URL || "/api";

async function request(path, options) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let message = `The API returned error ${response.status}`;
    try {
      const data = await response.json();
      message = typeof data.detail === "string" ? data.detail : message;
    } catch {
      // Keep the status-based message when the body is not JSON.
    }
    throw new Error(message);
  }

  return response.json();
}

export function chatWithDynamicFas(payload) {
  return request("/dynamic-fas/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resetDynamicFasSession(sessionId) {
  return request("/dynamic-fas/reset-session", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}
