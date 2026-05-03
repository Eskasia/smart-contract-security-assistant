import { useSettingsStore } from "../store/analysisStore";

export function usePersistedSettings() {
  const settings = useSettingsStore((state) => state.settings);
  const updateSettings = useSettingsStore((state) => state.updateSettings);
  return { settings, updateSettings };
}
