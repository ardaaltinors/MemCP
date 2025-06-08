import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Position,
  Panel,
  useReactFlow,
  BackgroundVariant,
  ConnectionMode,
  ReactFlowProvider,
  Handle,
  type Node,
  type Edge,
  type NodeTypes,
} from '@xyflow/react';
import { getMemoryGraph, createMemory, updateMemory, deleteMemory } from '@libs/api';
import type { ApiMemoryNode, ApiMemoryEdge, CreateMemoryRequest, UpdateMemoryRequest } from '@libs/types';
import { authUtils } from '@libs/utils/auth';

import '@xyflow/react/dist/style.css';

// Memory node data structure for React Flow
interface MemoryNodeData extends Record<string, unknown> {
  title: string;
  content: string;
  timestamp: string;
  tags: string[];
  isHighlighted?: boolean;
  colorGradient?: string;
}

// Custom Memory Node Component
const MemoryNode = ({ data, selected }: { data: MemoryNodeData; selected?: boolean }) => {
  // Use the assigned color gradient for this cluster, fallback to blue
  const colorGradient = data.colorGradient || 'from-blue-500 to-blue-700';
  
  // Larger size for better text visibility
  const size = 120;

  return (
    <div
      className={`relative group transition-all duration-300 ${
        selected ? 'scale-110 z-20' : 'hover:scale-105'
      }`}
      style={{ width: `${size}px`, height: `${size}px` }}
    >
      {/* Glow effect for selected/highlighted nodes */}
      {(selected || data.isHighlighted) && (
        <div
          className={`absolute inset-0 bg-gradient-to-br ${colorGradient} rounded-full blur-lg opacity-50 animate-pulse`}
          style={{ transform: 'scale(1.3)' }}
        />
      )}
      
      {/* Main node */}
      <div
        className={`relative w-full h-full bg-gradient-to-br ${colorGradient} rounded-full border-2 ${
          selected ? 'border-white' : 'border-gray-600'
        } shadow-lg flex items-center justify-center transition-all duration-300 cursor-pointer hover:shadow-xl`}
      >
        {/* Handles for connections */}
        <Handle type="target" position={Position.Left} className="!bg-gray-300 !border-gray-600" />
        <Handle type="source" position={Position.Right} className="!bg-gray-300 !border-gray-600" />
        
        {/* Node content */}
        <div className="text-center p-4 w-full h-full flex items-center justify-center">
          <div className="text-white font-medium text-sm leading-tight break-words max-w-full overflow-hidden">
            {data.title.length > 35 ? `${data.title.substring(0, 35)}...` : data.title}
          </div>
        </div>
      </div>
    </div>
  );
};

