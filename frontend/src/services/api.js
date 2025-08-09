const API_BASE = '/api/wind'; // proxied via Vite

export async function uploadFile(file) {
  const form = new FormData();
  form.append('file', file);

  let res;
  try {
    res = await fetch(`${API_BASE}/upload/`, { method: 'POST', body: form });
  } catch (err) {
    throw new Error('Network error: ' + err.message);
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Upload failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function fetchStatistics(fileId, year) {
  const payload = { file_id: fileId, year };
  let res;
  try {
    res = await fetch(`${API_BASE}/statistics/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    throw new Error('Network error: ' + err.message);
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Statistics fetch failed (${res.status}): ${text}`);
  }
  return res.json();
}