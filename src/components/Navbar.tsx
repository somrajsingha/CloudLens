import React from 'react';
import { TabType } from '../types';

interface NavbarProps {
  currentTab: TabType;
  onSelectTab: (tab: TabType) => void;
  fileCount: number;
  user: {email: string; isAdmin: boolean} | null;
  onSignIn: () => void;
  onSignOut: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentTab, onSelectTab, fileCount, user, onSignIn, onSignOut }) => {
  return (
    <header className="w-full pt-8 pb-4 px-6 md:px-12 flex flex-wrap items-center justify-between gap-4 z-20 relative">
      {/* Brand & Subtitle */}
      <div 
        onClick={() => onSelectTab('upload')} 
        className="flex items-center gap-3.5 cursor-pointer group select-none"
      >
        {/* Concentric Circle Target/Lens Logo */}
        <div className="relative flex items-center justify-center w-7 h-7 text-neutral-900 group-hover:scale-105 transition-transform">
          <svg viewBox="0 0 28 28" className="w-7 h-7" fill="none">
            {/* Outer circle */}
            <circle cx="14" cy="14" r="11.5" stroke="currentColor" strokeWidth="2.2" />
            {/* Inner circle */}
            <circle cx="14" cy="14" r="6" stroke="currentColor" strokeWidth="2.2" />
            {/* Center dot */}
            <circle cx="14" cy="14" r="2.2" fill="currentColor" />
          </svg>
        </div>

        <div className="flex flex-col">
          <span className="font-bold text-[17px] leading-tight text-neutral-900 tracking-[-0.02em]">
            CloudLens
          </span>
          <span className="text-[11px] text-neutral-500 font-normal tracking-tight leading-tight mt-0.5">
            Serverless image and document pipeline
          </span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex items-center flex-wrap gap-2 sm:gap-3 text-[13px] font-medium">
        {/* Upload Tab */}
        <button
          onClick={() => onSelectTab('upload')}
          className={`flex items-center gap-1.5 px-3.5 py-1 rounded-full transition-all duration-150 ${
            currentTab === 'upload'
              ? 'bg-white/90 text-neutral-900 border border-neutral-300/90 shadow-[0_1px_3px_rgba(0,0,0,0.06)] font-semibold'
              : 'text-neutral-600 hover:text-neutral-900 px-3'
          }`}
        >
          {currentTab === 'upload' && (
            <span className="w-1.5 h-1.5 rounded-full bg-neutral-900 inline-block" />
          )}
          <span>Upload</span>
        </button>

        {/* My files Tab */}
        <button
          onClick={() => onSelectTab('files')}
          className={`flex items-center gap-1.5 px-3.5 py-1 rounded-full transition-all duration-150 ${
            currentTab === 'files'
              ? 'bg-white/90 text-neutral-900 border border-neutral-300/90 shadow-[0_1px_3px_rgba(0,0,0,0.06)] font-semibold'
              : 'text-neutral-600 hover:text-neutral-900 px-3'
          }`}
        >
          {currentTab === 'files' && (
            <span className="w-1.5 h-1.5 rounded-full bg-neutral-900 inline-block" />
          )}
          <span>My files</span>
          {fileCount > 0 && (
            <span className="ml-0.5 px-1.5 py-0.2 text-[10px] rounded-full bg-neutral-200/80 text-neutral-700 font-normal">
              {fileCount}
            </span>
          )}
        </button>

        {/* Admin Tab */}
        <button
          onClick={() => onSelectTab('admin')}
          className={`flex items-center gap-1.5 px-3.5 py-1 rounded-full transition-all duration-150 ${
            currentTab === 'admin'
              ? 'bg-white/90 text-neutral-900 border border-neutral-300/90 shadow-[0_1px_3px_rgba(0,0,0,0.06)] font-semibold'
              : 'text-neutral-600 hover:text-neutral-900 px-3'
          }`}
        >
          {currentTab === 'admin' && (
            <span className="w-1.5 h-1.5 rounded-full bg-neutral-900 inline-block" />
          )}
          <span>Admin</span>
        </button>
        {user ? <button onClick={onSignOut} title={user.email} className="px-3 py-1 rounded-full bg-neutral-900 text-white">Sign out</button>
          : <button onClick={onSignIn} className="px-3 py-1 rounded-full bg-neutral-900 text-white">Sign in</button>}
      </nav>
    </header>
  );
};

