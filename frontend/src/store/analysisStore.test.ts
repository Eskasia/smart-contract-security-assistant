import { beforeEach, describe, expect, it } from "vitest";

import { defaultSettings, useSettingsStore } from "./analysisStore";

type PersistedSettingsStore = typeof useSettingsStore & {
  persist: {
    rehydrate: () => Promise<void> | void;
  };
};

describe("useSettingsStore", () => {
  beforeEach(() => {
    localStorage.clear();
    useSettingsStore.setState({ settings: defaultSettings });
  });

  it("migrates legacy echidnaEnabled settings to externalTools", async () => {
    const legacySettings = {
      ...defaultSettings,
      apiToken: "persisted-token",
      echidnaEnabled: true,
    };
    const { externalTools: _externalTools, ...persistedLegacySettings } = legacySettings;
    localStorage.setItem(
      "sca_settings_v1",
      JSON.stringify({
        state: { settings: persistedLegacySettings },
        version: 0,
      }),
    );

    await (useSettingsStore as PersistedSettingsStore).persist.rehydrate();

    expect(useSettingsStore.getState().settings.externalTools).toEqual(["echidna"]);
    expect(useSettingsStore.getState().settings.apiToken).toBe("");
  });
});

