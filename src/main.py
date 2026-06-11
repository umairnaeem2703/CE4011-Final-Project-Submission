# src/main.py

import sys
import os
from parser import XMLParser
from dof_optimizer import DOFOptimizer
from matrix_assembly import MatrixAssembler, DynamicAssembler
from banded_solver import BandedSolver, UnstableStructureError
from post_processor import PostProcessor
from visualizer import save_deformed_shape_from_active
from visualizer import plot_nvm_diagrams
from educational_exporter import EducationalExporter
from modal_solver import ModalSolver, ModalSolverError  # <-- Added Import

def run_analysis(xml_filepath: str, output_dir: str = "./results", plot: bool = True):
    print(f"--- Starting Analysis: {os.path.basename(xml_filepath)} ---")
    
    # 1. Parse Data
    try:
        parser = XMLParser(xml_filepath)
        model = parser.parse()
    except Exception as e:
        print(f"❌ Parse Error: {e}")
        return

    # 2. Optimize DOFs
    try:
        optimizer = DOFOptimizer(model)
        num_eq, semi_bw, full_bw = optimizer.optimize()
    except UnstableStructureError as e:
        print(f"❌ Structural Error:\n{e}")
        return

    print(f"Nodes: {len(model.nodes)} | Elements: {len(model.elements)}")
    print(f"Active Equations: {num_eq} | Bandwidth: {full_bw}")

    os.makedirs(output_dir, exist_ok=True)

    # Process each Load Case
    for lc_id in model.load_cases.keys():
        print(f"\nProcessing Load Case: {lc_id}...")
        
        # 3. Assemble Global System
        assembler = MatrixAssembler(model, num_eq, semi_bw)
        K_banded, F_global = assembler.assemble(lc_id)
        
        # 4. Solve System
        solver = BandedSolver(K_banded, F_global, semi_bw)
        try:
            D_active = solver.solve()
            print(f"✅ System solved successfully.")
        except UnstableStructureError as e:
            print(f"❌ {e}")
            continue
        except Exception as e:
            print(f"❌ Solver failed: {e}")
            continue

        # 5. Post-Process & Output
        processor = PostProcessor(model, D_active, lc_id)
        output_file = os.path.join(output_dir, f"{model.name}_{lc_id}_results.txt")
        processor.write_results(output_file)

        # ---------------------------------------------------------
        # 5b. Extract Educational Intermediate Variables
        # ---------------------------------------------------------
        edu_exporter = EducationalExporter(model)
        
        # We need the DynamicAssembler and full stiffness matrix for BOTH educational export and Modal Analysis
        dyn_assembler = DynamicAssembler(model, num_eq)
        K_full = assembler.assemble_full_stiffness_matrix()
        
        # Use LUMPED mass for static matrix export (backwards compatibility)
        M_full_lumped = dyn_assembler.assemble_mass_matrix(matrix_type='lumped', rho=7850.0)
        matrix_output_file = os.path.join(output_dir, f"{model.name}_{lc_id}_matrices.txt")
        edu_exporter.export_matrices(K_full, M_full_lumped, matrix_output_file)

        # ---------------------------------------------------------
        # 5c. MODAL ANALYSIS INTEGRATION
        # ---------------------------------------------------------
        # Build consistent mass matrix for more accurate dynamic modes
        M_full_consistent = dyn_assembler.assemble_mass_matrix(matrix_type='consistent', rho=7850.0)

        # Build influence vector r: 1 at every UX (horizontal) DOF, 0 elsewhere
        r_vector = [0.0] * num_eq
        for node in model.nodes.values():
            if node.dofs[0] >= 0:  # UX DOF is active
                r_vector[node.dofs[0]] = 1.0
                
        try:
            modal = ModalSolver(K_full, M_full_consistent)
            modal_results = modal.solve(r=r_vector, num_modes=min(num_eq, 10))
            modal.print_summary()
            modal.export_educational_output(
                os.path.join(output_dir, f"{model.name}_modal.txt"),
                modal_results
            )
        except ModalSolverError as e:
            print(f"⚠️ Modal analysis skipped: {e}")

        # 6. Plot Deformed Shape
        figure_file = os.path.join(output_dir, f"{model.name}_{lc_id}_deformed_shape.png")
        try:
            save_deformed_shape_from_active(
                model=model,
                D_active=D_active,
                filepath=figure_file,
                scale_factor=None,  # <-- Adjusted to trigger Auto-Scaling
                sub_segments=20,
                show_undeformed=True,
                lc_id=lc_id,
            )
        except Exception as e:
            print(f"⚠️ Plot generation failed: {e}")

        # 7. Generate NVM Diagrams
        if plot:
            nvm_path = os.path.join(output_dir, f"{model.name}_{lc_id}_NVM.png")
            plot_nvm_diagrams(model, processor, lc_id, save_path=nvm_path)

if __name__ == "__main__":
    # Run analysis on provided models
    for test_file in ["./data/Assignment_4_Q2a.xml", "./data/Assignment_4_Q2b.xml"]:
    # for test_file in ["./data/example1_case1_truss.xml", "./data/example2_frame.xml", "./data/example3_frame_truss.xml"]:
        if os.path.exists(test_file):
            run_analysis(test_file)
        else:
            print(f"File not found: {test_file}")