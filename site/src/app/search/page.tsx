'use client';
import { useState, useEffect, useMemo } from 'react';
import Papa from 'papaparse';
import { Search } from 'lucide-react';

type StudyRow = {
  study_id: string;
  title: string;
  author: string;
  year: string;
  technology: string;
  technology_raw: string;
  samples: string;
  cells: string;
  cancer_types: string;
  diseases: string;
};

export default function SearchPage() {
  const [data, setData] = useState<StudyRow[]>([]);
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<{study_id: number, score: number}[] | null>(null);

  useEffect(() => {
    fetch('/data/studies_clean.csv')
      .then(res => res.text())
      .then(csvText => {
        Papa.parse(csvText, {
          header: true,
          skipEmptyLines: true,
          complete: (results) => {
            setData(results.data as StudyRow[]);
          }
        });
      });
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setIsSearching(true);
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const json = await res.json();
      setSearchResults(json.results || []);
    } catch (err) {
      console.error(err);
      setSearchResults([]);
    }
    setIsSearching(false);
  };

  const parseListString = (str: string) => {
    if (!str) return [];
    try {
      return JSON.parse(str.replace(/'/g, '"'));
    } catch {
      return [str];
    }
  };

  // Match the returned IDs against our loaded CSV
  const matchedData = useMemo(() => {
    if (!searchResults) return null;
    
    const resultsWithRows = searchResults.map(sr => {
      // API returns integer study_id, CSV has float string like "189.0" or integer string
      const matchedRow = data.find(d => parseInt(d.study_id) === sr.study_id);
      return { ...sr, row: matchedRow };
    }).filter(r => r.row); // Keep only matches
    
    return resultsWithRows;
  }, [searchResults, data]);

  return (
    <div className="flex h-screen overflow-hidden bg-[#05080F]">
      <div className="flex-1 flex flex-col overflow-y-auto">
        <header className="px-8 py-8 border-b border-white/5 bg-[#0A0F1C]/50 backdrop-blur-md sticky top-0 z-10">
          <h2 className="text-3xl font-bold text-white tracking-tight mb-2">Semantic Search</h2>
          <p className="text-white/60 text-sm">Offline TF-IDF Search over the 3CA Knowledge Graph</p>
          
          <form onSubmit={handleSearch} className="flex items-center gap-4 mt-8 max-w-3xl">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-white/40">
                <Search size={18} />
              </div>
              <input
                type="text"
                placeholder="Search for '10x breast cancer', 'Pediatric glioma', etc..."
                className="w-full bg-[#05080F] border border-white/10 rounded-md py-3 pl-12 pr-4 text-white focus:outline-none focus:border-[#3b82f6] shadow-inner"
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
            </div>
            <button 
              type="submit" 
              disabled={isSearching}
              className="bg-[#3b82f6] hover:bg-[#2563eb] text-white px-6 py-3 rounded-md font-medium transition-colors disabled:opacity-50"
            >
              {isSearching ? 'Searching...' : 'Search'}
            </button>
          </form>
        </header>
        
        <main className="p-8">
          {matchedData && (
            <div className="bg-[#0A0F1C] rounded-xl border border-white/5 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm whitespace-nowrap">
                  <thead className="bg-white/5 text-white/50 border-b border-white/5">
                    <tr>
                      <th className="px-5 py-4 font-medium">Rank Score</th>
                      <th className="px-5 py-4 font-medium">Study ID</th>
                      <th className="px-5 py-4 font-medium">Title</th>
                      <th className="px-5 py-4 font-medium">Cancer Type</th>
                      <th className="px-5 py-4 font-medium">Disease</th>
                      <th className="px-5 py-4 font-medium">Technology</th>
                      <th className="px-5 py-4 font-medium">Year</th>
                      <th className="px-5 py-4 font-medium">Publication</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {matchedData.map((item, i) => (
                      <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                        <td className="px-5 py-3 text-[#3b82f6] font-medium">{(item.score * 100).toFixed(1)}%</td>
                        <td className="px-5 py-3 text-white/80 font-mono">ST{item.study_id.toString().padStart(3, '0')}</td>
                        <td className="px-5 py-3 text-white max-w-[250px] truncate" title={item.row!.title}>{item.row!.title}</td>
                        <td className="px-5 py-3 text-white/70">{parseListString(item.row!.cancer_types).join(', ')}</td>
                        <td className="px-5 py-3 text-white/70 max-w-[200px] truncate" title={parseListString(item.row!.diseases).join(', ')}>{parseListString(item.row!.diseases).join(', ')}</td>
                        <td className="px-5 py-3 text-white/70">{item.row!.technology_raw || item.row!.technology}</td>
                        <td className="px-5 py-3 text-white/70">{item.row!.year}</td>
                        <td className="px-5 py-3 text-white/70">{item.row!.author}</td>
                      </tr>
                    ))}
                    {matchedData.length === 0 && (
                      <tr>
                        <td colSpan={8} className="px-5 py-10 text-center text-white/40">No studies match your semantic query.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
