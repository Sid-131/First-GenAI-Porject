// frontend/src/main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/index.css";

// Error boundary to catch render crashes and show them instead of a blank screen
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { error: null };
    }
    static getDerivedStateFromError(error) {
        return { error };
    }
    render() {
        if (this.state.error) {
            return (
                <div style={{
                    fontFamily: "monospace", background: "#0f0f0f", color: "#f87171",
                    minHeight: "100vh", display: "flex", flexDirection: "column",
                    alignItems: "center", justifyContent: "center", padding: "2rem", gap: "1rem"
                }}>
                    <div style={{ fontSize: "2rem" }}>💥 React crashed</div>
                    <pre style={{
                        background: "#1c1c1c", padding: "1rem", borderRadius: "8px",
                        maxWidth: "720px", overflowX: "auto", color: "#fca5a5",
                        fontSize: "0.8rem", whiteSpace: "pre-wrap"
                    }}>
                        {String(this.state.error)}
                    </pre>
                    <button
                        onClick={() => this.setState({ error: null })}
                        style={{
                            background: "#dc2626", color: "#fff", border: "none",
                            padding: "0.5rem 1.5rem", borderRadius: "8px", cursor: "pointer"
                        }}
                    >
                        Retry
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}

ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
        <ErrorBoundary>
            <App />
        </ErrorBoundary>
    </React.StrictMode>
);
