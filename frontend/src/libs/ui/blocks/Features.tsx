import { type FC } from "react";
import { GitMerge, BrainCircuit, Code, Lock } from "lucide-react";

const features = [
    {
        name: "Tree Portability",
        description:
            "Your AI will remember your conversations and preferences.",
        icon: GitMerge,
    },
    {
        name: "Long-Term Memory",
        description: "Your conversation data is secure and under your control.",
        icon: BrainCircuit,
    },
    {
        name: "Developer-Friendly API",
        description:
            "Simple to integrate with any platform with our clear documentation.",
        icon: Code,
    },
    {
        name: "Secure & Private",
        description:
            "Move between AI providers without losing your conversation history.",
        icon: Lock,
    },
];

export const Features: FC = () => {
    return (
        <div className="py-24 sm:py-32">
            <div className="mx-auto max-w-7xl px-6 lg:px-8">
                <div className="mx-auto max-w-2xl lg:text-center">
                    <h2 className="text-base font-semibold leading-7 text-indigo-400">Features</h2>
                    <p className="mt-2 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                        Everything you need to manage your AI conversations
                    </p>
                </div>
                <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
                    <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-4">
                        {features.map((feature) => (
                            <div key={feature.name} className="flex flex-col">
                                <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-white">
                                    <feature.icon className="h-5 w-5 flex-none text-indigo-400" aria-hidden="true" />
                                    {feature.name}
                                </dt>
                                <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-300">
                                    <p className="flex-auto">{feature.description}</p>
                                </dd>
                            </div>
                        ))}
                    </dl>
                </div>
            </div>
        </div>
    );
};
