import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ground_motion import GroundMotionConfig, read_ground_motion
from newmark_solver import NewmarkTimeHistorySolver, build_earthquake_force_history
from results import THAResults


def test_ground_motion_two_column_cm_s2(tmp_path):
    """Verify: two-column records preserve time/raw values and convert cm/s2 to m/s2."""
    gm_file = tmp_path / "two_column.txt"
    gm_file.write_text("header\n0.00 0.0\n0.02 100.0\n", encoding="utf-8")

    record = read_ground_motion(
        GroundMotionConfig(
            file_path=str(gm_file),
            input_format="time_acceleration",
            skip_header_lines=1,
            acceleration_unit="cm/s2",
        )
    )

    assert record.time_vector == [0.0, 0.02]
    assert record.acceleration_raw == [0.0, 100.0]
    assert record.dt == 0.02
    assert record.acceleration_si == [0.0, 1.0]


def test_ground_motion_acceleration_only_with_dt(tmp_path):
    """Verify: acceleration-only records generate time from user-supplied dt."""
    gm_file = tmp_path / "accel_only.txt"
    gm_file.write_text("skip\n10.0\n20.0\n30.0\n", encoding="utf-8")

    record = read_ground_motion(
        GroundMotionConfig(
            file_path=str(gm_file),
            input_format="acceleration_only",
            time_step_dt=0.004,
            acceleration_column=0,
            first_line=2,
            acceleration_unit="m/s2",
        )
    )

    assert record.time_vector == [0.0, 0.004, 0.008]
    assert record.acceleration_si == [10.0, 20.0, 30.0]
    assert record.num_steps == 3


def test_acceleration_only_single_column_default(tmp_path):
    """Verify: one-value rows work without overriding the default acceleration column."""
    gm_file = tmp_path / "single_column.txt"
    gm_file.write_text("0.5\n1.5\n", encoding="utf-8")

    record = read_ground_motion(
        GroundMotionConfig(
            file_path=str(gm_file),
            input_format="acceleration_only",
            time_step_dt=0.01,
        )
    )

    assert record.time_vector == [0.0, 0.01]
    assert record.acceleration_raw == [0.5, 1.5]
    assert record.acceleration_si == [0.5, 1.5]


def test_ground_motion_unit_conversion_and_scale_factor(tmp_path):
    """Verify: unit conversion is applied before scale factor."""
    gm_file = tmp_path / "units.txt"
    gm_file.write_text("1.0\n100.0\n1000.0\n", encoding="utf-8")

    g_record = read_ground_motion(
        GroundMotionConfig(str(gm_file), "acceleration_only", 0.01, acceleration_column=0, last_line=1, acceleration_unit="g")
    )
    cm_record = read_ground_motion(
        GroundMotionConfig(str(gm_file), "acceleration_only", 0.01, acceleration_column=0, first_line=2, last_line=2, acceleration_unit="cm/s2", scale_factor=2.0)
    )
    mm_record = read_ground_motion(
        GroundMotionConfig(str(gm_file), "acceleration_only", 0.01, acceleration_column=0, first_line=3, last_line=3, acceleration_unit="mm/s2")
    )

    assert abs(g_record.acceleration_si[0] - 9.80665) < 1e-12
    assert cm_record.acceleration_si == [2.0]
    assert mm_record.acceleration_si == [1.0]


def test_earthquake_force_history_equals_minus_M_r_ag():
    """Verify: P(t) = -M r ag(t)."""
    M = [[2.0, 0.0], [0.0, 3.0]]
    r = [1.0, 0.0]

    force_history = build_earthquake_force_history(M, r, [0.0, 4.0])

    assert force_history == [[-0.0, -0.0], [-8.0, -0.0]]


def test_newmark_tha_result_histories_and_peaks(tmp_path):
    """Verify: one SDOF Newmark step returns histories, peaks, and source metadata."""
    gm_file = tmp_path / "step.txt"
    gm_file.write_text("0.0 0.0\n1.0 1.0\n", encoding="utf-8")
    record = read_ground_motion(GroundMotionConfig(str(gm_file), acceleration_unit="m/s2"))

    results = NewmarkTimeHistorySolver([[4.0]], [[2.0]], [[0.0]]).solve_ground_motion(record, [1.0])

    assert isinstance(results, THAResults)
    assert results.time_vector == [0.0, 1.0]
    assert results.applied_force_history == [[-0.0], [-2.0]]
    assert len(results.displacement_history) == 2
    assert len(results.velocity_history) == 2
    assert len(results.acceleration_history) == 2
    assert abs(results.displacement_history[1][0] - (-1.0 / 6.0)) < 1e-12
    assert results.peak_displacement[0] == abs(results.displacement_history[1][0])
    assert results.dt == 1.0
    assert results.num_steps == 2
    assert results.source_file == str(gm_file)
    assert results.base_shear_history == []
    assert results.overturning_moment_history == []
