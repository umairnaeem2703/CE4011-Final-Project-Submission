import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from results import ModalResults, RSAResults, StaticResults, THAResults
from ui.results_display import render_dynamic_results, render_static_results


class FakeStreamlit:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def recorder(*args, **kwargs):
            self.calls.append((name, args, kwargs))

        return recorder


def test_static_results_display_adapter():
    st = FakeStreamlit()
    results = StaticResults(
        K=[[1.0]],
        Kff=[[1.0]],
        F=[1.0],
        Ff=[1.0],
        displacements={1: [0.1, 0.0, 0.0]},
        reactions={1: [-1.0, 0.0, 0.0]},
        element_forces={"e1": [1.0, 0.0, 0.0, -1.0, 0.0, 0.0]},
        nvm_data={"e1": {"x": [0.0, 1.0], "N": [1.0, 1.0], "V": [0.0, 0.0], "M": [0.0, 0.0]}},
        dof_map={1: [0, 1, 2]},
        load_case_id="LC1",
    )

    render_static_results(st, results)

    dataframes = [args[0] for name, args, _ in st.calls if name == "dataframe"]
    assert len(dataframes) == 4 and dataframes[0][0]["ux"] == 0.1 and dataframes[2][0]["Ni"] == 1.0


def test_dynamic_results_display_adapter():
    st = FakeStreamlit()
    modal = ModalResults(
        K=[[2.0]],
        M=[[1.0]],
        eigenvalues=[4.0],
        frequencies=[0.3183],
        periods=[3.1416],
        mode_shapes=[[1.0]],
        modal_masses=[1.0],
        participation_factors=[1.0],
        effective_masses=[1.0],
        mass_participation_ratios=[1.0],
        influence_vector=[1.0],
        total_participating_mass=1.0,
        num_modes_requested=1,
        num_modes_extracted=1,
    )
    rsa = RSAResults([0.0], [1.0], [1.0], 1, [3.1416], [{0: 0.1}], [2.0], [3.0], "SRSS", {0: 0.1}, 2.0, 3.0, [], 0.05)
    tha = THAResults([0.0], [0.0], [[0.0]], [[0.1]], [[0.0]], [[0.0]], [1.0], [2.0], {0: 0.1}, {}, {}, 1.0, 2.0, [], 0.05, 0.1, 1, "gm", "m/s2", 1.0, "time_acceleration")

    render_dynamic_results(st, modal, rsa, tha)

    subheaders = [args[0] for name, args, _ in st.calls if name == "subheader"]
    assert subheaders == ["Modal Results", "Response Spectrum Results", "Time History Results"]
