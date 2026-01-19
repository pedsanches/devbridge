"use client";

import { Send } from "lucide-react";
import { useState, KeyboardEvent, forwardRef, useImperativeHandle, useRef, useEffect } from "react";

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
    { onSend, disabled = false, placeholder = "Pergunte sobre entregas, riscos ou o foco do time..." },
    ref
) {
    const [message, setMessage] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useImperativeHandle(ref, () => ({
        focus: () => textareaRef.current?.focus(),
        clear: () => setMessage(""),
    }));

    // Auto-resize textarea based on content
    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            // Reset height to auto to get the correct scrollHeight
            textarea.style.height = "auto";
            // Set height to scrollHeight, capped by max-height (128px = 8rem)
            const newHeight = Math.min(textarea.scrollHeight, 128);
            textarea.style.height = `${newHeight}px`;
        }
    }, [message]);

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
        <div className="flex items-end gap-2 rounded-2xl border border-neutral-200 bg-white p-2 shadow-sm transition-all focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20 dark:border-neutral-700 dark:bg-neutral-800 dark:focus-within:border-primary/50">
            <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={disabled}
                placeholder={placeholder}
                rows={1}
                className="min-h-[40px] max-h-32 flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-neutral-400 focus:outline-none"
                aria-label="Campo de mensagem"
            />
            <button
                onClick={handleSend}
                disabled={disabled || !message.trim()}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary text-white transition-all hover:bg-primary-hover hover:scale-105 disabled:opacity-40 disabled:bg-neutral-400 disabled:cursor-not-allowed disabled:hover:scale-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                aria-label="Enviar mensagem"
            >
                <Send className="h-4 w-4" />
            </button>
        </div>
    );
});
