export default function YearMenu({ years, selectedYear, onSelect }) {
  return (
    <div className="bg-white rounded-2xl shadow p-6 space-y-2">
      <h2 className="text-lg font-semibold">Pilih Tahun</h2>
      <div className="flex flex-wrap gap-2">
        {years.map((yr) => (
          <button
            key={yr}
            onClick={() => onSelect(yr)}
            className={
              `px-4 py-2 rounded-full transition-colors ` +
              (selectedYear === yr
                ? 'bg-blue-500 text-white'
                : 'bg-blue-100 hover:bg-blue-200')
            }
          >
            {yr}
          </button>
        ))}
      </div>
    </div>
  );
}