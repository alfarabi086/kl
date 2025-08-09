import { useRef, useState } from 'react';

export default function UploadCard({ onUpload }) {
  const fileInput = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setError(null);
    setUploading(true);
    try {
      await onUpload(file);
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      fileInput.current.value = null;
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow p-6 space-y-4">
      <h2 className="text-lg font-semibold">Upload .nc File</h2>
      <input
        ref={fileInput}
        type="file"
        accept=".nc"
        onChange={handleFileChange}
        disabled={uploading}
        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4
                   file:rounded-full file:border-0 file:text-sm file:font-semibold
                   file:bg-blue-100 file:text-blue-700 hover:file:bg-blue-200
                   disabled:opacity-50 disabled:cursor-not-allowed"
      />
      {uploading && <p className="text-blue-600">Uploading…</p>}
      {!uploading && !error && <p className="text-green-600">Ready to upload</p>}
      {error && <p className="text-red-500">{error}</p>}
    </div>
  )
}