// Transform API data to React Flow format
const transformApiDataToReactFlow = (
  apiNodes: ApiMemoryNode[], 
  apiEdges: ApiMemoryEdge[]
): { nodes: Node<MemoryNodeData>[]; edges: Edge[] } => {
  // Use clustering algorithm to group related nodes while maintaining organic distribution
  const nodeSize = 120;
  const minDistance = 180; // Minimum distance between node centers
  const canvasWidth = 2500;
  const canvasHeight = 2000;
  const padding = nodeSize;
  
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
  
  // Helper function to find position within a cluster area
  const findClusterPosition = (
    clusterCenter: {x: number, y: number}, 
    clusterRadius: number, 
    existingPositions: Array<{x: number, y: number}>,
    maxAttempts = 30
  ): {x: number, y: number} => {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      // Generate random position within cluster area
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
    
    // Fallback: place randomly within cluster area
    const angle = Math.random() * Math.PI * 2;
    const distance = Math.random() * clusterRadius;
    const x = Math.max(padding, Math.min(canvasWidth - padding, clusterCenter.x + Math.cos(angle) * distance));
    const y = Math.max(padding, Math.min(canvasHeight - padding, clusterCenter.y + Math.sin(angle) * distance));
    return { x, y };
  };
  
  // Get connected components
  const nodeIds = apiNodes.map(node => node.id);
  const components = findConnectedComponents(nodeIds);
  
  // Beautiful color palette for different clusters
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
  
  // Assign colors to components
  const componentColors = components.map((_, index) => 
    colorPalette[index % colorPalette.length]
  );
  
  // Assign cluster centers for each component
  const clusterCenters: Array<{x: number, y: number}> = [];
  const usedPositions: Array<{x: number, y: number}> = [];
  
  // Generate cluster centers with adequate spacing
  components.forEach((component, index) => {
    let clusterCenter;
    let attempts = 0;
    
    do {
      clusterCenter = {
        x: padding + Math.random() * (canvasWidth - 2 * padding),
        y: padding + Math.random() * (canvasHeight - 2 * padding)
      };
      attempts++;
    } while (
      attempts < 50 && 
      usedPositions.some(pos => isTooClose(clusterCenter.x, clusterCenter.y, pos.x, pos.y, 300))
    );
    
    clusterCenters.push(clusterCenter);
    usedPositions.push(clusterCenter);
  });
  
  // Create node-to-component mapping
  const nodeToComponent = new Map<string, number>();
  components.forEach((component, index) => {
    component.forEach(nodeId => {
      nodeToComponent.set(nodeId, index);
    });
  });
  
  // Generate positions for all nodes
  const nodePositions: Array<{x: number, y: number}> = [];
  
  const nodes: Node<MemoryNodeData>[] = apiNodes.map((node) => {
    const componentIndex = nodeToComponent.get(node.id) ?? 0;
    const clusterCenter = clusterCenters[componentIndex];
    const componentSize = components[componentIndex]?.length || 1;
    
    // Adjust cluster radius based on component size
    const baseRadius = 200;
    const clusterRadius = Math.max(baseRadius, Math.sqrt(componentSize) * 100);
    
    const position = findClusterPosition(clusterCenter, clusterRadius, nodePositions);
    nodePositions.push(position);
    
    return {
      id: node.id,
      type: 'memoryNode',
      position: { x: position.x, y: position.y },
      data: {
        title: node.label,
        content: node.content,
        timestamp: new Date(node.created_at).toLocaleDateString(),
        tags: node.tags,
        colorGradient: componentColors[componentIndex],
      },
      draggable: true,
      selectable: true,
    };
  });

  const edges: Edge[] = apiEdges.map((edge, index) => ({
    id: `edge-${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    type: 'bezier',
    animated: edge.weight > 0.7,
    style: {
      strokeWidth: Math.max(2, edge.weight * 6),
      stroke: edge.weight > 0.7 ? '#a855f7' : '#e2e8f0',
      strokeOpacity: 0.7,
      strokeLinecap: 'round',
    },
    data: {
      weight: edge.weight,
    },
  }));

  return { nodes, edges };
};

function MemoryGraphInner() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState<Node<MemoryNodeData> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nodeCount, setNodeCount] = useState(0);
  const [edgeCount, setEdgeCount] = useState(0);
  
  // New state for memory operations
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [editTags, setEditTags] = useState<string[]>([]);
  const [isOperating, setIsOperating] = useState(false);
  const [operationError, setOperationError] = useState<string | null>(null);
  
  // State for creating new memories
  const [isCreating, setIsCreating] = useState(false);
  const [newContent, setNewContent] = useState('');
  const [newTags, setNewTags] = useState<string[]>([]);
  
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
        const data = await getMemoryGraph(token);
      
      const { nodes: transformedNodes, edges: transformedEdges } = transformApiDataToReactFlow(
        data.nodes,
        data.edges
      );
      
      console.log('API Response:', {
        nodes: data.nodes.length,
        edges: data.edges.length,
        transformedNodes: transformedNodes.length,
        transformedEdges: transformedEdges.length,
        sampleEdge: transformedEdges[0]
      });
      
      // If no edges from API, add test edges to verify edge rendering works
      if (transformedEdges.length === 0 && transformedNodes.length >= 2) {
        const testEdges: Edge[] = [
          {
            id: 'test-edge-1',
            source: transformedNodes[0].id,
            target: transformedNodes[1].id,
            type: 'bezier',
            style: {
              strokeWidth: 2,
              stroke: '#e2e8f0',
              strokeOpacity: 0.7,
              strokeLinecap: 'round',
            },
          }
        ];
        console.log('Adding test edge:', testEdges[0]);
        setEdges(testEdges);
      } else {
        setEdges(transformedEdges);
      }
      
      setNodes(transformedNodes);
      setNodeCount(data.total_nodes);
      setEdgeCount(data.total_edges);
      
      // Auto-fit view after loading
      setTimeout(() => fitView({ padding: 0.1 }), 100);
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

  // Handle node connections
  const onConnect = useCallback(
    (params: any) => setEdges((eds) => addEdge({ ...params, type: 'bezier' }, eds)),
    [setEdges]
  );

  // Handle node clicks
  const onNodeClick = useCallback(
    (_: any, node: Node<MemoryNodeData>) => {
      setSelectedNode(selectedNode?.id === node.id ? null : node);
      
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
    [selectedNode, edges, setNodes]
  );

  // Handle edge clicks to highlight connections
  const onEdgeClick = useCallback(
    (_: any, edge: Edge) => {
      setNodes((nodes) =>
        nodes.map((n) => ({
          ...n,
          data: {
            ...n.data,
            isHighlighted: n.id === edge.source || n.id === edge.target,
          },
        }))
      );
    },
    [setNodes]
  );

  // Clear highlights when clicking on background
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setIsEditing(false);
    setIsCreating(false);
    setOperationError(null);
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

  // Start editing a memory
  const handleEditMemory = useCallback(() => {
    if (!selectedNode) return;
    
    setIsEditing(true);
    setEditContent(selectedNode.data.content);
    setEditTags([...selectedNode.data.tags]);
    setOperationError(null);
  }, [selectedNode]);

  // Save memory updates
  const handleSaveMemory = useCallback(async () => {
    if (!selectedNode) return;
    
    try {
      setIsOperating(true);
      setOperationError(null);
      
      const token = authUtils.getToken();
      const updateData: UpdateMemoryRequest = {
        content: editContent,
        tags: editTags,
      };
      
      await updateMemory(token, selectedNode.id, updateData);
      
      // Update the node in the graph
      setNodes((nodes) =>
        nodes.map((node) =>
          node.id === selectedNode.id
            ? {
                ...node,
                data: {
                  ...node.data,
                  title: editContent.length > 35 ? `${editContent.substring(0, 35)}...` : editContent,
                  content: editContent,
                  tags: editTags,
                },
              }
            : node
        )
      );
      
      // Update selected node data
      setSelectedNode((prev) =>
        prev
          ? {
              ...prev,
              data: {
                ...prev.data,
                title: editContent.length > 35 ? `${editContent.substring(0, 35)}...` : editContent,
                content: editContent,
                tags: editTags,
              },
            }
          : null
      );
      
      setIsEditing(false);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : 'Failed to update memory');
    } finally {
      setIsOperating(false);
    }
  }, [selectedNode, editContent, editTags, setNodes]);

  // Delete a memory
  const handleDeleteMemory = useCallback(async () => {
    if (!selectedNode) return;
    
    if (!confirm('Are you sure you want to delete this memory? This action cannot be undone.')) {
      return;
    }
    
    try {
      setIsOperating(true);
      setOperationError(null);
      
      const token = authUtils.getToken();
      await deleteMemory(token, selectedNode.id);
      
      // Remove the node from the graph
      setNodes((nodes) => nodes.filter((node) => node.id !== selectedNode.id));
      setEdges((edges) => 
        edges.filter((edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id)
      );
      
      setSelectedNode(null);
      setIsEditing(false);
      
      // Update counts
      setNodeCount(prev => prev - 1);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : 'Failed to delete memory');
    } finally {
      setIsOperating(false);
    }
  }, [selectedNode, setNodes, setEdges]);

  // Cancel editing
  const handleCancelEdit = useCallback(() => {
    setIsEditing(false);
    setOperationError(null);
  }, []);

  // Add tag to edit form
  const handleAddTag = useCallback((tag: string) => {
    if (tag.trim() && !editTags.includes(tag.trim())) {
      setEditTags([...editTags, tag.trim()]);
    }
  }, [editTags]);

  // Remove tag from edit form
  const handleRemoveTag = useCallback((index: number) => {
    setEditTags(editTags.filter((_, i) => i !== index));
  }, [editTags]);

  // Create new memory handlers
  const handleStartCreate = useCallback(() => {
    setIsCreating(true);
    setNewContent('');
    setNewTags([]);
    setOperationError(null);
  }, []);

  const handleCreateMemory = useCallback(async () => {
    if (!newContent.trim()) return;
    
    try {
      setIsOperating(true);
      setOperationError(null);
      
      const token = authUtils.getToken();
      const createData: CreateMemoryRequest = {
        content: newContent.trim(),
        tags: newTags,
      };
      
      await createMemory(token, createData);
      
      // Refresh the graph to show the new memory
      await fetchMemoryGraph();
      
      // Reset form
      setIsCreating(false);
      setNewContent('');
      setNewTags([]);
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : 'Failed to create memory');
    } finally {
      setIsOperating(false);
    }
  }, [newContent, newTags, fetchMemoryGraph]);

  const handleCancelCreate = useCallback(() => {
    setIsCreating(false);
    setNewContent('');
    setNewTags([]);
    setOperationError(null);
  }, []);

  const handleAddNewTag = useCallback((tag: string) => {
    if (tag.trim() && !newTags.includes(tag.trim())) {
      setNewTags([...newTags, tag.trim()]);
    }
  }, [newTags]);

  const handleRemoveNewTag = useCallback((index: number) => {
    setNewTags(newTags.filter((_, i) => i !== index));
  }, [newTags]);

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 border-4 border-purple-200 rounded-full animate-ping"></div>
            <div className="absolute inset-0 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-gray-300 text-lg">Loading memory graph...</p>
          <p className="text-gray-500 text-sm mt-2">Preparing your memories for visualization</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-900">
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

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Enhanced Header */}
      <div className="flex items-center justify-between p-4 bg-gray-800 border-b border-gray-700">
        
        <div className="flex items-center space-x-4 text-gray-400">
          <span>Click on a memory to explore</span>
        </div>
        
        {/* Controls */}
        <div className="flex items-center space-x-3">
          <button 
            onClick={() => fitView({ padding: 0.1 })}
            className="px-3 py-2 text-sm bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-md transition-colors"
            title="Fit to view"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
          <button 
            onClick={fetchMemoryGraph}
            className="px-3 py-2 text-sm bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-md transition-colors"
            title="Refresh"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <button 
            onClick={handleStartCreate}
            className="px-4 py-2 text-sm bg-purple-600 hover:bg-purple-700 text-white rounded-md transition-colors"
          >
            Add Memory
          </button>
        </div>
      </div>

      {/* React Flow Container */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          nodeTypes={nodeTypes}
          connectionMode={ConnectionMode.Loose}
          fitView
          attributionPosition="bottom-left"
          className="bg-gray-900"
          minZoom={0.1}
          maxZoom={2}
          defaultEdgeOptions={{
            style: { strokeWidth: 2, stroke: '#e2e8f0', strokeOpacity: 0.7, strokeLinecap: 'round' },
            type: 'bezier',
          }}
        >
          <Background 
            variant={BackgroundVariant.Dots} 
            gap={20} 
            size={1}
            className="opacity-30"
                    />
          <Controls 
            className="bg-gray-800 border-gray-600"
            showZoom={true}
            showFitView={true}
            showInteractive={false}
                  />
          <MiniMap 
            className="bg-gray-800 border-gray-600"
            maskColor="rgba(0, 0, 0, 0.8)"
            nodeColor="#ef4444"
          />

          {/* Enhanced Node Details Panel */}
          {selectedNode && (
            <Panel position="top-right" className="w-96">
              <div className="bg-gray-800 border border-gray-600 rounded-lg p-6 shadow-2xl">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div 
                      className={`w-6 h-6 rounded-full bg-gradient-to-br ${selectedNode.data.colorGradient || 'from-blue-500 to-blue-700'}`} 
                    />
                    <h3 className="text-white font-bold text-lg leading-tight">
                      {isEditing ? 'Edit Memory' : selectedNode.data.title}
                    </h3>
                  </div>
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="text-gray-400 hover:text-gray-300 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                {/* Error Display */}
                {operationError && (
                  <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
                    <p className="text-red-400 text-sm">{operationError}</p>
                  </div>
                )}
                
                <div className="space-y-4">
                  {/* Content Section */}
                  <div>
                    <label className="text-xs text-gray-400 uppercase tracking-wide font-semibold">Content</label>
                    {isEditing ? (
                      <textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        className="w-full mt-2 p-3 bg-gray-700 border border-gray-600 rounded-lg text-gray-300 text-sm leading-relaxed focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                        rows={4}
                        placeholder="Enter memory content..."
                      />
                    ) : (
                      <p className="text-sm text-gray-300 mt-1 leading-relaxed max-h-32 overflow-y-auto">
                        {selectedNode.data.content}
                      </p>
                    )}
                  </div>
                  
                  {/* Tags Section */}
                  <div>
                    <label className="text-xs text-gray-400 uppercase tracking-wide font-semibold">Tags</label>
                    {isEditing ? (
                      <div className="mt-2">
                        <div className="flex flex-wrap gap-2 mb-2">
                          {editTags.map((tag, index) => (
                            <span 
                              key={index}
                              className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-full border border-gray-600 flex items-center gap-1"
                            >
                              {tag}
                              <button 
                                onClick={() => handleRemoveTag(index)}
                                className="text-gray-400 hover:text-red-400 ml-1"
                              >
                                ×
                              </button>
                            </span>
                          ))}
                        </div>
                        <input
                          type="text"
                          placeholder="Add tag (press Enter)"
                          className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-gray-300 text-sm focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              handleAddTag(e.currentTarget.value);
                              e.currentTarget.value = '';
                            }
                          }}
                        />
                      </div>
                    ) : (
                      selectedNode.data.tags.length > 0 ? (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {selectedNode.data.tags.map((tag, index) => (
                            <span 
                              key={index}
                              className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-full border border-gray-600"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500 mt-1">No tags</p>
                      )
                    )}
                  </div>
                  
                  {/* Metadata */}
                  {!isEditing && (
                    <>
                      <div>
                        <label className="text-xs text-gray-400 uppercase tracking-wide font-semibold">Created</label>
                        <p className="text-sm text-gray-300 mt-1">{selectedNode.data.timestamp}</p>
                      </div>
                      
                      <div>
                        <label className="text-xs text-gray-400 uppercase tracking-wide font-semibold">Connections</label>
                        <p className="text-sm text-gray-300 mt-1">
                          {edges.filter(edge => edge.source === selectedNode.id || edge.target === selectedNode.id).length} connected nodes
                        </p>
                      </div>
                    </>
                  )}
                  
                  {/* Action Buttons */}
                  <div className="pt-4 border-t border-gray-700">
                    {isEditing ? (
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveMemory}
                          disabled={isOperating || !editContent.trim()}
                          className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors duration-200 font-medium text-sm flex items-center justify-center gap-2"
                        >
                          {isOperating ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              Saving...
                            </>
                          ) : (
                            <>
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              Save
                            </>
                          )}
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          disabled={isOperating}
                          className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors duration-200 font-medium text-sm"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          onClick={handleEditMemory}
                          disabled={isOperating}
                          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors duration-200 font-medium text-sm flex items-center justify-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                          Edit
                        </button>
                        <button
                          onClick={handleDeleteMemory}
                          disabled={isOperating}
                          className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors duration-200 font-medium text-sm flex items-center justify-center gap-2"
                        >
                          {isOperating ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              Deleting...
                            </>
                          ) : (
                            <>
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                              Delete
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Panel>
          )}

          {/* Create Memory Panel */}
          {isCreating && (
            <Panel position="top-left" className="w-96">
              <div className="bg-gray-800 border border-gray-600 rounded-lg p-6 shadow-2xl">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-purple-700" />
                    <h3 className="text-white font-bold text-lg leading-tight">Create New Memory</h3>
                  </div>
                  <button
                    onClick={handleCancelCreate}
                    className="text-gray-400 hover:text-gray-300 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                {/* Error Display */}
                {operationError && (
                  <div className="mb-4 p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
                    <p className="text-red-400 text-sm">{operationError}</p>
                  </div>
                )}
                
                <div className="space-y-4">
                  {/* Content Input */}
                  <div>
                    <label className="text-xs text-gray-400 uppercase tracking-wide font-semibold">Content *</label>
                    <textarea
                      value={newContent}
                      onChange={(e) => setNewContent(e.target.value)}
                      className="w-full mt-2 p-3 bg-gray-700 border border-gray-600 rounded-lg text-gray-300 text-sm leading-relaxed focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                      rows={4}
                      placeholder="Enter your memory content..."
                    />
                  </div>
                  
                  {/* Tags Input */}
                  <div>
                    <label className="text-xs text-gray-400 uppercase tracking-wide font-semibold">Tags</label>
                    <div className="mt-2">
                      {newTags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-2">
                          {newTags.map((tag, index) => (
                            <span 
                              key={index}
                              className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-full border border-gray-600 flex items-center gap-1"
                            >
                              {tag}
                              <button 
                                onClick={() => handleRemoveNewTag(index)}
                                className="text-gray-400 hover:text-red-400 ml-1"
                              >
                                ×
                              </button>
                            </span>
                          ))}
                        </div>
                      )}
                      <input
                        type="text"
                        placeholder="Add tag (press Enter)"
                        className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-gray-300 text-sm focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddNewTag(e.currentTarget.value);
                            e.currentTarget.value = '';
                          }
                        }}
                      />
                    </div>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="pt-4 border-t border-gray-700">
                    <div className="flex gap-2">
                      <button
                        onClick={handleCreateMemory}
                        disabled={isOperating || !newContent.trim()}
                        className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors duration-200 font-medium text-sm flex items-center justify-center gap-2"
                      >
                        {isOperating ? (
                          <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            Creating...
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                            Create Memory
                          </>
                        )}
                      </button>
                      <button
                        onClick={handleCancelCreate}
                        disabled={isOperating}
                        className="px-4 py-2 bg-gray-600 hover:bg-gray-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors duration-200 font-medium text-sm"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </Panel>
          )}
        </ReactFlow>
              </div>
              
      {/* Enhanced Stats Footer */}
      <div className="px-4 py-3 bg-gray-800 border-t border-gray-700">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-6 text-gray-400">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span>{nodeCount} memories</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-cyan-500 rounded-full"></div>
              <span>{edgeCount} connections</span>
              </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>Last updated: {new Date().toLocaleDateString()}</span>
            </div>
      </div>

          <div className="text-gray-500">
            Drag to rearrange • Scroll to zoom
        </div>
        </div>
      </div>
    </div>
  );
} 

// Wrapper component with ReactFlowProvider
export function MemoryGraph() {
  return (
    <ReactFlowProvider>
      <MemoryGraphInner />
    </ReactFlowProvider>
  );
} 