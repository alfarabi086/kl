export default function LogPanel({ messages }) {
  return (
    <div className="bg-white rounded-2xl shadow p-4 mt-4">
      <h3 className="font-semibold">Logs & Errors</h3>
      <ul className="list-disc list-inside space-y-1 text-sm text-red-600">
        {messages.map((msg, idx) => (
          <li key={idx}>{msg}</li>
        ))}
      </ul>
    </div>
  );
}