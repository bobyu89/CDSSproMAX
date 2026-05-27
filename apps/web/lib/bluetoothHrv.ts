"use client";

/**
 * Web Bluetooth client for Polar H10 (and any standard BLE Heart Rate Monitor).
 *
 * Heart Rate Service: 0x180D
 * Heart Rate Measurement characteristic: 0x2A37
 *
 * Caveats (Web Bluetooth gotchas — see report):
 *   - navigator.bluetooth is **only** available in Chromium-family browsers
 *     over HTTPS or localhost. Safari/Firefox/iOS will hit the `undefined`
 *     guard below and the UI should fall back to mock mode.
 *   - requestDevice() MUST be triggered from a user gesture (button click);
 *     never call it inside an effect or auto-on-mount.
 *   - On disconnect the GATT server is invalidated — caller must re-pair via
 *     a fresh button click; we expose a cleanup function from
 *     startNotifications() that stops notifications safely.
 */

export interface ParsedHrSample {
  timestampMs: number;
  rToRMs: number;
  heartRate: number;
}

export interface ParsedHrMeasurement {
  heartRate: number;
  rrIntervalsMs: number[]; // 0 or more — Polar typically sends 1-3
}

const HR_SERVICE_UUID = 0x180d;
const HR_MEASUREMENT_UUID = 0x2a37;


function hasBluetooth(): boolean {
  return (
    typeof navigator !== "undefined" &&
    "bluetooth" in navigator &&
    !!(navigator as unknown as { bluetooth?: unknown }).bluetooth
  );
}


/**
 * Parse a Heart Rate Measurement notification per the BLE spec:
 *
 *   byte 0  : flags
 *     bit 0 = HR value format (0 = uint8, 1 = uint16)
 *     bit 1 = sensor contact bit
 *     bit 2 = sensor contact supported
 *     bit 3 = energy expended present
 *     bit 4 = RR-interval present
 *   bytes 1-2 (or 1) : HR
 *   [energy 2 bytes] : if bit 3
 *   [RR pairs 2 bytes each, units = 1/1024 s] : remainder
 */
export function parseHeartRateMeasurement(data: DataView): ParsedHrMeasurement {
  const flags = data.getUint8(0);
  const hr16 = (flags & 0x01) !== 0;
  const energyPresent = (flags & 0x08) !== 0;
  const rrPresent = (flags & 0x10) !== 0;

  let offset = 1;
  let heartRate: number;
  if (hr16) {
    heartRate = data.getUint16(offset, /* littleEndian */ true);
    offset += 2;
  } else {
    heartRate = data.getUint8(offset);
    offset += 1;
  }
  if (energyPresent) offset += 2;

  const rrIntervalsMs: number[] = [];
  if (rrPresent) {
    while (offset + 1 < data.byteLength) {
      const raw = data.getUint16(offset, true);
      offset += 2;
      // Spec: RR is in units of 1/1024 s. Convert to ms.
      rrIntervalsMs.push((raw * 1000) / 1024);
    }
  }

  return { heartRate, rrIntervalsMs };
}


export async function connect(): Promise<BluetoothDevice> {
  if (!hasBluetooth()) {
    throw new Error(
      "此瀏覽器不支援 Web Bluetooth（請使用 Chrome / Edge，或改用示範模式）",
    );
  }
  const bt = (navigator as unknown as { bluetooth: Bluetooth }).bluetooth;
  const device = await bt.requestDevice({
    filters: [{ services: [HR_SERVICE_UUID] }],
    optionalServices: [HR_SERVICE_UUID],
  });
  return device;
}


export type StopFn = () => Promise<void>;


/**
 * Subscribe to Heart Rate Measurement notifications.
 *
 * Returns a cleanup function that stops notifications and disconnects.
 * `onSample` is invoked once per RR-interval; if a notification carries
 * multiple RRs we fan them out with monotonically-increasing timestamps.
 */
export async function startNotifications(
  device: BluetoothDevice,
  onSample: (sample: ParsedHrSample) => void,
): Promise<StopFn> {
  if (!device.gatt) {
    throw new Error("BLE 裝置不支援 GATT");
  }
  const server = await device.gatt.connect();
  const service = await server.getPrimaryService(HR_SERVICE_UUID);
  const char = await service.getCharacteristic(HR_MEASUREMENT_UUID);

  const listener = (event: Event) => {
    const target = event.target as unknown as { value?: DataView };
    const value = target?.value;
    if (!value) return;
    try {
      const parsed = parseHeartRateMeasurement(value);
      const now = Date.now();
      if (parsed.rrIntervalsMs.length === 0) {
        // Fall back to emitting one synthetic RR derived from HR so the
        // UI still gets *something* in the rare case the strap omits RR.
        if (parsed.heartRate > 0) {
          onSample({
            timestampMs: now,
            rToRMs: Math.round(60000 / parsed.heartRate),
            heartRate: parsed.heartRate,
          });
        }
        return;
      }
      // Spread the RRs slightly so they don't all share the same ms.
      parsed.rrIntervalsMs.forEach((rr, i) => {
        onSample({
          timestampMs: now + i,
          rToRMs: Math.round(rr),
          heartRate: parsed.heartRate,
        });
      });
    } catch {
      // ignore malformed packets
    }
  };

  char.addEventListener("characteristicvaluechanged", listener);
  await char.startNotifications();

  return async () => {
    try {
      char.removeEventListener("characteristicvaluechanged", listener);
      await char.stopNotifications().catch(() => undefined);
    } finally {
      if (device.gatt?.connected) {
        device.gatt.disconnect();
      }
    }
  };
}
