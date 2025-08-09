import { Line } from 'react-chartjs-2';
import 'chart.js/auto';

export default function GraphCard({ data, summary }) {
  const labels = data.map((pt) => pt.x);
  const values = data.map((pt) => pt.y);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Processed Data',
        data: values,
        tension: 0.4,
        borderWidth: 2,
      },
    ],
  };

  return (
    <div className="bg-white rounded-2xl shadow p-6 space-y-4">
      <h2 className="text-lg font-semibold">Results</h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p><strong>Mean:</strong> {summary.mean}</p>
          <p><strong>Std Dev:</strong> {summary.std}</p>
        </div>
        <div>
          <Line data={chartData} />
        </div>
      </div>
    </div>
  );
}