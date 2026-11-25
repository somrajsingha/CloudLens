import { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { UploadView } from './components/UploadView';
import { MyFilesView } from './components/MyFilesView';
import { AdminView } from './components/AdminView';
import { CloudFile, cloud, currentUser, finishSignIn, getToken, signIn, signOut } from './cloud';
import { TabType } from './types';

export default function App() {
  const [currentTab, setCurrentTab] = useState<TabType>('upload');
  const [files, setFiles] = useState<CloudFile[]>([]);
  const [user, setUser] = useState(currentUser());
  const [error, setError] = useState('');

  const refreshFiles = async () => {
    if (!getToken()) return;
    try { setFiles((await cloud.files()).files); setUser(currentUser()); }
    catch (err) { setError((err as Error).message); if (!currentUser()) setUser(null); }
  };

  useEffect(() => {
    finishSignIn().then(() => { setUser(currentUser()); refreshFiles(); })
      .catch(err => setError((err as Error).message));
  }, []);

  useEffect(() => {
    if (!user) return;
    const timer = window.setInterval(refreshFiles, 5000);
    return () => window.clearInterval(timer);
  }, [user]);

  return (
    <div className="min-h-screen w-full bg-[#ebebe9] flex flex-col relative overflow-hidden">
      <div className="fixed inset-0 pointer-events-none z-0" style={{backgroundImage: "url('/cloudlens-bg.jpg')", backgroundSize: 'cover', backgroundPosition: 'center bottom'}} />
      <div className="fixed inset-0 pointer-events-none z-0 bg-gradient-to-b from-transparent via-white/10 to-transparent" />
      <Navbar currentTab={currentTab} onSelectTab={setCurrentTab} fileCount={files.length} user={user} onSignIn={signIn} onSignOut={signOut} />
      {error && <div role="alert" className="relative z-20 mx-auto max-w-3xl px-4 py-2 rounded-xl bg-red-50 text-red-800 text-sm border border-red-200">{error} <button className="underline ml-2" onClick={() => setError('')}>Dismiss</button></div>}
      <main className="flex-1 flex flex-col justify-center relative z-10">
        {currentTab === 'upload' && <UploadView signedIn={Boolean(user)} onFileProcessed={refreshFiles} onGoToFiles={() => setCurrentTab('files')} />}
        {currentTab === 'files' && <MyFilesView files={files} signedIn={Boolean(user)} onDeleteFile={async id => {try {await cloud.remove(id); await refreshFiles();} catch (err) {setError((err as Error).message);}}} onGoToUpload={() => setCurrentTab('upload')} />}
        {currentTab === 'admin' && <AdminView isAdmin={Boolean(user?.isAdmin)} signedIn={Boolean(user)} />}
      </main>
      <footer className="w-full py-4 relative z-10" />
    </div>
  );
}
