import React from 'react';

export const LiquidGlassProblemSolution: React.FC = () => {
    return (
        <section className="liquid-glass-section problem-solution">
            <div className="section-container">
                <div className="section-header">
                    <h2 className="section-title">
                        <span className="title-gradient">The Challenge We Solve</span>
                    </h2>
                    <p className="section-subtitle">
                        Every AI conversation starts from zero. Until now.
                    </p>
                </div>
                
                <div className="problem-grid">
                    <div className="problem-card liquid-glass layer-1">
                        <div className="card-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="url(#gradient1)" strokeWidth="2">
                                <path d="M9 11H3M21 11h-6M12 3v6M12 15v6M4.22 4.22l4.24 4.24M15.54 15.54l4.24 4.24M4.22 19.78l4.24-4.24M15.54 8.46l4.24-4.24" />
                            </svg>
                        </div>
                        <h3 className="card-title">Fragmented Context</h3>
                        <p className="card-description">
                            AI assistants forget everything between sessions, forcing you to repeat context endlessly.
                        </p>
                    </div>
                    
                    <div className="problem-card liquid-glass layer-1">
                        <div className="card-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="url(#gradient2)" strokeWidth="2">
                                <circle cx="12" cy="12" r="10" />
                                <path d="M12 6v6l4 2" />
                            </svg>
                        </div>
                        <h3 className="card-title">Lost Progress</h3>
                        <p className="card-description">
                            Valuable insights and decisions from past conversations vanish into the void.
                        </p>
                    </div>
                    
                    <div className="problem-card liquid-glass layer-1">
                        <div className="card-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="url(#gradient3)" strokeWidth="2">
                                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                            </svg>
                        </div>
                        <h3 className="card-title">Siloed Knowledge</h3>
                        <p className="card-description">
                            Each AI platform keeps its memory locked away, preventing cross-platform intelligence.
                        </p>
                    </div>
                </div>
                
                <div className="solution-wrapper">
                    <div className="solution-content liquid-glass layer-2">
                        <h3 className="solution-title">
                            <span className="title-gradient">Enter MemCP</span>
                        </h3>
                        <p className="solution-description">
                            A universal memory layer that persists across all your AI interactions. 
                            Build continuous, context-aware conversations that remember and evolve.
                        </p>
                        <div className="solution-features">
                            <div className="feature-item">
                                <svg className="feature-icon" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9 11H7a5 5 0 0 1 0-10h2m8 0h2a5 5 0 1 1 0 10h-2m-8-5h8" />
                                </svg>
                                <span>Cross-platform memory sync</span>
                            </div>
                            <div className="feature-item">
                                <svg className="feature-icon" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                                </svg>
                                <span>Structured knowledge graphs</span>
                            </div>
                            <div className="feature-item">
                                <svg className="feature-icon" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" />
                                </svg>
                                <span>Privacy-first architecture</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <svg width="0" height="0">
                <defs>
                    <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#409cff" />
                        <stop offset="100%" stopColor="#ba40ff" />
                    </linearGradient>
                    <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#ba40ff" />
                        <stop offset="100%" stopColor="#409cff" />
                    </linearGradient>
                    <linearGradient id="gradient3" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#409cff" />
                        <stop offset="50%" stopColor="#ba40ff" />
                        <stop offset="100%" stopColor="#409cff" />
                    </linearGradient>
                </defs>
            </svg>
            
            <style jsx>{`
                .liquid-glass-section {
                    padding: 120px 40px;
                    position: relative;
                }
                
                .section-container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                
                .section-header {
                    text-align: center;
                    margin-bottom: 80px;
                    animation: fadeInUp 0.8s ease-out;
                }
                
                .section-title {
                    font-size: clamp(36px, 5vw, 56px);
                    font-weight: 700;
                    line-height: 1.2;
                    margin-bottom: 16px;
                }
                
                .title-gradient {
                    background: linear-gradient(135deg, #1d1d1f 0%, #6e6e73 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }
                
                @media (prefers-color-scheme: dark) {
                    .title-gradient {
                        background: linear-gradient(135deg, #f5f5f7 0%, #86868b 100%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                    }
                }
                
                .section-subtitle {
                    font-size: 20px;
                    color: #6e6e73;
                    max-width: 600px;
                    margin: 0 auto;
                    line-height: 1.5;
                }
                
                @media (prefers-color-scheme: dark) {
                    .section-subtitle {
                        color: #86868b;
                    }
                }
                
                .problem-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 32px;
                    margin-bottom: 80px;
                }
                
                .problem-card {
                    padding: 40px;
                    border-radius: 24px;
                    text-align: center;
                    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
                    animation: fadeInUp 0.8s ease-out;
                    animation-fill-mode: both;
                }
                
                .problem-card:nth-child(1) {
                    animation-delay: 0.1s;
                }
                
                .problem-card:nth-child(2) {
                    animation-delay: 0.2s;
                }
                
                .problem-card:nth-child(3) {
                    animation-delay: 0.3s;
                }
                
                .problem-card:hover {
                    transform: translateY(-8px) scale(1.02);
                }
                
                .card-icon {
                    margin-bottom: 24px;
                    display: inline-block;
                    animation: pulse 3s ease-in-out infinite;
                }
                
                .card-title {
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 16px;
                    color: #1d1d1f;
                }
                
                @media (prefers-color-scheme: dark) {
                    .card-title {
                        color: #f5f5f7;
                    }
                }
                
                .card-description {
                    font-size: 16px;
                    line-height: 1.6;
                    color: #6e6e73;
                }
                
                @media (prefers-color-scheme: dark) {
                    .card-description {
                        color: #86868b;
                    }
                }
                
                .solution-wrapper {
                    display: flex;
                    justify-content: center;
                }
                
                .solution-content {
                    max-width: 800px;
                    padding: 60px;
                    border-radius: 32px;
                    text-align: center;
                    animation: morphing 8s ease-in-out infinite;
                }
                
                .solution-title {
                    font-size: 36px;
                    font-weight: 700;
                    margin-bottom: 24px;
                }
                
                .solution-description {
                    font-size: 18px;
                    line-height: 1.6;
                    color: #6e6e73;
                    margin-bottom: 40px;
                }
                
                @media (prefers-color-scheme: dark) {
                    .solution-description {
                        color: #86868b;
                    }
                }
                
                .solution-features {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 24px;
                    justify-content: center;
                }
                
                .feature-item {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px 24px;
                    background: rgba(64, 156, 255, 0.1);
                    border-radius: 100px;
                    font-size: 15px;
                    color: #409cff;
                    transition: all 0.3s ease;
                }
                
                .feature-item:hover {
                    background: rgba(64, 156, 255, 0.2);
                    transform: scale(1.05);
                }
                
                .feature-icon {
                    width: 20px;
                    height: 20px;
                }
                
                @media (max-width: 768px) {
                    .liquid-glass-section {
                        padding: 80px 20px;
                    }
                    
                    .problem-card,
                    .solution-content {
                        padding: 32px 24px;
                    }
                    
                    .solution-features {
                        flex-direction: column;
                        align-items: center;
                    }
                }
            `}</style>
        </section>
    );
};

export const LiquidGlassHowItWorks: React.FC = () => {
    return (
        <section className="liquid-glass-section how-it-works">
            <div className="section-container">
                <div className="section-header">
                    <h2 className="section-title">
                        <span className="title-gradient">How It Works</span>
                    </h2>
                    <p className="section-subtitle">
                        Three simple steps to persistent AI memory
                    </p>
                </div>
                
                <div className="steps-container">
                    <div className="step-card liquid-glass layer-1">
                        <div className="step-number liquid-glass">1</div>
                        <h3 className="step-title">Connect Your AI</h3>
                        <p className="step-description">
                            Install our MCP server or use our API to connect your favorite AI platforms.
                        </p>
                    </div>
                    
                    <div className="step-connector"></div>
                    
                    <div className="step-card liquid-glass layer-1">
                        <div className="step-number liquid-glass">2</div>
                        <h3 className="step-title">Build Knowledge</h3>
                        <p className="step-description">
                            Every conversation automatically builds your personal knowledge graph.
                        </p>
                    </div>
                    
                    <div className="step-connector"></div>
                    
                    <div className="step-card liquid-glass layer-1">
                        <div className="step-number liquid-glass">3</div>
                        <h3 className="step-title">Access Anywhere</h3>
                        <p className="step-description">
                            Your AI remembers everything across all platforms and sessions.
                        </p>
                    </div>
                </div>
            </div>
            
            <style jsx>{`
                .how-it-works {
                    background: rgba(64, 156, 255, 0.05);
                }
                
                .steps-container {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 24px;
                    position: relative;
                }
                
                .step-card {
                    flex: 1;
                    max-width: 320px;
                    padding: 48px 32px;
                    border-radius: 24px;
                    text-align: center;
                    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
                    animation: fadeInUp 0.8s ease-out;
                    animation-fill-mode: both;
                }
                
                .step-card:nth-child(1) {
                    animation-delay: 0.1s;
                }
                
                .step-card:nth-child(3) {
                    animation-delay: 0.2s;
                }
                
                .step-card:nth-child(5) {
                    animation-delay: 0.3s;
                }
                
                .step-card:hover {
                    transform: translateY(-8px) scale(1.05);
                }
                
                .step-number {
                    width: 64px;
                    height: 64px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 24px;
                    font-size: 28px;
                    font-weight: 700;
                    background: linear-gradient(135deg, #409cff 0%, #ba40ff 100%);
                    color: white;
                    border-radius: 20px;
                    animation: morphing 6s ease-in-out infinite;
                }
                
                .step-title {
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 16px;
                    color: #1d1d1f;
                }
                
                @media (prefers-color-scheme: dark) {
                    .step-title {
                        color: #f5f5f7;
                    }
                }
                
                .step-description {
                    font-size: 16px;
                    line-height: 1.6;
                    color: #6e6e73;
                }
                
                @media (prefers-color-scheme: dark) {
                    .step-description {
                        color: #86868b;
                    }
                }
                
                .step-connector {
                    width: 60px;
                    height: 2px;
                    background: linear-gradient(90deg, #409cff 0%, #ba40ff 100%);
                    position: relative;
                    overflow: hidden;
                }
                
                .step-connector::after {
                    content: "";
                    position: absolute;
                    top: 0;
                    left: -100%;
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(90deg, transparent 0%, white 50%, transparent 100%);
                    animation: flow 2s linear infinite;
                }
                
                @keyframes flow {
                    to {
                        left: 100%;
                    }
                }
                
                @media (max-width: 768px) {
                    .steps-container {
                        flex-direction: column;
                        gap: 32px;
                    }
                    
                    .step-connector {
                        width: 2px;
                        height: 40px;
                        background: linear-gradient(180deg, #409cff 0%, #ba40ff 100%);
                    }
                    
                    .step-connector::after {
                        animation: flowVertical 2s linear infinite;
                    }
                    
                    @keyframes flowVertical {
                        from {
                            top: -100%;
                            left: 0;
                        }
                        to {
                            top: 100%;
                            left: 0;
                        }
                    }
                }
            `}</style>
        </section>
    );
};

export const LiquidGlassFeatures: React.FC = () => {
    const features = [
        {
            icon: '🧠',
            title: 'Intelligent Memory',
            description: 'Advanced AI algorithms organize and connect your memories automatically.'
        },
        {
            icon: '🔒',
            title: 'Privacy First',
            description: 'Your memories are encrypted and only accessible by you.'
        },
        {
            icon: '⚡',
            title: 'Real-time Sync',
            description: 'Instant synchronization across all connected AI platforms.'
        },
        {
            icon: '🌐',
            title: 'Universal Compatibility',
            description: 'Works with Claude, GPT, Gemini, and more AI assistants.'
        },
        {
            icon: '📊',
            title: 'Visual Knowledge Graph',
            description: 'See and explore your memories as an interactive network.'
        },
        {
            icon: '🚀',
            title: 'API Access',
            description: 'Build custom integrations with our powerful REST API.'
        }
    ];
    
    return (
        <section className="liquid-glass-section features">
            <div className="section-container">
                <div className="section-header">
                    <h2 className="section-title">
                        <span className="title-gradient">Powerful Features</span>
                    </h2>
                    <p className="section-subtitle">
                        Everything you need for persistent AI memory
                    </p>
                </div>
                
                <div className="features-grid">
                    {features.map((feature, index) => (
                        <div key={index} className="feature-card liquid-glass layer-1">
                            <div className="feature-icon">{feature.icon}</div>
                            <h3 className="feature-title">{feature.title}</h3>
                            <p className="feature-description">{feature.description}</p>
                        </div>
                    ))}
                </div>
            </div>
            
            <style jsx>{`
                .features-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                    gap: 32px;
                }
                
                .feature-card {
                    padding: 40px 32px;
                    border-radius: 24px;
                    text-align: center;
                    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
                    animation: fadeInUp 0.8s ease-out;
                    animation-fill-mode: both;
                }
                
                .feature-card:hover {
                    transform: translateY(-8px) scale(1.02);
                }
                
                .feature-icon {
                    font-size: 48px;
                    margin-bottom: 24px;
                    animation: bounce 2s ease-in-out infinite;
                }
                
                @keyframes bounce {
                    0%, 100% {
                        transform: translateY(0);
                    }
                    50% {
                        transform: translateY(-10px);
                    }
                }
                
                .feature-title {
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 16px;
                    color: #1d1d1f;
                }
                
                @media (prefers-color-scheme: dark) {
                    .feature-title {
                        color: #f5f5f7;
                    }
                }
                
                .feature-description {
                    font-size: 16px;
                    line-height: 1.6;
                    color: #6e6e73;
                }
                
                @media (prefers-color-scheme: dark) {
                    .feature-description {
                        color: #86868b;
                    }
                }
            `}</style>
        </section>
    );
};

export const LiquidGlassGetStarted: React.FC = () => {
    return (
        <section className="liquid-glass-section get-started">
            <div className="section-container">
                <div className="cta-card liquid-glass layer-3">
                    <h2 className="cta-title">
                        <span className="title-gradient">Ready to Give Your AI Memory?</span>
                    </h2>
                    <p className="cta-description">
                        Join thousands of users building smarter AI conversations.
                    </p>
                    <div className="cta-actions">
                        <button className="cta-btn primary-btn liquid-glass">
                            <span>Start Free Trial</span>
                            <svg className="btn-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M5 12h14M12 5l7 7-7 7" />
                            </svg>
                        </button>
                        <button className="cta-btn secondary-btn liquid-glass">
                            <span>View Documentation</span>
                        </button>
                    </div>
                    <p className="cta-note">No credit card required • 14-day free trial</p>
                </div>
            </div>
            
            <style jsx>{`
                .get-started {
                    padding-bottom: 160px;
                }
                
                .cta-card {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 80px 60px;
                    border-radius: 32px;
                    text-align: center;
                    background: linear-gradient(135deg, rgba(64, 156, 255, 0.1) 0%, rgba(186, 64, 255, 0.1) 100%);
                    animation: morphing 10s ease-in-out infinite;
                }
                
                .cta-title {
                    font-size: clamp(36px, 5vw, 48px);
                    font-weight: 700;
                    line-height: 1.2;
                    margin-bottom: 24px;
                }
                
                .cta-description {
                    font-size: 20px;
                    line-height: 1.5;
                    color: #6e6e73;
                    margin-bottom: 48px;
                }
                
                @media (prefers-color-scheme: dark) {
                    .cta-description {
                        color: #86868b;
                    }
                }
                
                .cta-actions {
                    display: flex;
                    gap: 20px;
                    justify-content: center;
                    margin-bottom: 24px;
                }
                
                .cta-btn {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 16px 32px;
                    border: none;
                    border-radius: 16px;
                    font-size: 17px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
                }
                
                .primary-btn {
                    background: linear-gradient(135deg, #409cff 0%, #ba40ff 100%);
                    color: white;
                }
                
                .primary-btn:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 12px 32px rgba(64, 156, 255, 0.4);
                }
                
                .secondary-btn {
                    background: rgba(255, 255, 255, 0.3);
                    color: #1d1d1f;
                    border: 1px solid rgba(255, 255, 255, 0.4);
                }
                
                @media (prefers-color-scheme: dark) {
                    .secondary-btn {
                        background: rgba(255, 255, 255, 0.1);
                        color: #f5f5f7;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    }
                }
                
                .secondary-btn:hover {
                    transform: translateY(-3px);
                    background: rgba(255, 255, 255, 0.5);
                    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
                }
                
                .btn-icon {
                    transition: transform 0.3s ease;
                }
                
                .cta-btn:hover .btn-icon {
                    transform: translateX(4px);
                }
                
                .cta-note {
                    font-size: 14px;
                    color: #6e6e73;
                }
                
                @media (prefers-color-scheme: dark) {
                    .cta-note {
                        color: #86868b;
                    }
                }
                
                @media (max-width: 768px) {
                    .cta-card {
                        padding: 60px 32px;
                    }
                    
                    .cta-actions {
                        flex-direction: column;
                        align-items: center;
                    }
                }
            `}</style>
        </section>
    );
};