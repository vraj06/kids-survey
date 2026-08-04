import { useState } from "react";

const API_URL = `${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/submit-survey`;

const SUBJECT_OPTIONS = [
  "Math",
  "Reading",
  "Science",
  "Art",
  "Coding",
  "Music",
];

const LEARNING_STYLES = [
  { value: "visual", label: "Watching videos", emoji: "🎬" },
  { value: "handson", label: "Games & activities", emoji: "🧩" },
  { value: "reading", label: "Reading stories", emoji: "📖" },
  { value: "audio", label: "Listening along", emoji: "🎧" },
];

const initialForm = {
  parentName: "",
  parentEmail: "",
  childName: "",
  childAge: "",
  grade: "",
  subjects: [],
  learningStyle: "",
  screenTime: "",
  rating: 0,
  recommend: "",
  feedback: "",
};

// fields that count toward the sticker progress tracker
const TRACKED_FIELDS = [
  "parentName",
  "parentEmail",
  "childName",
  "childAge",
  "grade",
  "subjects",
  "learningStyle",
  "rating",
  "recommend",
];

function App() {
  const [form, setForm] = useState(initialForm);
  const [status, setStatus] = useState("idle"); // idle | sending | success | error
  const [errorMsg, setErrorMsg] = useState("");

  const filledCount = TRACKED_FIELDS.filter((key) => {
    const value = form[key];
    if (Array.isArray(value)) return value.length > 0;
    return value !== "" && value !== 0;
  }).length;

  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const toggleSubject = (subject) => {
    setForm((prev) => {
      const has = prev.subjects.includes(subject);
      return {
        ...prev,
        subjects: has
          ? prev.subjects.filter((s) => s !== subject)
          : [...prev.subjects, subject],
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("sending");
    setErrorMsg("");

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000); // give up after 25s

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.message || "Something went wrong");
      }
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMsg(
        err.name === "AbortError"
          ? "The server took too long to respond. If it's on a free hosting tier it may have been asleep — please try again."
          : err.message
      );
    } finally {
      clearTimeout(timeoutId);
    }
  };

  if (status === "success") {
    return (
      <div className="page">
        <div className="card success-card">
          <div className="success-badge">🌟</div>
          <h1>Yay, all done!</h1>
          <p>
            Thanks for sharing! We've emailed your answers and can't wait to
            make learning even more fun.
          </p>
          <button
            className="btn primary"
            onClick={() => {
              setForm(initialForm);
              setStatus("idle");
            }}
          >
            Fill it out again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="blob blob-1" />
      <div className="blob blob-2" />
      <div className="blob blob-3" />

      <div className="card">
        <header className="header">
          <div className="header-emoji">🚀</div>
          <h1>Little Learners Check-In</h1>
          <p className="subtitle">
            Tell us how your child is enjoying their learning adventure!
          </p>
        </header>

        <div className="progress-track" aria-label="Form progress">
          {TRACKED_FIELDS.map((_, i) => (
            <span
              key={i}
              className={`progress-star ${i < filledCount ? "filled" : ""}`}
            >
              ⭐
            </span>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="form">
          <section className="section">
            <h2>👋 About you</h2>
            <div className="field-row">
              <label className="field">
                <span>Your name</span>
                <input
                  type="text"
                  required
                  value={form.parentName}
                  onChange={(e) => update("parentName", e.target.value)}
                  placeholder="Priya Shah"
                />
              </label>
              <label className="field">
                <span>Your email</span>
                <input
                  type="email"
                  required
                  value={form.parentEmail}
                  onChange={(e) => update("parentEmail", e.target.value)}
                  placeholder="priya@example.com"
                />
              </label>
            </div>
          </section>

          <section className="section">
            <h2>🧒 About your child</h2>
            <div className="field-row">
              <label className="field">
                <span>Child's name</span>
                <input
                  type="text"
                  required
                  value={form.childName}
                  onChange={(e) => update("childName", e.target.value)}
                  placeholder="Aarav"
                />
              </label>
              <label className="field small">
                <span>Age</span>
                <input
                  type="number"
                  min="2"
                  max="18"
                  value={form.childAge}
                  onChange={(e) => update("childAge", e.target.value)}
                  placeholder="7"
                />
              </label>
              <label className="field small">
                <span>Grade</span>
                <input
                  type="text"
                  value={form.grade}
                  onChange={(e) => update("grade", e.target.value)}
                  placeholder="2nd"
                />
              </label>
            </div>
          </section>

          <section className="section">
            <h2>📚 Favorite subjects</h2>
            <div className="chip-group">
              {SUBJECT_OPTIONS.map((subject) => (
                <button
                  type="button"
                  key={subject}
                  className={`chip ${form.subjects.includes(subject) ? "active" : ""}`}
                  onClick={() => toggleSubject(subject)}
                >
                  {subject}
                </button>
              ))}
            </div>
          </section>

          <section className="section">
            <h2>🎨 How does your child like to learn?</h2>
            <div className="style-grid">
              {LEARNING_STYLES.map((style) => (
                <label
                  key={style.value}
                  className={`style-card ${form.learningStyle === style.value ? "active" : ""}`}
                >
                  <input
                    type="radio"
                    name="learningStyle"
                    value={style.value}
                    checked={form.learningStyle === style.value}
                    onChange={(e) => update("learningStyle", e.target.value)}
                  />
                  <span className="style-emoji">{style.emoji}</span>
                  <span>{style.label}</span>
                </label>
              ))}
            </div>
          </section>

          <section className="section">
            <h2>⏱️ Daily learning time</h2>
            <select
              value={form.screenTime}
              onChange={(e) => update("screenTime", e.target.value)}
            >
              <option value="">Choose one</option>
              <option value="Under 30 minutes">Under 30 minutes</option>
              <option value="30-60 minutes">30-60 minutes</option>
              <option value="1-2 hours">1-2 hours</option>
              <option value="More than 2 hours">More than 2 hours</option>
            </select>
          </section>

          <section className="section">
            <h2>⭐ How much does your child enjoy it?</h2>
            <div className="rating-row">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  type="button"
                  key={n}
                  className={`rating-star ${n <= form.rating ? "filled" : ""}`}
                  onClick={() => update("rating", n)}
                  aria-label={`${n} star${n > 1 ? "s" : ""}`}
                >
                  ⭐
                </button>
              ))}
            </div>
          </section>

          <section className="section">
            <h2>💬 Would you recommend us to other parents?</h2>
            <div className="toggle-row">
              <button
                type="button"
                className={`toggle-btn ${form.recommend === "Yes" ? "active" : ""}`}
                onClick={() => update("recommend", "Yes")}
              >
                Yes 🙌
              </button>
              <button
                type="button"
                className={`toggle-btn ${form.recommend === "No" ? "active" : ""}`}
                onClick={() => update("recommend", "No")}
              >
                Not yet 🤔
              </button>
            </div>
          </section>

          <section className="section">
            <h2>📝 Anything else you'd like to share?</h2>
            <textarea
              rows={4}
              value={form.feedback}
              onChange={(e) => update("feedback", e.target.value)}
              placeholder="Tell us what's working, or what could be more fun..."
            />
          </section>

          {status === "error" && (
            <p className="error-text">⚠️ {errorMsg}</p>
          )}

          <button className="btn primary submit-btn" type="submit" disabled={status === "sending"}>
            {status === "sending" ? "Sending..." : "Submit survey 🎉"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
