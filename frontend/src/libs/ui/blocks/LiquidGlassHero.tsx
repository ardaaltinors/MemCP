import React, { useEffect, useRef } from 'react';

interface LiquidGlassHeroProps {
    title: string;
    description: string;
}

export const LiquidGlassHero: React.FC<LiquidGlassHeroProps> = ({ title, description }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Set canvas size
        const updateCanvasSize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        updateCanvasSize();
        window.addEventListener('resize', updateCanvasSize);

        // Particle system for fluid background
        class Particle {
            x: number;
            y: number;
            size: number;
            speedX: number;
            speedY: number;
            color: string;
            opacity: number;

            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.size = Math.random() * 100 + 50;
                this.speedX = (Math.random() - 0.5) * 0.5;
                this.speedY = (Math.random() - 0.5) * 0.5;
                this.color = Math.random() > 0.5 ? '#409cff' : '#ba40ff';
                this.opacity = Math.random() * 0.3 + 0.1;
            }

            update() {
                this.x += this.speedX;
                this.y += this.speedY;

                if (this.x > canvas.width + this.size) this.x = -this.size;
                if (this.x < -this.size) this.x = canvas.width + this.size;
                if (this.y > canvas.height + this.size) this.y = -this.size;
                if (this.y < -this.size) this.y = canvas.height + this.size;
            }

            draw() {
                if (!ctx) return;
                
                const gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.size);
                gradient.addColorStop(0, this.color + Math.floor(this.opacity * 255).toString(16).padStart(2, '0'));
                gradient.addColorStop(1, this.color + '00');
                
                ctx.fillStyle = gradient;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        const particles: Particle[] = [];
        for (let i = 0; i < 5; i++) {
            particles.push(new Particle());
        }

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            particles.forEach(particle => {
                particle.update();
                particle.draw();
            });
            
            requestAnimationFrame(animate);
        };
        animate();

        return () => {
            window.removeEventListener('resize', updateCanvasSize);
        };
    }, []);

    return (
        <section className="liquid-glass-hero" ref={containerRef}>
            <canvas ref={canvasRef} className="hero-canvas" />
            
            <div className="hero-content">
                <div className="hero-badge liquid-glass">
                    <span className="badge-text">AI Memory Platform</span>
                </div>
                
                <h1 className="hero-title">
                    <span className="title-gradient">{title}</span>
                </h1>
                
                <p className="hero-description">{description}</p>
                
                <div className="hero-actions">
                    <button className="hero-btn primary-btn liquid-glass">
                        <span>Get Started Free</span>
                        <svg className="btn-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                    </button>
                    <button className="hero-btn secondary-btn liquid-glass">
                        <span>Watch Demo</span>
                        <svg className="btn-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M8 5v14l11-7z" />
                        </svg>
                    </button>
                </div>
                
                <div className="hero-stats">
                    <div className="stat-item liquid-glass">
                        <span className="stat-number">10K+</span>
                        <span className="stat-label">Active Users</span>
                    </div>
                    <div className="stat-item liquid-glass">
                        <span className="stat-number">1M+</span>
                        <span className="stat-label">Memories Stored</span>
                    </div>
                    <div className="stat-item liquid-glass">
                        <span className="stat-number">99.9%</span>
                        <span className="stat-label">Uptime</span>
                    </div>
                </div>
            </div>
            
            <div className="hero-visual liquid-glass liquid-glass-morph">
                <div className="visual-content">
                    <div className="memory-nodes">
                        <div className="memory-node node-1"></div>
                        <div className="memory-node node-2"></div>
                        <div className="memory-node node-3"></div>
                        <div className="connection connection-1"></div>
                        <div className="connection connection-2"></div>
                    </div>
                </div>
            </div>
            
            <style jsx>{`
                .liquid-glass-hero {
                    position: relative;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 120px 40px 80px;
                    overflow: hidden;
                }
                
                .hero-canvas {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: -1;
                    opacity: 0.5;
                    filter: blur(100px);
                }
                
                .hero-content {
                    max-width: 1200px;
                    width: 100%;
                    text-align: center;
                    z-index: 1;
                    animation: fadeInUp 1s ease-out;
                }
                
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(30px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                
                .hero-badge {
                    display: inline-flex;
                    align-items: center;
                    padding: 8px 20px;
                    margin-bottom: 24px;
                    background: rgba(255, 255, 255, 0.25);
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                    backdrop-filter: blur(4px);
                    -webkit-backdrop-filter: blur(4px);
                    border-radius: 30px;
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    animation: pulse 3s ease-in-out infinite;
                }
                
                @keyframes pulse {
                    0%, 100% {
                        transform: scale(1);
                    }
                    50% {
                        transform: scale(1.05);
                    }
                }
                
                .badge-text {
                    font-size: 14px;
                    font-weight: 500;
                    background: linear-gradient(135deg, #409cff 0%, #ba40ff 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }
                
                .hero-title {
                    font-size: clamp(48px, 8vw, 80px);
                    font-weight: 700;
                    line-height: 1.1;
                    margin-bottom: 24px;
                    letter-spacing: -0.02em;
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
                
                .hero-description {
                    font-size: 20px;
                    line-height: 1.5;
                    color: #6e6e73;
                    margin-bottom: 48px;
                    max-width: 600px;
                    margin-left: auto;
                    margin-right: auto;
                }
                
                @media (prefers-color-scheme: dark) {
                    .hero-description {
                        color: #86868b;
                    }
                }
                
                .hero-actions {
                    display: flex;
                    gap: 20px;
                    justify-content: center;
                    margin-bottom: 80px;
                }
                
                .hero-btn {
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
                    position: relative;
                    overflow: hidden;
                }
                
                .primary-btn {
                    background: linear-gradient(135deg, rgba(64, 156, 255, 0.85) 0%, rgba(186, 64, 255, 0.85) 100%);
                    box-shadow: 0 8px 32px 0 rgba(64, 156, 255, 0.37);
                    backdrop-filter: blur(4px);
                    -webkit-backdrop-filter: blur(4px);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    color: white;
                }
                
                .primary-btn:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 12px 32px rgba(64, 156, 255, 0.4);
                }
                
                .secondary-btn {
                    background: rgba(255, 255, 255, 0.25);
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                    backdrop-filter: blur(4px);
                    -webkit-backdrop-filter: blur(4px);
                    color: #1d1d1f;
                    border: 1px solid rgba(255, 255, 255, 0.18);
                }
                
                @media (prefers-color-scheme: dark) {
                    .secondary-btn {
                        background: rgba(255, 255, 255, 0.1);
                        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                        backdrop-filter: blur(4px);
                        -webkit-backdrop-filter: blur(4px);
                        color: #f5f5f7;
                        border: 1px solid rgba(255, 255, 255, 0.18);
                    }
                }
                
                .secondary-btn:hover {
                    transform: translateY(-3px);
                    background: rgba(255, 255, 255, 0.35);
                    box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.45);
                }
                
                .btn-icon {
                    transition: transform 0.3s ease;
                }
                
                .hero-btn:hover .btn-icon {
                    transform: translateX(4px);
                }
                
                .hero-stats {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 24px;
                    max-width: 600px;
                    margin: 0 auto 80px;
                }
                
                .stat-item {
                    padding: 24px;
                    background: rgba(255, 255, 255, 0.25);
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                    backdrop-filter: blur(4px);
                    -webkit-backdrop-filter: blur(4px);
                    border-radius: 16px;
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    text-align: center;
                    transition: all 0.3s ease;
                }
                
                .stat-item:hover {
                    transform: translateY(-4px);
                    box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.45);
                    background: rgba(255, 255, 255, 0.35);
                }
                
                .stat-number {
                    display: block;
                    font-size: 32px;
                    font-weight: 700;
                    background: linear-gradient(135deg, #409cff 0%, #ba40ff 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    margin-bottom: 4px;
                }
                
                .stat-label {
                    font-size: 14px;
                    color: #6e6e73;
                }
                
                @media (prefers-color-scheme: dark) {
                    .stat-label {
                        color: #86868b;
                    }
                }
                
                .hero-visual {
                    position: absolute;
                    bottom: -100px;
                    right: -100px;
                    width: 400px;
                    height: 400px;
                    background: rgba(255, 255, 255, 0.25);
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                    backdrop-filter: blur(4px);
                    -webkit-backdrop-filter: blur(4px);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    padding: 40px;
                    opacity: 0.8;
                }
                
                .visual-content {
                    position: relative;
                    width: 100%;
                    height: 100%;
                }
                
                .memory-nodes {
                    position: relative;
                    width: 100%;
                    height: 100%;
                }
                
                .memory-node {
                    position: absolute;
                    width: 60px;
                    height: 60px;
                    background: linear-gradient(135deg, #409cff 0%, #ba40ff 100%);
                    border-radius: 50%;
                    animation: float 6s ease-in-out infinite;
                }
                
                .node-1 {
                    top: 20%;
                    left: 20%;
                    animation-delay: 0s;
                }
                
                .node-2 {
                    top: 60%;
                    right: 30%;
                    animation-delay: 2s;
                }
                
                .node-3 {
                    bottom: 20%;
                    left: 40%;
                    animation-delay: 4s;
                }
                
                @keyframes float {
                    0%, 100% {
                        transform: translateY(0);
                    }
                    50% {
                        transform: translateY(-20px);
                    }
                }
                
                .connection {
                    position: absolute;
                    height: 2px;
                    background: linear-gradient(90deg, #409cff 0%, #ba40ff 100%);
                    opacity: 0.5;
                }
                
                .connection-1 {
                    top: 35%;
                    left: 30%;
                    width: 120px;
                    transform: rotate(30deg);
                }
                
                .connection-2 {
                    top: 60%;
                    left: 40%;
                    width: 100px;
                    transform: rotate(-45deg);
                }
                
                @media (max-width: 768px) {
                    .liquid-glass-hero {
                        padding: 100px 20px 60px;
                    }
                    
                    .hero-actions {
                        flex-direction: column;
                        align-items: center;
                    }
                    
                    .hero-stats {
                        grid-template-columns: 1fr;
                    }
                    
                    .hero-visual {
                        display: none;
                    }
                }
            `}</style>
        </section>
    );
};