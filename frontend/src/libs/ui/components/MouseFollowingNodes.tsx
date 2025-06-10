import React, { useEffect, useRef, useState } from 'react';

interface Node {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  targetX: number;
  targetY: number;
  size: number;
  color: string;
  opacity: number;
}

export const MouseFollowingNodes: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0, y: 0 });
  const animationRef = useRef<number>();
  const nodesRef = useRef<Node[]>([]);
  const [isVisible, setIsVisible] = useState(false);

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

    // Initialize nodes
    const nodeCount = 12;
    const colors = [
      'rgba(64, 156, 255, 0.15)',   // Blue
      'rgba(186, 64, 255, 0.15)',    // Purple
      'rgba(16, 185, 129, 0.15)',    // Emerald
      'rgba(251, 113, 133, 0.15)',   // Rose
      'rgba(251, 191, 36, 0.15)',    // Amber
    ];

    nodesRef.current = Array.from({ length: nodeCount }, (_, i) => ({
      id: i,
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: 0,
      vy: 0,
      targetX: Math.random() * canvas.width,
      targetY: Math.random() * canvas.height,
      size: 15 + Math.random() * 25,
      color: colors[Math.floor(Math.random() * colors.length)],
      opacity: 0.1 + Math.random() * 0.2,
    }));

    // Mouse move handler
    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener('mousemove', handleMouseMove);

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw connections between close nodes
      nodesRef.current.forEach((node, i) => {
        nodesRef.current.slice(i + 1).forEach(otherNode => {
          const distance = Math.sqrt(
            Math.pow(node.x - otherNode.x, 2) + Math.pow(node.y - otherNode.y, 2)
          );
          
          if (distance < 120) {
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(otherNode.x, otherNode.y);
            ctx.strokeStyle = `rgba(255, 255, 255, ${0.05 * (1 - distance / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        });
      });

      // Update and draw nodes
      nodesRef.current.forEach(node => {
        // Calculate mouse influence
        const mouseDistance = Math.sqrt(
          Math.pow(mouseRef.current.x - node.x, 2) + 
          Math.pow(mouseRef.current.y - node.y, 2)
        );
        
        const mouseInfluence = Math.max(0, 1 - mouseDistance / 200);
        
        // Update target position based on mouse
        if (mouseInfluence > 0) {
          const angle = Math.atan2(
            mouseRef.current.y - node.y,
            mouseRef.current.x - node.x
          );
          
          // Move away from mouse
          node.targetX = node.x - Math.cos(angle) * 100 * mouseInfluence;
          node.targetY = node.y - Math.sin(angle) * 100 * mouseInfluence;
        } else {
          // Random wandering
          if (Math.random() < 0.02) {
            node.targetX = Math.random() * canvas.width;
            node.targetY = Math.random() * canvas.height;
          }
        }

        // Spring physics
        const dx = node.targetX - node.x;
        const dy = node.targetY - node.y;
        node.vx += dx * 0.02;
        node.vy += dy * 0.02;
        
        // Damping
        node.vx *= 0.95;
        node.vy *= 0.95;
        
        // Update position
        node.x += node.vx;
        node.y += node.vy;
        
        // Keep nodes within bounds
        node.x = Math.max(node.size, Math.min(canvas.width - node.size, node.x));
        node.y = Math.max(node.size, Math.min(canvas.height - node.size, node.y));

        // Draw node with glass effect
        const gradient = ctx.createRadialGradient(
          node.x, node.y, 0,
          node.x, node.y, node.size
        );
        gradient.addColorStop(0, node.color.replace('0.15', '0.2'));
        gradient.addColorStop(1, node.color.replace('0.15', '0.05'));
        
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
        ctx.fillStyle = gradient;
        ctx.fill();
        
        // Glass edge
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.size, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 255, 255, ${node.opacity * 0.3})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    // Start animation after a delay
    setTimeout(() => {
      setIsVisible(true);
      animate();
    }, 500);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      window.removeEventListener('resize', updateCanvasSize);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={`fixed inset-0 pointer-events-none transition-opacity duration-1000 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      style={{ 
        mixBlendMode: 'screen',
        zIndex: -10
      }}
    />
  );
};