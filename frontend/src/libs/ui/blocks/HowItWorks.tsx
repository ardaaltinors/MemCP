import { type FC } from "react";
import { User, Link } from "lucide-react";
import ClaudeIcon from "@static/icons/claude.svg?react";

const steps = [
    {
        name: "Login to MemCP",
        icon: User,
    },
    {
        name: "Get Your MCP Connection URL",
        icon: Link,
    },
    {
        name: "Connect Your Agents",
        icon: ClaudeIcon,
    },
];

export const HowItWorks: FC = () => {
    return (
        <div className="py-24 sm:py-32">
            <div className="mx-auto max-w-7xl px-6 lg:px-8">
                <div className="mx-auto max-w-2xl text-center">
                    <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                        How It Works
                    </h2>
                </div>
                <div className="mt-16">
                    <ol className="relative grid grid-cols-1 gap-x-8 gap-y-10 lg:grid-cols-3">
                        {steps.map((step, stepIdx) => (
                            <li key={step.name} className="flex flex-col items-center text-center relative">
                                {/* Connection line to next step */}
                                {stepIdx < steps.length - 1 && (
                                    <div className="hidden lg:block absolute top-6 left-1/2 w-full h-0.5 bg-gradient-to-r from-gray-600 to-gray-700 transform translate-x-4 z-0" />
                                )}
                                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-800 ring-1 ring-white/10 relative z-10">
                                    <step.icon className="h-6 w-6 text-white" aria-hidden="true" />
                                </div>
                                <p className="mt-4 text-lg font-medium text-white">{step.name}</p>
                            </li>
                        ))}
                    </ol>
                </div>
                <div className="mt-16 flex justify-center">
                    <div className="relative rounded-full px-4 py-1.5 text-sm leading-6 text-gray-300 ring-1 ring-white/10 hover:ring-white/20">
                        <span className="font-mono">mcp.memcp.com/mcp/YOUR_API_KEY</span>
                    </div>
                </div>
            </div>
        </div>
    );
}; 