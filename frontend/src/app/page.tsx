"use client";

import Link from "next/link";
import { ArrowRight, Bot, GitBranch, Github, Shield } from "lucide-react";


export default function Home() {
    return (
        <div className="flex min-h-screen flex-col">


            <main className="flex-1">
                <section className="container mx-auto flex max-w-5xl flex-col items-center gap-8 py-24 text-center md:py-32">
                    <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
                        Translate Technical Work into{" "}
                        <span className="text-primary">Business Value</span>
                    </h1>
                    <p className="max-w-2xl text-lg text-secondary sm:text-xl">
                        Stop invisible work. DevBridge uses AI to automatically translate
                        your commits and pull requests into stakeholder-friendly updates,
                        highlighting the real business impact of engineering efforts.
                    </p>
                    <div className="flex gap-4">
                        <Link
                            href="/chat"
                            className="flex items-center gap-2 rounded-lg bg-primary px-6 py-3 font-medium text-white transition-colors hover:bg-primary-hover"
                        >
                            Start Chatting <ArrowRight className="h-4 w-4" />
                        </Link>
                        <Link
                            href="https://github.com/pedsanches/devbridge"
                            target="_blank"
                            className="flex items-center gap-2 rounded-lg border border-neutral-200 bg-white px-6 py-3 font-medium text-neutral-900 transition-colors hover:bg-neutral-50 dark:border-neutral-800 dark:bg-neutral-900 dark:text-white dark:hover:bg-neutral-800"
                        >
                            <Github className="h-4 w-4" /> Star on GitHub
                        </Link>
                    </div>
                </section>

                <section className="container mx-auto grid max-w-5xl gap-8 px-4 pb-24 md:grid-cols-3">
                    <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-6 dark:border-neutral-800 dark:bg-neutral-900">
                        <Bot className="mb-4 h-8 w-8 text-primary" />
                        <h3 className="mb-2 text-lg font-semibold">AI Translation</h3>
                        <p className="text-secondary">
                            Automatically converts technical jargon (&quot;Refactored API wrapper&quot;)
                            into business value (&quot;Improved system stability for payments&quot;).
                        </p>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-6 dark:border-neutral-800 dark:bg-neutral-900">
                        <Shield className="mb-4 h-8 w-8 text-success" />
                        <h3 className="mb-2 text-lg font-semibold">Privacy First</h3>
                        <p className="text-secondary">
                            Microsoft Presidio integration ensures no PII or sensitive data
                            ever leaves your infrastructure.
                        </p>
                    </div>
                    <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-6 dark:border-neutral-800 dark:bg-neutral-900">
                        <GitBranch className="mb-4 h-8 w-8 text-warning" />
                        <h3 className="mb-2 text-lg font-semibold">Zero Friction</h3>
                        <p className="text-secondary">
                            Works directly with your existing Git workflow. No new tools to
                            learn, just improved visibility.
                        </p>
                    </div>
                </section>
            </main>

            <footer className="border-t border-neutral-200 bg-white py-8 dark:border-neutral-800 dark:bg-neutral-900">
                <div className="container mx-auto flex flex-col items-center justify-between gap-4 px-4 md:flex-row">
                    <p className="text-sm text-secondary">
                        © 2026 DevBridge. MIT License.
                    </p>
                    <div className="flex gap-4">
                        <Link href="#" className="text-secondary hover:text-primary">
                            <Github className="h-5 w-5" />
                        </Link>
                    </div>
                </div>
            </footer>
        </div>
    );
}
