# src/educational_exporter.py

from parser import StructuralModel

class EducationalExporter:
    """
    A utility class dedicated to writing intermediate parameters (like matrices)
    to readable text files to help students verify hand calculations.
    """
    def __init__(self, model: StructuralModel):
        self.model = model

    def export_matrices(self, K_full: list, M_full: list, output_filename: str):
        """Writes the DOF map, Stiffness Matrix, and Mass Matrix to a text file."""
        with open(output_filename, 'w') as f:
            f.write("=================================================================\n")
            f.write("      INTERMEDIATE MATRICES (EDUCATIONAL VERIFICATION DATA)      \n")
            f.write("=================================================================\n\n")
            
            # 1. Print the DOF Map so students know which row is which Node/Direction
            f.write("--- Degree of Freedom (DOF) Map ---\n")
            f.write("Note: -1 indicates a restrained (support) or condensed DOF.\n")
            f.write(f"{'Node ID':<10} {'UX':<8} {'UY':<8} {'RZ':<8}\n")
            f.write("-" * 35 + "\n")
            
            for node_id in sorted(self.model.nodes.keys()):
                node = self.model.nodes[node_id]
                dofs = node.dofs
                ux = str(dofs[0]) if len(dofs) > 0 else "N/A"
                uy = str(dofs[1]) if len(dofs) > 1 else "N/A"
                rz = str(dofs[2]) if len(dofs) > 2 else "N/A"
                f.write(f"{node_id:<10} {ux:<8} {uy:<8} {rz:<8}\n")
            
            # 2. Print Full Stiffness Matrix
            f.write("\n\n--- Global Stiffness Matrix [K] (Active DOFs) ---\n")
            if not K_full or len(K_full) == 0:
                f.write("No active DOFs found.\n")
            else:
                for row in K_full:
                    # Format as scientific notation, e.g., 1.234e+05
                    row_str = "  ".join(f"{val:12.4e}" for val in row)
                    f.write(row_str + "\n")

            # 3. Print Full Mass Matrix
            f.write("\n\n--- Global Mass Matrix [M] (Active DOFs) ---\n")
            if not M_full or len(M_full) == 0:
                f.write("No active DOFs found.\n")
            else:
                for row in M_full:
                    # Format as standard decimal, e.g., 1500.000
                    row_str = "  ".join(f"{val:12.3f}" for val in row)
                    f.write(row_str + "\n")
            
            f.write("\n=================================================================\n")
            print(f"[Educational Output] Exported intermediate matrices to {output_filename}")