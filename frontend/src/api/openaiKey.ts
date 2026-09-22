let openAIKey: string | null = null;

export function setOpenAIKey(key: string) {
  openAIKey = key.trim() || null;
}

export function clearOpenAIKey() {
  openAIKey = null;
}

export function getOpenAIKey() {
  return openAIKey;
}