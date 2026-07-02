from pymodbus.client import ModbusSerialClient
from .models import DeviceResult, Protocol, BAUD_RATES


def scan_rtu(config, result_callback, progress_callback, stop_event, existing_client=None):
    use_existing = existing_client is not None and not config.auto_baud
    baudrates = [config.baudrate] if use_existing else (BAUD_RATES if config.auto_baud else [config.baudrate])
    found_slaves = set()
    total = len(baudrates) * (config.slave_end - config.slave_start + 1) * len(config.function_codes)
    attempted = 0

    for baud in baudrates:
        if not use_existing:
            client = ModbusSerialClient(
                port=config.port, baudrate=baud, bytesize=8,
                parity=config.parity, stopbits=config.stopbits, timeout=config.timeout,
            )
            if not client.connect():
                attempted += (config.slave_end - config.slave_start + 1) * len(config.function_codes)
                continue
        else:
            client = existing_client

        for slave in range(config.slave_start, config.slave_end + 1):
            if slave in found_slaves:
                attempted += len(config.function_codes)
                continue
            if stop_event and stop_event.is_set():
                if not use_existing:
                    client.close()
                return

            for fc in config.function_codes:
                attempted += 1
                if stop_event and stop_event.is_set():
                    if not use_existing:
                        client.close()
                    return

                progress_callback(attempted / total, f"RTU {config.port} @ {baud} baud | Slave {slave} | FC {fc}")

                try:
                    resp = None
                    if fc == 1:
                        resp = client.read_coils(0, config.registers_per_slave, device_id=slave)
                    elif fc == 2:
                        resp = client.read_discrete_inputs(0, config.registers_per_slave, device_id=slave)
                    elif fc == 3:
                        resp = client.read_holding_registers(0, config.registers_per_slave, device_id=slave)
                    elif fc == 4:
                        resp = client.read_input_registers(0, config.registers_per_slave, device_id=slave)

                    if resp is not None and not resp.isError():
                        found_slaves.add(slave)
                        values = getattr(resp, "registers", None) or getattr(resp, "bits", [])
                        for i, val in enumerate(values):
                            result_callback(DeviceResult(
                                slave_id=slave, function_code=fc, address=i,
                                value=int(val), protocol=Protocol.RTU,
                                baudrate=baud, connection=config.port,
                            ))
                except Exception:
                    pass

        if not use_existing:
            client.close()

    progress_callback(1.0, "Scan complete")
