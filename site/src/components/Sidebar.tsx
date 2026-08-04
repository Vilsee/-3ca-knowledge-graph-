'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Network, Search } from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-[240px] h-screen fixed left-0 top-0 bg-[#0A0F1C] border-r border-white/5 flex flex-col z-50">
      <div className="p-6 border-b border-white/5">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#EF4444] to-[#F97316] flex items-center justify-center shadow-[0_0_15px_rgba(239,68,68,0.3)] shrink-0">
            <Network size={18} className="text-white" />
          </div>
          <h1 className="text-white font-bold tracking-tight leading-tight text-sm">3CA Knowledge Graph</h1>
        </div>
        <p className="text-white/50 text-[11px] font-medium uppercase tracking-wider">Cancer & Cell-Cell Adhesion Explorer</p>
      </div>

      <nav className="flex-1 py-6 px-3 flex flex-col gap-2">
        <Link 
          href="/" 
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${pathname === '/' ? 'bg-white/10 text-white font-medium' : 'text-white/60 hover:bg-white/5 hover:text-white'}`}
        >
          <LayoutDashboard size={18} />
          <span className="text-sm">Explore</span>
        </Link>
        <Link 
          href="/search" 
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${pathname === '/search' ? 'bg-white/10 text-white font-medium' : 'text-white/60 hover:bg-white/5 hover:text-white'}`}
        >
          <Search size={18} />
          <span className="text-sm">Search</span>
        </Link>
        <Link 
          href="/graph" 
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${pathname === '/graph' ? 'bg-white/10 text-white font-medium' : 'text-white/60 hover:bg-white/5 hover:text-white'}`}
        >
          <Network size={18} />
          <span className="text-sm">Graph</span>
        </Link>
      </nav>
    </div>
  );
}
