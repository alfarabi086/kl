export default function StatistikPanel({ data }) {
  const { wind_speed_statistics, wind_direction_statistics, data_info } = data;
  return (
    <div className="bg-white rounded-2xl shadow p-6 space-y-4">
      <h2 className="text-lg font-semibold">Statistik Wind Data</h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="font-semibold">Kecepatan Angin (m/s)</h3>
          <ul className="list-disc list-inside">
            {Object.entries(wind_speed_statistics).map(([k, v]) => (
              <li key={k}>{k}: {v}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="font-semibold">Arah Angin (°)</h3>
          <ul className="list-disc list-inside">
            {Object.entries(wind_direction_statistics).map(([k, v]) => (
              <li key={k}>{k}: {v}</li>
            ))}
          </ul>
        </div>
      </div>
      <div>
        <h3 className="font-semibold">Data Info</h3>
        <ul className="list-disc list-inside">
          {Object.entries(data_info).map(([k, v]) => (
            <li key={k}>{k}: {v}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}