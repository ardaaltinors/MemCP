import { type FC } from "react";
// The import statement itself is correct
import ArrowRightIcon from "@static/icons/arrow-right.svg";
import { mindmap } from "@static/images";

type HeroProps = {
    title: string;
    description: string;
};

export const Hero: FC<HeroProps> = ({ title, description }) => {
    return (
        <div className="relative isolate overflow-hidden">
            {/* Background Gradient */}
            <div
                className="absolute inset-x-0 top-[-10rem] -z-10 transform-gpu overflow-hidden blur-3xl sm:top-[-20rem]"
                aria-hidden="true"
            >
                <div
                    className="relative left-1/2 -z-10 aspect-[1155/678] w-[36.125rem] max-w-none -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%-40rem)] sm:w-[72.1875rem]"
                    style={{
                        clipPath:
                            "polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)",
                    }}
                />
            </div>

            {/* --- FIX START (Mobile Padding) --- */}
            {/* Increased top padding on mobile from 'pt-24' to 'pt-32' */}
            <div className="mx-auto max-w-7xl px-6 lg:px-8 pt-32 pb-32 sm:pt-40 sm:pb-40 lg:grid lg:grid-cols-2 lg:gap-x-12 items-center">
            {/* --- FIX END (Mobile Padding) --- */}

                {/* Text Content */}
                <div className="text-center lg:text-left">
                    <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl md:text-7xl">
                        {title}
                    </h1>
                    <p className="mt-6 text-lg leading-8 text-gray-200">
                        {description}
                    </p>
                    <div className="mt-10 flex items-center justify-center lg:justify-start gap-x-6">
                        <a
                            href="/register"
                            className="inline-flex items-center gap-x-2 rounded-md bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-lg hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 transition-colors duration-200"
                        >
                            Get Started
                            <img
                                src={ArrowRightIcon.src}
                                alt=""
                                aria-hidden="true"
                                className="h-4 w-4"
                            />
                        </a>
                        <a
                            href="#"
                            className="text-sm font-semibold leading-6 text-white hover:text-gray-300 transition-colors duration-200"
                        >
                            Learn more <span aria-hidden="true">→</span>
                        </a>
                    </div>
                </div>

                {/* Image Content */}
                <div className="mt-16 sm:mt-24 lg:mt-0 hidden lg:flex justify-center">
                    <div className="relative rounded-xl p-2">
                         <img
                            src={mindmap.src}
                            alt="Hero graphic"
                            className="w-full max-w-md lg:max-w-none rounded-md"
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};