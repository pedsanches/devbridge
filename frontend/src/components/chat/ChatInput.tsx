"use client";

import { Send } from "lucide-react";
import { useState, KeyboardEvent, forwardRef, useImperativeHandle, useRef } from "react";

interface ChatInputProps {
    onSend: (message: string) => void;
    disabled?: boolean;
    placeholder?: string;
}

export interface ChatInputHandle {
    focus: () => void;
    clear: () => void;
}

export const ChatInput = forwardRef<ChatInputHandle, ChatInputProps>(function ChatInput(
    { onSend, disabled = false, placeholder = "Pergunte sobre as atividades do time..." },
    ref
) {
    const [message, setMessage] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useImperativeHandle(ref, () => ({
        focus: () => textareaRef.current?.focus(),
        clear: () => setMessage(""),
    }));

    const handleSend = () => {
        if (message.trim() && !disabled) {
            onSend(message.trim());
            setMessage("");
        }
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
        // Escape to clear
        if (e.key === "Escape") {
            setMessage("");
            textareaRef.current?.blur();
        }
    };

    return (
        <div className="flex items-end gap-2 rounded-2xl border border-neutral-200 bg-white p-2 shadow-sm dark:border-neutral-700 dark:bg-neutral-800">
            <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={disabled}
                placeholder={placeholder}
                rows={1}
                className="max-h-32 min-h-[40px] flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-neutral-400"
                aria-label="Campo de mensagem"
            />
            <button
                onClick={handleSend}
                disabled={disabled || !message.trim()}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary text-white transition-colors hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Enviar mensagem"
            >
                <Send className="h-4 w-4" />
            </button>
        </div>
    );
});
