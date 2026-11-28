import type { LiveState } from "@f1/contract";
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useLiveSession, type EventSourceLike } from "./use-live-session";

class FakeEventSource implements EventSourceLike {
  static instances: FakeEventSource[] = [];
  readyState = 0;
  close = vi.fn(() => {
    this.readyState = 2;
  });
  private listeners = new Map<string, ((e: MessageEvent) => void)[]>();
  constructor(public url: string) {
    FakeEventSource.instances.push(this);
  }
  addEventListener(type: string, listener: (e: MessageEvent) => void) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
  }
  emit(type: string, data?: unknown, id?: string) {
    if (type === "error") this.readyState = 2; // the browser gave up on this source
    else this.readyState = 1;
    const event = new MessageEvent(type, { data: data === undefined ? "" : JSON.stringify(data), lastEventId: id ?? "" });
    this.listeners.get(type)?.forEach((l) => l(event));
  }
}

const source = (i: number) => FakeEventSource.instances[i]!;
const factory = (url: string) => new FakeEventSource(url);
const opts = { eventSourceFactory: factory, now: () => Date.now() };

function liveState(status: LiveState["status"], numbers: number[] = []): LiveState {
  return {
    drivers: numbers.map((n, i) => ({
      number: n,
      position: i + 1,
      code: `D${n}`,
      last_lap_ms: null,
      best_lap_ms: null,
      best_sectors_ms: [null, null, null],
      gap_to_leader: i === 0 ? null : `+${i}.000`,
      interval: null,
      compound: null,
      tyre_age_laps: null,
      in_pit: false,
      retired: false,
      sectors: ["none", "none", "none"],
    })),
    flag: "GREEN",
    lap: 3,
    session_best_lap_ms: null,
    session_best_sectors_ms: [null, null, null],
    last_seq: status === "waiting" ? 0 : 7,
    status,
  };
}

beforeEach(() => {
  vi.useFakeTimers();
  FakeEventSource.instances = [];
});
afterEach(() => vi.useRealTimers());

describe("useLiveSession", () => {
  it("parses tower events into state", async () => {
    const { result } = renderHook(() => useLiveSession(9158, opts));
    expect(result.current.connection).toBe("connecting");
    expect(source(0).url).toBe("/v1/live/9158/stream");
    act(() => source(0).emit("tower", liveState("live", [4, 81, 1]), "7"));
    expect(result.current.state?.drivers.map((d) => d.number)).toEqual([4, 81, 1]);
    expect(result.current.connection).toBe("live");
    expect(result.current.lastEventAt).toBe(Date.now());
  });

  it("goes stale after 20s of silence", async () => {
    const { result } = renderHook(() => useLiveSession(9158, opts));
    act(() => source(0).emit("tower", liveState("live", [4]), "7"));
    act(() => vi.advanceTimersByTime(19_000));
    expect(result.current.connection).toBe("live");
    act(() => vi.advanceTimersByTime(2_000));
    expect(result.current.connection).toBe("stale");
    act(() => source(0).emit("tower", liveState("live", [4]), "8"));
    expect(result.current.connection).toBe("live");
  });

  it("reconnects with backoff after an error", async () => {
    const spy = vi.fn(factory);
    const { result } = renderHook(() => useLiveSession(9158, { eventSourceFactory: spy }));
    act(() => source(0).emit("error"));
    expect(result.current.connection).toBe("reconnecting");
    expect(source(0).close).toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(999));
    expect(spy).toHaveBeenCalledTimes(1);
    act(() => vi.advanceTimersByTime(1));
    expect(spy).toHaveBeenCalledTimes(2);
    // second failure waits 2 s, not 1 s
    act(() => source(1).emit("error"));
    act(() => vi.advanceTimersByTime(1_999));
    expect(spy).toHaveBeenCalledTimes(2);
    act(() => vi.advanceTimersByTime(1));
    expect(spy).toHaveBeenCalledTimes(3);
    // a received event resets the backoff
    act(() => source(2).emit("tower", liveState("live", [4]), "9"));
    act(() => source(2).emit("error"));
    act(() => vi.advanceTimersByTime(1_000));
    expect(spy).toHaveBeenCalledTimes(4);
  });

  it("caps the backoff at 15s", async () => {
    const spy = vi.fn(factory);
    renderHook(() => useLiveSession(9158, { eventSourceFactory: spy }));
    for (const delay of [1_000, 2_000, 4_000, 8_000, 15_000, 15_000]) {
      act(() => FakeEventSource.instances.at(-1)!.emit("error"));
      const before = spy.mock.calls.length;
      act(() => vi.advanceTimersByTime(delay - 1));
      expect(spy).toHaveBeenCalledTimes(before);
      act(() => vi.advanceTimersByTime(1));
      expect(spy).toHaveBeenCalledTimes(before + 1);
    }
  });

  it("shows waiting state when server status is waiting", async () => {
    const { result } = renderHook(() => useLiveSession(9158, opts));
    act(() => source(0).emit("tower", liveState("waiting")));
    expect(result.current.state?.status).toBe("waiting");
    expect(result.current.state?.drivers).toEqual([]);
    // waiting streams only carry (invisible) heartbeats, so silence is not staleness
    act(() => vi.advanceTimersByTime(60_000));
    expect(result.current.connection).toBe("live");
  });

  it("closes the EventSource on unmount", async () => {
    const { unmount } = renderHook(() => useLiveSession(9158, opts));
    const es = source(0);
    unmount();
    expect(es.close).toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(60_000));
    expect(FakeEventSource.instances).toHaveLength(1);
  });
});
