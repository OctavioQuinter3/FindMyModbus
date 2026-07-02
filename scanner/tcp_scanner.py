from pymodbus.client import ModbusTcpClient
from .models import DeviceResult, Protocol


def scan_tcp(config, result_callback, progress_callback, stop_event):
    client = ModbusTcpClient(config.host, port=config.tcp_port, timeout=config.timeout)
    if not client.connect():
        progress_callback(1.0, f"Failed to connect to {config.host}:{config.tcp_port}")
        return

    total = (config.slave_end - config.slave_start + 1) * len(config.function_codes)
    attempted = 0

    for unit in range(config.slave_start, config.slave_end + 1):
        if stop_event and stop_event.is_set():
            client.close()
            return

        for fc in config.function_codes:
            attempted += 1
            if stop_event and stop_event.is_set():
                client.close()
                return

            progress_callback(attempted / total, f"TCP {config.host}:{config.tcp_port} | Unit {unit} | FC {fc}")

            try:
                resp = None
                if fc == 1:
                    resp = client.read_coils(0, config.registers_per_slave, device_id=unit)
                elif fc == 2:
                    resp = client.read_discrete_inputs(0, config.registers_per_slave, device_id=unit)
                elif fc == 3:
                    resp = client.read_holding_registers(0, config.registers_per_slave, device_id=unit)
                elif fc == 4:
                    resp = client.read_input_registers(0, config.registers_per_slave, device_id=unit)

                if resp is not None and not resp.isError():
                    values = getattr(resp, "registers", None) or getattr(resp, "bits", [])
                    for i, val in enumerate(values):
                        result_callback(DeviceResult(
                            slave_id=unit, function_code=fc, address=i,
                            value=int(val), protocol=Protocol.TCP,
                            connection=f"{config.host}:{config.tcp_port}",
                        ))
            except Exception:
                pass

    client.close()
    progress_callback(1.0, "Scan complete")
