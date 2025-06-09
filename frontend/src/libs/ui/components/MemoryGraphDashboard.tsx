import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  Position,
  useReactFlow,
  BackgroundVariant,
  ReactFlowProvider,
  Handle,
  type Node,
  type Edge,
  type NodeTypes,
} from '@xyflow/react';
import { getMemoryGraph } from '@libs/api';
import type { ApiMemoryNode, ApiMemoryEdge, CreateMemoryRequest, UpdateMemoryRequest } from '@libs/types';
import { authUtils } from '@libs/utils/auth';

import '@xyflow/react/dist/style.css';

// Memory node data structure
interface MemoryNodeData extends Record<string, unknown> {
  title: string;
  content: string;
  timestamp: string;
  tags: string[];
  isHighlighted?: boolean;
  colorGradient?: string;
  isCenter?: boolean;
}

// Custom Memory Node Component with Apple-like design
const MemoryNode = ({ data, selected }: { data: MemoryNodeData; selected?: boolean }) => {
  const isCenter = data.isCenter;
  const size = isCenter ? 180 : 140;
  const colorGradient = data.colorGradient || 'from-blue-500 to-blue-700';
  
  return (
    <div
      className={`relative group transition-all duration-500 ${
        selected ? 'scale-110 z-20' : 'hover:scale-105'
      }`}
      style={{ width: `${size}px`, height: `${size}px` }}
    >
      {/* Glow effect */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${colorGradient} rounded-2xl blur-xl opacity-60 animate-pulse`}
        style={{ transform: 'scale(1.2)' }}
      />
      
      {/* Main node */}
      <div
        className={`relative w-full h-full bg-gradient-to-br ${colorGradient} rounded-2xl border-2 ${
          selected ? 'border-white' : 'border-gray-700'
        } shadow-2xl flex items-center justify-center transition-all duration-300 cursor-pointer hover:shadow-3xl`}
      >
        {/* Handles */}
        <Handle type="target" position={Position.Left} className="opacity-0" />
        <Handle type="source" position={Position.Right} className="opacity-0" />
        
        {/* Node content */}
        <div className="text-center p-6 w-full h-full flex flex-col items-center justify-center">
          {isCenter && (
            <svg className="w-8 h-8 text-white/80 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          )}
          <div className={`text-white font-semibold ${isCenter ? 'text-xl' : 'text-base'} leading-tight break-words max-w-full`}>
            {data.title}
          </div>
        </div>
      </div>
    </div>
  );
};

// Transform API data to React Flow format with enhanced clustering algorithm
const transformApiDataToReactFlow = (
  apiNodes: ApiMemoryNode[], 
  apiEdges: ApiMemoryEdge[]
): { nodes: Node<MemoryNodeData>[]; edges: Edge[] } => {
  // Use clustering algorithm to group related nodes while maintaining organic distribution
  const nodeSize = 100;
  const centerNodeSize = 180;
  const minDistance = 200; // Reduced for better connectivity visualization
  const connectedNodeDistance = 120; // Specific distance for directly connected nodes
  const canvasWidth = 2200;
  const canvasHeight = 2000;
  const padding = nodeSize * 1.5;
  
  // Build connection map from edges
  const connectionMap = new Map<string, Set<string>>();
  apiEdges.forEach(edge => {
    const sourceConnections = connectionMap.get(edge.source) || new Set();
    const targetConnections = connectionMap.get(edge.target) || new Set();
    
    sourceConnections.add(edge.target);
    targetConnections.add(edge.source);
    
    connectionMap.set(edge.source, sourceConnections);
    connectionMap.set(edge.target, targetConnections);
  });
  
  // Find connected components (clusters of related nodes)
  const findConnectedComponents = (nodeIds: string[]): string[][] => {
    const visited = new Set<string>();
    const components: string[][] = [];
    
    nodeIds.forEach(nodeId => {
      if (!visited.has(nodeId)) {
        const component: string[] = [];
        const stack = [nodeId];
        
        while (stack.length > 0) {
          const current = stack.pop()!;
          if (!visited.has(current)) {
            visited.add(current);
            component.push(current);
            
            const connections = connectionMap.get(current) || new Set();
            connections.forEach(connectedId => {
              if (!visited.has(connectedId)) {
                stack.push(connectedId);
              }
            });
          }
        }
        
        components.push(component);
      }
    });
    
    return components;
  };
  
  // Helper function to check if two positions are too close
  const isTooClose = (x1: number, y1: number, x2: number, y2: number, minDist: number): boolean => {
    const distance = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
    return distance < minDist;
  };
  
  // Helper function to find position for connected nodes
  const findConnectedNodePosition = (
    targetNodeId: string,
    existingPositions: Map<string, {x: number, y: number}>,
    allPositions: Array<{x: number, y: number}>,
    maxAttempts = 30
  ): {x: number, y: number} => {
    const connections = connectionMap.get(targetNodeId) || new Set();
    const connectedPositions = Array.from(connections)
      .map(id => existingPositions.get(id))
      .filter(pos => pos !== undefined);
    
    if (connectedPositions.length === 0) {
      // No connected nodes positioned yet, use cluster center approach
      return findClusterPosition(
        { x: canvasWidth / 2, y: canvasHeight / 2 }, 
        300, 
        allPositions, 
        maxAttempts
      );
    }
    
    // Calculate centroid of connected nodes
    const centroid = connectedPositions.reduce(
      (acc, pos) => ({ x: acc.x + pos.x, y: acc.y + pos.y }),
      { x: 0, y: 0 }
    );
    centroid.x /= connectedPositions.length;
    centroid.y /= connectedPositions.length;
    
    // Try to place node near the centroid of its connections
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const angle = Math.random() * Math.PI * 2;
      const distance = connectedNodeDistance + Math.random() * 60; // Small variation
      const x = centroid.x + Math.cos(angle) * distance;
      const y = centroid.y + Math.sin(angle) * distance;
      
      const boundedX = Math.max(padding, Math.min(canvasWidth - padding, x));
      const boundedY = Math.max(padding, Math.min(canvasHeight - padding, y));
      
      const isValid = allPositions.every(pos => 
        !isTooClose(boundedX, boundedY, pos.x, pos.y, minDistance)
      );
      
      if (isValid) {
        return { x: boundedX, y: boundedY };
      }
    }
    
    // Fallback to cluster positioning
    return findClusterPosition(centroid, 200, allPositions, maxAttempts);
  };

  // Helper function to find position within a cluster area with improved spacing
  const findClusterPosition = (
    clusterCenter: {x: number, y: number}, 
    clusterRadius: number, 
    existingPositions: Array<{x: number, y: number}>,
    maxAttempts = 30
  ): {x: number, y: number} => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      // Generate position within cluster area
      const angle = Math.random() * Math.PI * 2;
      const distance = Math.random() * clusterRadius;
      const x = clusterCenter.x + Math.cos(angle) * distance;
      const y = clusterCenter.y + Math.sin(angle) * distance;
      
      // Ensure position is within canvas bounds
      const boundedX = Math.max(padding, Math.min(canvasWidth - padding, x));
      const boundedY = Math.max(padding, Math.min(canvasHeight - padding, y));
      
      // Check if position is valid (not too close to existing nodes)
      const isValid = existingPositions.every(pos => 
        !isTooClose(boundedX, boundedY, pos.x, pos.y, minDistance)
      );
      
      if (isValid) {
        return { x: boundedX, y: boundedY };
      }
    }
    
    // Fallback: spiral outward from cluster center
    for (let radius = 50; radius <= clusterRadius * 1.5; radius += 40) {
      for (let angle = 0; angle < Math.PI * 2; angle += Math.PI / 6) {
        const x = clusterCenter.x + Math.cos(angle) * radius;
        const y = clusterCenter.y + Math.sin(angle) * radius;
        
        const boundedX = Math.max(padding, Math.min(canvasWidth - padding, x));
        const boundedY = Math.max(padding, Math.min(canvasHeight - padding, y));
        
        const isValid = existingPositions.every(pos => 
          !isTooClose(boundedX, boundedY, pos.x, pos.y, minDistance)
        );
        
        if (isValid) {
          return { x: boundedX, y: boundedY };
        }
      }
    }
    
    // Final fallback: place randomly within canvas bounds
    const x = padding + Math.random() * (canvasWidth - 2 * padding);
    const y = padding + Math.random() * (canvasHeight - 2 * padding);
    return { x, y };
  };

  // Color palette for different clusters
  const colorPalette = [
    'from-blue-500 to-blue-700',       // Ocean blue
    'from-purple-500 to-purple-700',   // Royal purple
    'from-emerald-500 to-emerald-700', // Emerald green
    'from-rose-500 to-rose-700',       // Rose pink
    'from-amber-500 to-amber-700',     // Golden amber
    'from-cyan-500 to-cyan-700',       // Cyan blue
    'from-indigo-500 to-indigo-700',   // Deep indigo
    'from-teal-500 to-teal-700',       // Teal green
    'from-orange-500 to-orange-700',   // Warm orange
    'from-violet-500 to-violet-700',   // Soft violet
    'from-lime-500 to-lime-700',       // Lime green
    'from-pink-500 to-pink-700',       // Bright pink
    'from-sky-500 to-sky-700',         // Sky blue
    'from-green-500 to-green-700',     // Forest green
    'from-red-500 to-red-700',         // Classic red
  ];

  // Get all node IDs and find connected components
  const nodeIds = apiNodes.map(node => node.id);
  const components = findConnectedComponents(nodeIds);
  
  // Assign colors to components
  const componentColors = components.map((_, index) => 
    colorPalette[index % colorPalette.length]
  );
  
  // Create node-to-component mapping
  const nodeToComponent = new Map<string, number>();
  components.forEach((component, index) => {
    component.forEach(nodeId => {
      nodeToComponent.set(nodeId, index);
    });
  });
  
  // Generate cluster centers with improved spacing algorithm
  const clusterCenters: Array<{x: number, y: number}> = [];
  const usedPositions: Array<{x: number, y: number}> = [];
  const minClusterDistance = 400; // Reduced for better connectivity
  
  // Sort components by size (larger clusters get priority in positioning)
  const sortedComponents = components
    .map((component, index) => ({ component, index }))
    .sort((a, b) => b.component.length - a.component.length);
  
  sortedComponents.forEach(({ component, index }) => {
    let clusterCenter;
    let attempts = 0;
    const maxAttempts = 100;
    
    // For single nodes, use improved random distribution
    if (component.length === 1) {
      do {
        // Use Poisson disk sampling approach for better distribution
        clusterCenter = {
          x: padding + Math.random() * (canvasWidth - 2 * padding),
          y: padding + Math.random() * (canvasHeight - 2 * padding)
        };
        attempts++;
      } while (
        attempts < maxAttempts && 
        usedPositions.some(pos => isTooClose(clusterCenter.x, clusterCenter.y, pos.x, pos.y, minClusterDistance))
      );
      
      // If we couldn't find a position, use systematic grid placement
      if (attempts >= maxAttempts) {
        const gridCols = Math.ceil(Math.sqrt(components.length));
        const gridRow = Math.floor(index / gridCols);
        const gridCol = index % gridCols;
        const cellWidth = (canvasWidth - 2 * padding) / gridCols;
        const cellHeight = (canvasHeight - 2 * padding) / Math.ceil(components.length / gridCols);
        
        clusterCenter = {
          x: padding + cellWidth * (gridCol + 0.5),
          y: padding + cellHeight * (gridRow + 0.5)
        };
      }
    } else {
      // For larger clusters, use strategic positioning with more space
      const clusterRadius = Math.max(300, Math.sqrt(component.length) * 150);
      
      do {
        clusterCenter = {
          x: padding + clusterRadius + Math.random() * (canvasWidth - 2 * padding - 2 * clusterRadius),
          y: padding + clusterRadius + Math.random() * (canvasHeight - 2 * padding - 2 * clusterRadius)
        };
        attempts++;
      } while (
        attempts < maxAttempts && 
        usedPositions.some(pos => isTooClose(clusterCenter.x, clusterCenter.y, pos.x, pos.y, minClusterDistance))
      );
    }
    
    clusterCenters[index] = clusterCenter;
    usedPositions.push(clusterCenter);
  });
  
  // Generate positions for all nodes using connection-aware placement
  const nodePositions: Array<{x: number, y: number}> = [];
  const nodePositionMap = new Map<string, {x: number, y: number}>();
  const nodes: Node<MemoryNodeData>[] = [];
  
  if (apiNodes.length > 0) {
    // Sort nodes by connection count (most connected first) for better placement
    const sortedNodes = [...apiNodes].sort((a, b) => {
      const aConnections = connectionMap.get(a.id)?.size || 0;
      const bConnections = connectionMap.get(b.id)?.size || 0;
      return bConnections - aConnections;
    });
    
    // Process nodes in order of connectivity
    sortedNodes.forEach((node, nodeIndex) => {
      const componentIndex = nodeToComponent.get(node.id) ?? 0;
      const componentSize = components[componentIndex]?.length || 1;
      const connections = connectionMap.get(node.id)?.size || 0;
      
      let position: {x: number, y: number};
      let nodeData: MemoryNodeData;
      
      if (nodeIndex === 0 && sortedNodes.length > 1) {
        // Most connected node becomes the center node
        position = { x: canvasWidth / 2 - centerNodeSize / 2, y: canvasHeight / 2 - centerNodeSize / 2 };
        nodeData = {
          title: node.label,
          content: node.content,
          timestamp: new Date(node.created_at).toISOString(),
          tags: node.tags,
          colorGradient: 'from-purple-600 to-blue-600',
          isCenter: true,
        };
      } else if (connections > 0) {
        // Connected nodes use connection-aware positioning
        position = findConnectedNodePosition(node.id, nodePositionMap, nodePositions);
        nodeData = {
          title: node.label,
          content: node.content,
          timestamp: new Date(node.created_at).toISOString(),
          tags: node.tags,
          colorGradient: componentColors[componentIndex],
        };
      } else {
        // Isolated nodes use cluster positioning
        const clusterCenter = clusterCenters[componentIndex];
        const baseRadius = 150;
        position = findClusterPosition(clusterCenter, baseRadius, nodePositions);
        nodeData = {
          title: node.label,
          content: node.content,
          timestamp: new Date(node.created_at).toISOString(),
          tags: node.tags,
          colorGradient: componentColors[componentIndex],
        };
      }
      
      nodePositions.push(position);
      nodePositionMap.set(node.id, position);
      
      nodes.push({
        id: node.id,
        type: 'memoryNode',
        position: { x: position.x, y: position.y },
        data: nodeData,
        draggable: true,
        selectable: true,
      });
    });
  }

  // Transform edges with enhanced styling
  const edges: Edge[] = apiEdges.map((edge, index) => ({
    id: `edge-${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    type: 'bezier',
    animated: true,
    style: {
      strokeWidth: 10,
      stroke: `rgba(147, 51, 234, ${0.3 + edge.weight * 0.4})`,
      strokeDasharray: '5 5',
    },
  }));

  return { nodes, edges };
};

