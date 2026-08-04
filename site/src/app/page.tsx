'use client';
import { useState, useEffect, useMemo } from 'react';
import Papa from 'papaparse';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

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

export default function ExplorePage() {
  const [data, setData] = useState<StudyRow[]>([]);
  const [insights, setInsights] = useState<any>(null);
  
  const [cancerFilter, setCancerFilter] = useState<string>('All');
  const [techFilter, setTechFilter] = useState<string>('All');
  
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
      
    fetch('/data/insights_summary.json')
      .then(res => res.json())
      .then(json => setInsights(json));
  }, []);

  const parseListString = (str: string) => {
    if (!str) return [];
    try {
      return JSON.parse(str.replace(/'/g, '"'));
    } catch {
      return [str];
    }
  };

  const uniqueCancerTypes = useMemo(() => {
    const types = new Set<string>();
    data.forEach(row => {
      const parsed = parseListString(row.cancer_types);
      parsed.forEach((t: string) => types.add(t));
    });
    return Array.from(types).sort();
  }, [data]);

  const uniqueTechnologies = useMemo(() => {
    const techs = new Set<string>();
    data.forEach(row => {
      if (row.technology_raw) techs.add(row.technology_raw);
      else if (row.technology) techs.add(row.technology);
    });
    return Array.from(techs).sort();
  }, [data]);

  const filteredData = useMemo(() => {
    return data.filter(row => {
      const cTypes = parseListString(row.cancer_types);
      const passCancer = cancerFilter === 'All' || cTypes.includes(cancerFilter);
      const passTech = techFilter === 'All' || row.technology_raw === techFilter || row.technology === techFilter;
      return passCancer && passTech;
    });
  }, [data, cancerFilter, techFilter]);

  const cancerDistribution = useMemo(() => {
    const counts: Record<string, number> = {};
    filteredData.forEach(row => {
      const cTypes = parseListString(row.cancer_types);
      cTypes.forEach((t: string) => {
        counts[t] = (counts[t] || 0) + 1;
      });
    });
    return Object.entries(counts).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count).slice(0, 7);
  }, [filteredData]);

  const techDistribution = useMemo(() => {
    const counts: Record<string, number> = {};
    filteredData.forEach(row => {
      const t = row.technology || 'Unknown';
      counts[t] = (counts[t] || 0) + 1;
    });
    return Object.entries(counts).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count).slice(0, 7);
  }, [filteredData]);

  return (
    <div className="flex h-screen overflow-hidden bg-[#05080F]">
      <div className="flex-1 flex flex-col overflow-y-auto">
        <header className="px-8 py-8 border-b border-white/5 bg-[#0A0F1C]/50 backdrop-blur-md sticky top-0 z-10">
          <h2 className="text-3xl font-bold text-white tracking-tight mb-2">3CA Knowledge Graph</h2>
          <p className="text-white/60 text-sm">Cancer & Cell-Cell Adhesion Explorer</p>
          
          <div className="flex items-center gap-6 mt-8">
            <div className="flex flex-col gap-2 flex-1 max-w-xs">
              <label className="text-white/50 text-xs font-medium uppercase tracking-wider">Cancer Type</label>
              <select 
                className="bg-[#05080F] border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#EF4444]"
                value={cancerFilter}
                onChange={e => setCancerFilter(e.target.value)}
              >
                <option value="All">Multiple</option>
                {uniqueCancerTypes.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            
            <div className="flex flex-col gap-2 flex-1 max-w-xs">
              <label className="text-white/50 text-xs font-medium uppercase tracking-wider">Technology</label>
              <select 
                className="bg-[#05080F] border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-[#EF4444]"
                value={techFilter}
                onChange={e => setTechFilter(e.target.value)}
              >
                <option value="All">All</option>
                {uniqueTechnologies.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            
            <div className="flex items-end self-stretch pb-0">
              <button className="bg-[#3b82f6] hover:bg-[#2563eb] text-white px-5 py-2 rounded-md text-sm font-medium transition-colors h-[38px]">
                Apply Filters
              </button>
            </div>
          </div>
        </header>
        
        <main className="p-8">
          <div className="bg-[#0A0F1C] rounded-xl border border-white/5 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-white/5 text-white/50 border-b border-white/5">
                  <tr>
                    <th className="px-5 py-4 font-medium">Study ID</th>
                    <th className="px-5 py-4 font-medium">Title</th>
                    <th className="px-5 py-4 font-medium">Cancer Type</th>
                    <th className="px-5 py-4 font-medium">Technology</th>
                    <th className="px-5 py-4 font-medium">Sample Count</th>
                    <th className="px-5 py-4 font-medium">Data Type (Cells)</th>
                    <th className="px-5 py-4 font-medium">Year</th>
                    <th className="px-5 py-4 font-medium">Publication</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {filteredData.slice(0, 100).map((row, i) => (
                    <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-5 py-3 text-white/80 font-mono">ST{row.study_id.split('.')[0].padStart(3, '0')}</td>
                      <td className="px-5 py-3 text-white max-w-[300px] truncate" title={row.title}>{row.title}</td>
                      <td className="px-5 py-3 text-white/70">{parseListString(row.cancer_types).join(', ')}</td>
                      <td className="px-5 py-3 text-white/70">{row.technology_raw || row.technology}</td>
                      <td className="px-5 py-3 text-white/70">{row.samples}</td>
                      <td className="px-5 py-3 text-white/70">{row.cells} cells</td>
                      <td className="px-5 py-3 text-white/70">{row.year}</td>
                      <td className="px-5 py-3 text-white/70">{row.author}</td>
                    </tr>
                  ))}
                  {filteredData.length === 0 && (
                    <tr>
                      <td colSpan={8} className="px-5 py-10 text-center text-white/40">No studies match the selected filters.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t border-white/5 text-xs text-white/40 text-center">
              Showing {Math.min(filteredData.length, 100)} of {filteredData.length} total datasets
            </div>
          </div>
        </main>
      </div>

      <div className="w-[340px] bg-[#0A0F1C] border-l border-white/5 flex flex-col flex-shrink-0 overflow-y-auto">
        <div className="p-8">
          <h3 className="text-2xl font-bold text-white mb-2">Insights</h3>
          <p className="text-white/50 text-sm mb-10">Highlights from the data.</p>
          
          <div className="mb-12">
            <h4 className="text-white text-base font-medium mb-3">Top Dataset Links</h4>
            {insights?.strongest_links && insights.strongest_links.length > 0 && (
              <p className="text-white/60 text-xs italic mb-5 leading-relaxed border-l-2 border-[#3b82f6] pl-3 py-2 bg-[#3b82f6]/5">
                For example, <strong>ST{insights.strongest_links[0].study_A.toString().padStart(3, '0')}</strong> ({insights.strongest_links[0].cancer_type_A}) and <strong>ST{insights.strongest_links[0].study_B.toString().padStart(3, '0')}</strong> ({insights.strongest_links[0].cancer_type_B}) share the <strong>{insights.strongest_links[0].shared_diseases[0]}</strong> disease label despite being filed under different cancer-type categories — this is the kind of cross-organ link 3CA&apos;s original site doesn&apos;t surface.
              </p>
            )}
            <ul className="flex flex-col gap-5">
              {insights?.strongest_links?.slice(0, 4).map((link: any, i: number) => (
                <li key={i} className="text-sm">
                  <span className="text-white/80">{i + 1}. </span>
                  <span className="text-[#3b82f6] cursor-pointer hover:underline">ST{link.study_A.toString().padStart(3, '0')}</span>
                  <span className="text-white/50"> - {link.cancer_type_A}</span>
                  <br />
                  <span className="text-white/30 ml-4">& </span>
                  <span className="text-[#3b82f6] cursor-pointer hover:underline">ST{link.study_B.toString().padStart(3, '0')}</span>
                  <span className="text-white/50"> - {link.cancer_type_B}</span>
                  <div className="text-white/40 text-xs mt-2 ml-4 pl-3 border-l border-white/10 italic">
                    {link.shared_diseases.join(', ')}
                  </div>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="mb-12">
            <h4 className="text-white text-base font-medium mb-5">Distribution by Cancer Type</h4>
            <div className="h-[220px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cancerDistribution} margin={{ top: 0, right: 0, left: -25, bottom: 60 }}>
                  <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} angle={-45} textAnchor="end" interval={0} />
                  <YAxis tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#05080F', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', fontSize: '12px' }}
                    itemStyle={{ color: '#3b82f6' }}
                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div>
            <h4 className="text-white text-base font-medium mb-5">Distribution by Technology</h4>
            <div className="h-[220px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={techDistribution} margin={{ top: 0, right: 0, left: -25, bottom: 60 }}>
                  <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} angle={-45} textAnchor="end" interval={0} />
                  <YAxis tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#05080F', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', fontSize: '12px' }}
                    itemStyle={{ color: '#3b82f6' }}
                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
