import { type FC } from "react";
import { RefreshCw, FileText, Share } from "lucide-react";

const problems = [
    {
        icon: RefreshCw,
        text: "Tired of repeating yourself to every new AI?",
    },
    {
        icon: FileText,
        text: "Your chat history is trapped in silos.",
    },
];

const solution = {
    icon: Share,
    title: "The Solution",
    description:
        "MemCP provides a universal context layer for your AI interactions. Carry your conversation history across any platform.",
};

export const ProblemSolution: FC = () => {
    return (
        <div className="py-24 sm:py-32">
            <div className="mx-auto max-w-7xl px-6 lg:px-8">
                <div className="grid grid-cols-1 gap-x-8 gap-y-16 sm:gap-y-20 lg:grid-cols-2 lg:items-start">
                    <div className="px-6 lg:px-0 lg:pr-4 lg:pt-4">
                        <div className="mx-auto max-w-2xl lg:mx-0 lg:max-w-lg">
                            <h2 className="text-base font-semibold leading-7 text-indigo-400">The Problem</h2>
                            <div className="mt-10 space-y-8">
                                {problems.map((problem, index) => (
                                    <div key={index} className="flex items-center gap-x-3">
                                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gray-800">
                                            <problem.icon
                                                className="h-6 w-6 text-white"
                                                aria-hidden="true"
                                            />
                                        </div>
                                        <p className="text-lg leading-7 text-gray-300">{problem.text}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                    <div className="px-6 lg:px-0 lg:pl-4 lg:pt-4">
                        <div className="mx-auto max-w-2xl lg:mx-0 lg:max-w-lg">
                            <h2 className="text-base font-semibold leading-7 text-indigo-400">{solution.title}</h2>
                            <p className="mt-6 text-lg leading-8 text-gray-300">
                                {solution.description}
                            </p>
                            <div className="mt-10 flex items-center justify-center rounded-lg bg-gray-800 p-8">
                                <solution.icon className="h-16 w-16 text-white" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}; 