interface MemoryGraphDashboardInnerProps {
  onNodeSelect?: (node: any) => void;
  onMemoryCreate?: (memory: CreateMemoryRequest) => Promise<void>;
  onMemoryUpdate?: (id: string, memory: UpdateMemoryRequest) => Promise<void>;
  onMemoryDelete?: (id: string) => Promise<void>;
}

// Add Memory Modal Component
const AddMemoryModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (memory: CreateMemoryRequest) => Promise<void>;
}> = ({ isOpen, onClose, onSubmit }) => {
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setIsSubmitting(true);
    try {
      const tagArray = tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
      await onSubmit({ content: content.trim(), tags: tagArray });
      setContent('');
      setTags('');
      onClose();
    } catch (error) {
      console.error('Failed to create memory:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 max-w-lg w-full">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-white">Add New Memory</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Content</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter memory content..."
              className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-colors min-h-[120px]"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Tags (comma-separated)</label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="tag1, tag2, tag3..."
              className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-colors"
            />
          </div>
          
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!content.trim() || isSubmitting}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:scale-105 disabled:opacity-50 disabled:transform-none transition-all"
            >
              {isSubmitting ? 'Creating...' : 'Create Memory'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Update Memory Modal Component
const UpdateMemoryModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (id: string, memory: UpdateMemoryRequest) => Promise<void>;
  memory?: { id: string; title: string; content: string; tags: string[] };
}> = ({ isOpen, onClose, onSubmit, memory }) => {
  const [content, setContent] = useState('');
  const [tags, setTags] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Update form when memory changes
  useEffect(() => {
    if (memory) {
      setContent(memory.content);
      setTags(memory.tags.join(', '));
    }
  }, [memory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!memory || !content.trim()) return;

    setIsSubmitting(true);
    try {
      const tagArray = tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
      await onSubmit(memory.id, { content: content.trim(), tags: tagArray });
      onClose();
    } catch (error) {
      console.error('Failed to update memory:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !memory) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 max-w-lg w-full">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-white">Update Memory</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Content</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter memory content..."
              className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-colors min-h-[120px]"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Tags (comma-separated)</label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="tag1, tag2, tag3..."
              className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-colors"
            />
          </div>
          
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!content.trim() || isSubmitting}
              className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:scale-105 disabled:opacity-50 disabled:transform-none transition-all"
            >
              {isSubmitting ? 'Updating...' : 'Update Memory'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Delete Confirmation Modal Component
const DeleteConfirmModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  memoryTitle?: string;
}> = ({ isOpen, onClose, onConfirm, memoryTitle }) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    setIsDeleting(true);
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      console.error('Failed to delete memory:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-white">Delete Memory</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="mb-6">
          <div className="w-16 h-16 mx-auto mb-4 bg-red-500/20 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </div>
          <p className="text-gray-300 text-center mb-2">
            Are you sure you want to delete this memory?
          </p>
          {memoryTitle && (
            <p className="text-gray-500 text-center text-sm font-medium">
              "{memoryTitle}"
            </p>
          )}
          <p className="text-red-400 text-center text-sm mt-3">
            This action cannot be undone.
          </p>
        </div>
        
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={isDeleting}
            className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium disabled:opacity-50 transition-all"
          >
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
};

function MemoryGraphDashboardInner({ 
  onNodeSelect,
  onMemoryCreate,
  onMemoryUpdate,
  onMemoryDelete,
}: MemoryGraphDashboardInnerProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<Node<MemoryNodeData> | null>(null);
  
  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  
  const { fitView } = useReactFlow();

  // Custom node types
  const nodeTypes: NodeTypes = useMemo(
    () => ({
      memoryNode: ({ data, selected }) => <MemoryNode data={data} selected={selected} />,
    }),
    []
  );

  // Fetch memory graph data
  const fetchMemoryGraph = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const token = authUtils.getToken();
      
      if (!token) {
        setError('Please log in to view your memories');
        return;
      }

      const data = await getMemoryGraph(token);
      
      const { nodes: transformedNodes, edges: transformedEdges } = transformApiDataToReactFlow(
        data.nodes,
        data.edges
      );
      
      setNodes(transformedNodes);
      setEdges(transformedEdges);
      
      // Auto-fit view after loading
      setTimeout(() => fitView({ padding: 0.2, maxZoom: 1.2 }), 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch memory graph');
      console.error('Error fetching memory graph:', err);
    } finally {
      setIsLoading(false);
    }
  }, [setNodes, setEdges, fitView]);

  // Initial load
  useEffect(() => {
    fetchMemoryGraph();
  }, [fetchMemoryGraph]);

  // Handle node clicks
  const onNodeClick = useCallback(
    (_: any, node: Node<MemoryNodeData>) => {
      setSelectedNode(node);
      
      // Notify parent component
      if (onNodeSelect) {
        onNodeSelect({
          id: node.id,
          title: node.data.title,
          content: node.data.content,
          tags: node.data.tags,
          createdAt: node.data.timestamp,
          updatedAt: node.data.timestamp,
        });
      }
      
      // Highlight connected nodes
      const connectedNodeIds = edges
        .filter(edge => edge.source === node.id || edge.target === node.id)
        .flatMap(edge => [edge.source, edge.target])
        .filter(id => id !== node.id);

      setNodes((nodes) =>
        nodes.map((n) => ({
          ...n,
          data: {
            ...n.data,
            isHighlighted: connectedNodeIds.includes(n.id),
          },
        }))
      );
    },
    [edges, setNodes, onNodeSelect]
  );

  // Clear highlights when clicking on background
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setNodes((nodes) =>
      nodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          isHighlighted: false,
        },
      }))
    );
  }, [setNodes]);

  // Handle memory operations with graph refresh
  const handleCreateMemory = async (memory: CreateMemoryRequest) => {
    if (onMemoryCreate) {
      await onMemoryCreate(memory);
      // Refresh the graph after creating
      setTimeout(() => fetchMemoryGraph(), 500);
    }
  };

  const handleUpdateMemory = async (id: string, memory: UpdateMemoryRequest) => {
    if (onMemoryUpdate) {
      await onMemoryUpdate(id, memory);
      // Refresh the graph after updating
      setTimeout(() => fetchMemoryGraph(), 500);
    }
  };

  const handleDeleteMemory = async (id: string) => {
    if (onMemoryDelete) {
      await onMemoryDelete(id);
      setSelectedNode(null);
      // Refresh the graph after deleting
      setTimeout(() => fetchMemoryGraph(), 500);
    }
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-[#0D0D1A]">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 border-4 border-purple-200 rounded-full animate-ping"></div>
            <div className="absolute inset-0 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-gray-300 text-lg">Loading your memory space...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-[#0D0D1A]">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 mx-auto mb-4 bg-red-500/20 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-red-400 text-lg font-semibold mb-2">Unable to load memory graph</h3>
          <p className="text-gray-400 mb-6">{error}</p>
          <button 
            onClick={fetchMemoryGraph}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors duration-200 font-medium"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-[#0D0D1A]">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 mx-auto mb-6 bg-purple-500/20 rounded-full flex items-center justify-center">
            <svg className="w-10 h-10 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h3 className="text-white text-xl font-semibold mb-2">No memories yet</h3>
          <p className="text-gray-400 mb-6">Start creating memories to build your knowledge graph</p>
          {onMemoryCreate && (
            <button 
              onClick={() => {
                // This would typically open a create memory dialog
                // For now, we'll just show it's clickable
              }}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg transition-all duration-200 font-medium hover:scale-105"
            >
              Create your first memory
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="h-full relative bg-[#0D0D1A]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
        className="bg-transparent"
        minZoom={0.3}
        maxZoom={1.2}
        defaultViewport={{ x: 0, y: 0, zoom: 0.5 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background 
          variant={BackgroundVariant.Dots} 
          gap={30} 
          size={1}
          color="#1a1a2e"
          className="opacity-50"
        />
        <Controls 
          className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-xl overflow-hidden"
          showZoom={true}
          showFitView={true}
          showInteractive={false}
        />
      </ReactFlow>
      
      {/* Gradient overlays for depth */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-[#0D0D1A] to-transparent"></div>
        <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-[#0D0D1A] to-transparent"></div>
      </div>

      {/* Action Buttons */}
      <div className="absolute top-4 right-4 flex flex-col space-y-2">
        {/* Refresh Button */}
        <button
          onClick={fetchMemoryGraph}
          className="p-2 bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-lg hover:bg-gray-800/50 transition-colors group"
          title="Refresh"
        >
          <svg className="w-5 h-5 text-gray-400 group-hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        {/* Add Memory Button */}
        <button
          onClick={() => setShowAddModal(true)}
          className="p-2 bg-gradient-to-r from-purple-600 to-blue-600 backdrop-blur-sm border border-purple-500/50 rounded-lg hover:scale-105 transition-all group"
          title="Add Memory"
        >
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>

        {/* Update Memory Button */}
        {selectedNode && (
          <button
            onClick={() => setShowUpdateModal(true)}
            className="p-2 bg-gradient-to-r from-emerald-600 to-teal-600 backdrop-blur-sm border border-emerald-500/50 rounded-lg hover:scale-105 transition-all group"
            title="Update Memory"
          >
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
        )}

        {/* Delete Memory Button */}
        {selectedNode && (
          <button
            onClick={() => setShowDeleteModal(true)}
            className="p-2 bg-gradient-to-r from-red-600 to-pink-600 backdrop-blur-sm border border-red-500/50 rounded-lg hover:scale-105 transition-all group"
            title="Delete Memory"
          >
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        )}
      </div>

      {/* Modals */}
      <AddMemoryModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={handleCreateMemory}
      />

      <UpdateMemoryModal
        isOpen={showUpdateModal}
        onClose={() => setShowUpdateModal(false)}
        onSubmit={handleUpdateMemory}
        memory={selectedNode ? {
          id: selectedNode.id,
          title: selectedNode.data.title,
          content: selectedNode.data.content,
          tags: selectedNode.data.tags
        } : undefined}
      />

      <DeleteConfirmModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={() => selectedNode ? handleDeleteMemory(selectedNode.id) : Promise.resolve()}
        memoryTitle={selectedNode?.data.title}
      />
    </div>
  );
}

// Wrapper component with ReactFlowProvider
export function MemoryGraphDashboard({ 
  onNodeSelect,
  onMemoryCreate,
  onMemoryUpdate,
  onMemoryDelete 
}: MemoryGraphDashboardInnerProps) {
  return (
    <ReactFlowProvider>
      <MemoryGraphDashboardInner 
        onNodeSelect={onNodeSelect}
        onMemoryCreate={onMemoryCreate}
        onMemoryUpdate={onMemoryUpdate}
        onMemoryDelete={onMemoryDelete}
      />
    </ReactFlowProvider>
  );
}