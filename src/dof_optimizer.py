# src/dof_optimizer.py

from parser import StructuralModel
from structural_validator import StructuralValidator

# ==========================================
# UNION-FIND DATA STRUCTURE (Disjoint Set)
# ==========================================

class UnionFind:
    """
    A Union-Find (Disjoint Set Union) data structure for grouping nodes
    that are connected by axially rigid members.
    Implements path compression and union by rank for efficiency.
    """
    def __init__(self, elements):
        """Initialize with node IDs from the elements."""
        self.parent = {}
        self.rank = {}
        
        # Collect all node IDs
        node_ids = set()
        for element in elements.values():
            node_ids.add(element.node_i.id)
            node_ids.add(element.node_j.id)
        
        # Initialize each node as its own parent (singleton set)
        for node_id in node_ids:
            self.parent[node_id] = node_id
            self.rank[node_id] = 0
    
    def find(self, x: int) -> int:
        """
        Finds the root (representative) of the set containing x.
        Uses path compression for efficiency.
        """
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
        
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]
    
    def union(self, x: int, y: int) -> None:
        """
        Unites the sets containing x and y.
        Uses union by rank for efficiency.
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return  # Already in the same set
        
        # Union by rank: attach smaller tree under larger tree
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
    
    def get_component(self, x: int) -> set:
        """Returns all nodes in the same component as x."""
        root = self.find(x)
        return {n for n in self.parent.keys() if self.find(n) == root}


class DOFOptimizer:
    def __init__(self, model: StructuralModel):
        self.model = model
        self.num_equations = 0
        self.semi_bandwidth = 0
        self.full_bandwidth = 0
        self.node_to_master = {}       # Maps slave node IDs to master node IDs
        self.node_to_master_axial = {} # Initialize axial mapping dictionary
        self.node_to_master_ux = {}    # Initialize UX mapping dictionary

    def optimize(self) -> tuple[int, int, int]:
        """Runs the optimization and returns (num_equations, semi_bandwidth, full_bandwidth)."""
        StructuralValidator(self.model).validate()
        
        # Group nodes connected by axially rigid members
        self._identify_rigid_groups()
        
        adj_list = self._build_adjacency_list()
        rcm_order = self._reverse_cuthill_mckee(adj_list)
        self._assign_dofs(rcm_order)
        self._calculate_bandwidth()
        return self.num_equations, self.semi_bandwidth, self.full_bandwidth

    def _identify_rigid_groups(self) -> None:
        """
        Identifies rigid constraints from:
        1. Axially rigid members (is_axially_rigid=true in XML)
        
        Does NOT apply automatic floor-level rigid diaphragm assumption.
        Each node is independent unless explicitly coupled.
        """
        # Use Union-Find for explicitly-defined axially rigid members only
        uf = UnionFind(self.model.elements)
        for element in self.model.elements.values():
            if element.is_axially_rigid:
                uf.union(element.node_i.id, element.node_j.id)
        
        # For axially rigid groups, designate smallest ID as master
        self.node_to_master = {}
        processed = set()
        for node_id in self.model.nodes.keys():
            if node_id not in processed:
                component = uf.get_component(node_id)
                processed.update(component)
                master_id = min(component)
                for node_id_in_comp in component:
                    self.node_to_master_axial[node_id_in_comp] = master_id
        
        # UX direction: same as axial (no separate floor-based grouping)
        self.node_to_master_ux = self.node_to_master_axial.copy()
        
        # For backward compatibility
        self.node_to_master = self.node_to_master_ux

    def _get_master_ux(self, node_id: int) -> int:
        """
        Returns the master node ID for UX DOF (floor-based rigid diaphragm).
        """
        return self.node_to_master_ux.get(node_id, node_id)
    
    def _get_effective_node(self, node_id: int) -> int:
        """
        Returns the master node ID if node_id is a slave in an axially rigid group,
        otherwise returns node_id itself.
        """
        return self.node_to_master.get(node_id, node_id)

    def _has_rotational_stiffness(self, node_id: int) -> bool:
        """
        Checks if a node receives rotational stiffness from any connected member.
        This prevents 'spinning node' mechanisms (singular matrix) when multiple 
        hinged members meet at a free node.
        """
        for el in self.model.elements.values():
            if el.type == 'frame':
                if el.node_i.id == node_id and not el.release_start:
                    return True
                if el.node_j.id == node_id and not el.release_end:
                    return True
        return False

    def _get_active_nodes(self) -> set:
        """Identifies nodes that have at least one active DOF."""
        active_nodes = set()
        for n_id, node in self.model.nodes.items():
            support = self.model.supports.get(n_id)
            has_active = False
            
            if not (support and support.restrain_ux):
                has_active = True
            if not (support and support.restrain_uy):
                has_active = True
                
            # Only assign an active rotational DOF if the node actually has rotational stiffness
            if self._has_rotational_stiffness(n_id) and not (support and support.restrain_rz):
                has_active = True
                
            if has_active:
                active_nodes.add(n_id)
                
        return active_nodes

    def _build_adjacency_list(self) -> dict:
        """Creates an adjacency graph of node connectivity, excluding fully restrained nodes."""
        active_nodes = self._get_active_nodes()
        adj = {n_id: set() for n_id in active_nodes}
        
        for el in self.model.elements.values():
            if el.node_i.id in active_nodes and el.node_j.id in active_nodes:
                adj[el.node_i.id].add(el.node_j.id)
                adj[el.node_j.id].add(el.node_i.id)
                
        return {k: list(v) for k, v in adj.items()}

    def _reverse_cuthill_mckee(self, adj: dict) -> list:
        """Orders nodes using RCM with coordinate tie-breaking."""
        if not adj:
            return []
            
        degrees = {node: len(neighbors) for node, neighbors in adj.items()}
        
        def sort_key(n_id):
            node = self.model.nodes[n_id]
            return (degrees[n_id], float(node.x), float(node.y), int(n_id))

        unvisited = set(adj.keys())
        result = []

        while unvisited:
            start_node = min(unvisited, key=sort_key)
            queue = [start_node]
            unvisited.remove(start_node)

            while queue:
                current = queue.pop(0)
                result.append(current)

                neighbors = [n for n in adj[current] if n in unvisited]
                neighbors.sort(key=sort_key)
                
                for neighbor in neighbors:
                    queue.append(neighbor)
                    unvisited.remove(neighbor)
                    
        return result[::-1]

    def _assign_dofs(self, rcm_order: list):
        """
        Assigns equation numbers to active DOFs.
        
        UX, UY, RZ are all independent UNLESS explicitly constrained:
        - By a support (boundary condition)
        - By an axially rigid member coupling all DOFs between nodes
        
        Process:
        1. For each master node in RCM order, assign UX, UY, RZ
        2. Propagate master DOFs to slave nodes (axially rigid groups)
        """
        self.num_equations = 0
        
        # Initialize all nodes with unassigned DOF indices
        for node in self.model.nodes.values():
            node.dofs = [-1, -1, -1]
        
        # First: assign DOFs for axially-rigid group masters
        assigned_masters = set()
        for node_id in rcm_order:
            axial_master_id = self._get_effective_node(node_id)
            
            if axial_master_id in assigned_masters:
                continue  # Already processed this master's DOFs
            
            assigned_masters.add(axial_master_id)
            node = self.model.nodes[axial_master_id]
            support = self.model.supports.get(axial_master_id)
            
            # Assign UX independently (no floor-level ridging)
            if not (support and support.restrain_ux):
                node.dofs[0] = self.num_equations
                self.num_equations += 1
            
            # Assign UY independently
            if not (support and support.restrain_uy):
                node.dofs[1] = self.num_equations
                self.num_equations += 1
            
            # Assign RZ if has rotational stiffness
            if self._has_rotational_stiffness(axial_master_id) and not (support and support.restrain_rz):
                node.dofs[2] = self.num_equations
                self.num_equations += 1
        
        # Second: propagate master DOFs to all slave nodes (axially rigid groups)
        for node_id in self.model.nodes.keys():
            node = self.model.nodes[node_id]
            axial_master_id = self._get_effective_node(node_id)
            
            if axial_master_id != node_id:
                # This is a slave node: copy master's DOFs
                master_node = self.model.nodes[axial_master_id]
                node.dofs = master_node.dofs.copy()

    def _calculate_bandwidth(self):
        """Calculates semi-bandwidth m = max(|DOF_a - DOF_b|) + 1, and full bandwidth."""
        max_m = 0
        for el in self.model.elements.values():
            active_dofs = [dof for dof in (el.node_i.dofs + el.node_j.dofs) if dof >= 0]
            
            if active_dofs:
                m = max(active_dofs) - min(active_dofs) + 1
                if m > max_m:
                    max_m = m
                    
        self.semi_bandwidth = max_m if max_m > 0 else 1
        self.full_bandwidth = 2 * self.semi_bandwidth - 1