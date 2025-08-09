export default function InfoPanel({ info }) {
  return (
    <div className="bg-white rounded-2xl shadow p-6 space-y-2">
      <h2 className="text-lg font-semibold">File Details</h2>
      <p><strong>Message:</strong> {info.message}</p>
      <p><strong>File ID:</strong> {info.file_id}</p>
      <p><strong>Name:</strong> {info.file_name}</p>
      <p><strong>Latitude:</strong> {info.latitude}</p>
      <p><strong>Longitude:</strong> {info.longitude}</p>
      <p><strong>Years Available:</strong> {info.years.join(', ')}</p>
    </div>
  );
}