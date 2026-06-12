from dataclasses import dataclass


SUPPORTED_ACCELERATION_UNITS = ("m/s2", "cm/s2", "mm/s2", "g")
SUPPORTED_INPUT_FORMATS = ("acceleration_only", "time_acceleration")


@dataclass
class GroundMotionConfig:
    """Backend settings for reading an earthquake ground-motion record."""

    file_path: str
    input_format: str = "time_acceleration"
    time_step_dt: float | None = None
    time_column: int = 0
    acceleration_column: int = 1
    first_line: int | None = None
    last_line: int | None = None
    skip_header_lines: int = 0
    acceleration_unit: str = "m/s2"
    scale_factor: float = 1.0
    excitation_direction: str = "x"


@dataclass
class GroundMotionRecord:
    """Ground-motion values normalized for solver use."""

    time_vector: list
    acceleration_raw: list
    acceleration_si: list
    dt: float
    num_steps: int
    source_file: str
    acceleration_unit: str
    scale_factor: float
    input_format: str


def read_ground_motion(config: GroundMotionConfig) -> GroundMotionRecord:
    """Read a ground-motion text file and convert acceleration to m/s2."""
    _validate_config(config)
    time_values = []
    acceleration_raw = []

    with open(config.file_path, "r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number <= config.skip_header_lines:
                continue
            if config.first_line is not None and line_number < config.first_line:
                continue
            if config.last_line is not None and line_number > config.last_line:
                continue

            stripped = line.strip()
            if not stripped:
                continue
            parts = _split_numeric_columns(stripped)

            if config.input_format == "acceleration_only":
                acceleration_raw.append(float(_acceleration_only_value(parts, config.acceleration_column)))
            else:
                time_values.append(float(parts[config.time_column]))
                acceleration_raw.append(float(parts[config.acceleration_column]))

    if not acceleration_raw:
        raise ValueError("Ground-motion file did not contain any usable acceleration rows.")

    if config.input_format == "acceleration_only":
        if config.time_step_dt is None or config.time_step_dt <= 0.0:
            raise ValueError("time_step_dt must be supplied for acceleration_only records.")
        dt = float(config.time_step_dt)
        time_values = [i * dt for i in range(len(acceleration_raw))]
    else:
        if len(time_values) != len(acceleration_raw):
            raise ValueError("Time and acceleration vectors have different lengths.")
        dt = _infer_dt(time_values)

    acceleration_si = [
        convert_acceleration_to_si(value, config.acceleration_unit) * config.scale_factor
        for value in acceleration_raw
    ]

    return GroundMotionRecord(
        time_vector=time_values,
        acceleration_raw=acceleration_raw,
        acceleration_si=acceleration_si,
        dt=dt,
        num_steps=len(acceleration_raw),
        source_file=config.file_path,
        acceleration_unit=config.acceleration_unit,
        scale_factor=config.scale_factor,
        input_format=config.input_format,
    )


def convert_acceleration_to_si(value: float, unit: str) -> float:
    """Convert acceleration to m/s2."""
    if unit == "m/s2":
        return float(value)
    if unit == "cm/s2":
        return float(value) / 100.0
    if unit == "mm/s2":
        return float(value) / 1000.0
    if unit == "g":
        return float(value) * 9.80665
    raise ValueError(f"Unsupported acceleration unit '{unit}'.")


def _validate_config(config: GroundMotionConfig) -> None:
    if config.input_format not in SUPPORTED_INPUT_FORMATS:
        raise ValueError(f"Unsupported ground-motion input format '{config.input_format}'.")
    if config.acceleration_unit not in SUPPORTED_ACCELERATION_UNITS:
        raise ValueError(f"Unsupported acceleration unit '{config.acceleration_unit}'.")
    if config.first_line is not None and config.first_line < 1:
        raise ValueError("first_line is 1-based and must be positive.")
    if config.last_line is not None and config.last_line < 1:
        raise ValueError("last_line is 1-based and must be positive.")
    if (
        config.first_line is not None
        and config.last_line is not None
        and config.last_line < config.first_line
    ):
        raise ValueError("last_line must be greater than or equal to first_line.")


def _split_numeric_columns(line: str) -> list:
    return line.replace(",", " ").split()


def _acceleration_only_value(parts: list, acceleration_column: int) -> str:
    if len(parts) == 1:
        return parts[0]
    return parts[acceleration_column]


def _infer_dt(time_vector: list) -> float:
    if len(time_vector) < 2:
        return 0.0
    return time_vector[1] - time_vector[0]
