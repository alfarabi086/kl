import { useState, useEffect } from 'react';
import { uploadFile, fetchStatistics } from './services/api';
import UploadCard from './components/UploadCard';
import InfoPanel from './components/InfoPanel';
import YearMenu from './components/YearMenu';
import FeatureMenu from './components/FeatureMenu';
import StatistikPanel from './components/StatistikPanel';
import LogPanel from './components/LogPanel';

export default function App() {
  const [uploadInfo, setUploadInfo] = useState(null);
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedFeature, setSelectedFeature] = useState('');
  const [statistikData, setStatistikData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Handle file upload
  const handleUpload = async (file) => {
    setError(null);
    setStatistikData(null);
    setSelectedYear('');
    setSelectedFeature('');
    try {
      const info = await uploadFile(file);
      setUploadInfo(info);
    } catch (e) {
      setError(e.message);
    }
  };

  // Trigger Statistik API on feature+year
  useEffect(() => {
    if (selectedFeature === 'statistik' && uploadInfo && selectedYear) {
      setLoading(true);
      fetchStatistics(uploadInfo.file_id, selectedYear)
        .then(data => {
          setStatistikData(data);
          setError(null);
        })
        .catch(err => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [selectedFeature, selectedYear, uploadInfo]);

  return (
    <div className="min-h-screen bg-blue-50">
      <header className="bg-blue-600 text-white p-4 text-xl font-semibold">
        Wind Data Processor
      </header>
      <main className="p-6 space-y-6">
        <UploadCard onUpload={handleUpload} />

        {uploadInfo && <InfoPanel info={uploadInfo} />}

        {uploadInfo && (
          <div className="space-y-4">
            <YearMenu
              years={uploadInfo.years}
              selectedYear={selectedYear}
              onSelect={setSelectedYear}
            />
            <FeatureMenu
              selectedFeature={selectedFeature}
              onSelect={setSelectedFeature}
            />
          </div>
        )}

        {loading && <p className="text-gray-600">Loading Statistik…</p>}

        {statistikData && selectedFeature === 'statistik' && (
          <StatistikPanel data={statistikData} />
        )}

        {error && <LogPanel messages={[error]} />}
      </main>
      <footer className="bg-blue-600 text-white p-4 text-sm text-center">
        © 2025 Teknik Kelautan
      </footer>
    </div>
  );
}