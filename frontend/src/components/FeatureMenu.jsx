const FEATURES = [
  { key: 'statistik', label: 'Statistik' },
  { key: 'analisis', label: 'Analisis Distribusi' },
  { key: 'terbaik', label: 'Distribusi Terbaik' },
  { key: 'parameter', label: 'Parameter Distribusi' },
  { key: 'potensi', label: 'Potensi Energi' },
];

export default function FeatureMenu({ selectedFeature, onSelect }) {
  return (
    <div className="bg-white rounded-2xl shadow p-6 space-y-2">
      <h2 className="text-lg font-semibold">Pilih Fitur</h2>
      <div className="flex flex-wrap gap-2">
        {FEATURES.map((f) => (
          <button
            key={f.key}
            onClick={() => onSelect(f.key)}
            className={
              `px-4 py-2 rounded-full transition-colors ` +
              (selectedFeature === f.key
                ? 'bg-green-500 text-white'
                : 'bg-green-100 hover:bg-green-200')
            }
          >
            {f.label}
          </button>
        ))}
      </div>
    </div>
  );
}