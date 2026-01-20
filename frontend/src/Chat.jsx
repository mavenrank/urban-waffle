import React, { useEffect, useRef, useState } from "react";
import {
    FaBolt,
    FaDatabase,
    FaPaperPlane,
    FaRobot,
    FaUser,
} from "react-icons/fa";
import "./Chat.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function Chat() {
    const [messages, setMessages] = useState([
        {
            role: "assistant",
            content:
                "Hello! I am your Pagila Database Assistant. Ask me anything about the movies, actors, or rental data.",
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [models, setModels] = useState([]);
    const [selectedModel, setSelectedModel] = useState(
        "mistralai/mistral-7b-instruct:free"
    );
    const [loadingModels, setLoadingModels] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const fetchModels = async () => {
        setLoadingModels(true);
        try {
            const resp = await fetch(`${API_BASE}/models`);
            if (!resp.ok) throw new Error("Could not load models");
            const data = await resp.json();
            setModels(data.models || []);
            if (data.models?.length) {
                const found = data.models.find((m) => m.id === selectedModel);
                setSelectedModel(found ? found.id : data.models[0].id);
            }
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: "I could not fetch models right now.",
                },
            ]);
        } finally {
            setLoadingModels(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = { role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const resp = await fetch(`${API_BASE}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: userMessage.content,
                    model: selectedModel,
                }),
            });

            if (!resp.ok) {
                const errorData = await resp.json().catch(() => ({}));
                throw new Error(errorData.detail || "Request failed");
            }

            const data = await resp.json();
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: data.response,
                    metadata: data.metadata,
                },
            ]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: `Error: ${err.message}. Please ensure the backend is running on ${API_BASE}.`,
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="chat-shell">
            <header className="chat-header">
                <div className="brand">
                    <div className="brand-icon">
                        <FaDatabase />
                    </div>
                    <div>
                        <p className="eyebrow">Pagila RAG • No LangChain</p>
                        <h1>SQL Copilot</h1>
                    </div>
                </div>
                <div className="controls">
                    {models.length === 0 ? (
                        <button
                            className="ghost"
                            onClick={fetchModels}
                            disabled={loadingModels}
                        >
                            {loadingModels ? "Loading..." : "Load Free Models"}
                        </button>
                    ) : (
                        <select
                            className="select"
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                        >
                            {models.map((m) => (
                                <option key={m.id} value={m.id}>
                                    {m.name || m.id}
                                </option>
                            ))}
                        </select>
                    )}
                    <span className="status-pill">
                        <FaBolt /> No LangChain
                    </span>
                </div>
            </header>

            <main className="chat-body">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`bubble-row ${msg.role}`}>
                        <div className="avatar">
                            {msg.role === "assistant" ? (
                                <FaRobot />
                            ) : (
                                <FaUser />
                            )}
                        </div>
                        <div className="bubble">
                            <div>{msg.content}</div>
                            {msg.metadata && (
                                <div className="meta">
                                    {msg.metadata.model} •{" "}
                                    {msg.metadata.duration}s
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="bubble-row assistant">
                        <div className="avatar">
                            <FaRobot />
                        </div>
                        <div className="bubble">Thinking…</div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </main>

            <form className="chat-input" onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask about films, actors, rentals…"
                    disabled={isLoading}
                />
                <button type="submit" disabled={isLoading || !input.trim()}>
                    <FaPaperPlane />
                </button>
            </form>
        </div>
    );
}

export default Chat;
