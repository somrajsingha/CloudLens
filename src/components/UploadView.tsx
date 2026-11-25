import { useRef, useState } from 'react';
import { AlertCircle, ArrowRight, ArrowUpRight, CheckCircle2, Download, Eye, FileText, Loader2, Upload, X } from 'lucide-react';
import { CloudFile, cloud, configured } from '../cloud';

interface Props { signedIn: boolean; onFileProcessed: () => void; onGoToFiles: () => void; }
const MAX_SIZE = 10 * 1024 * 1024;
const allowed = ['image/jpeg', 'image/png', 'application/pdf'];
const size = (bytes: number) => `${(bytes / 1024 / 1024).toFixed(2)} MB`;

export function UploadView({signedIn, onFileProcessed, onGoToFiles}: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);
  const [stage, setStage] = useState<'idle' | 'uploading' | 'processing' | 'completed'>('idle');
  const [result, setResult] = useState<CloudFile | null>(null);

  function select(next: File) {
    setResult(null); setStage('idle'); setFile(next);
    if (!allowed.includes(next.type)) setError('Only JPG, PNG, and PDF files are supported.');
    else if (next.size > MAX_SIZE) setError(`File exceeds the 10 MB limit (${size(next.size)}).`);
    else if (!next.size) setError('The selected file is empty.');
    else setError('');
  }

  async function sample(path: string, name: string, type: string) {
    try {
      const response = await fetch(path);
      if (!response.ok) throw new Error('Sample file is unavailable.');
      select(new File([await response.blob()], name, {type}));
    } catch (err) { setError((err as Error).message); }
  }

  async function process() {
    if (!file || error || !signedIn) return;
    try {
      setError(''); setStage('uploading');
      const {file: created, uploadUrl, headers} = await cloud.uploadUrl(file);
      const uploaded = await fetch(uploadUrl, {method: 'PUT', headers, body: file});
      if (!uploaded.ok) throw new Error('Upload to S3 failed. Please try again.');
      setStage('processing'); onFileProcessed();
      for (let attempt = 0; attempt < 90; attempt++) {
        await new Promise(resolve => window.setTimeout(resolve, 2000));
        const latest = (await cloud.file(created.fileId)).file;
        if (latest.status === 'completed') {setResult(latest); setStage('completed'); onFileProcessed(); return;}
        if (latest.status === 'failed') throw new Error(latest.error || 'Processing failed.');
      }
      throw new Error('Processing is taking longer than expected. Check My files for its status.');
    } catch (err) {setError((err as Error).message); setStage('idle'); onFileProcessed();}
  }

  return <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 relative z-10 py-6 sm:py-10 max-w-4xl mx-auto w-full">
    <input ref={input} type="file" accept=".jpg,.jpeg,.png,.pdf" className="hidden" onChange={event => {if (event.target.files?.[0]) select(event.target.files[0]);}} />
    <h1 className="text-4xl sm:text-5xl md:text-[54px] font-bold tracking-tight text-neutral-900 leading-[1.08] text-center">Upload a file.<br />Get it back ready to use.</h1>
    <p className="mt-4 text-xs sm:text-sm md:text-[14.5px] text-neutral-600 text-center max-w-[590px] leading-relaxed">Images are resized, compressed and watermarked. PDFs and scans become searchable text. Processing starts when the file lands.</p>
    <div onDragEnter={e => {e.preventDefault(); setDragging(true);}} onDragOver={e => e.preventDefault()} onDragLeave={e => {e.preventDefault(); setDragging(false);}} onDrop={e => {e.preventDefault(); setDragging(false); if (e.dataTransfer.files[0]) select(e.dataTransfer.files[0]);}}
      onClick={() => {if (input.current) {input.current.value = ''; input.current.click();}}}
      className={`relative mt-8 sm:mt-10 w-full max-w-[620px] rounded-[22px] border-[1.5px] border-dashed transition-all cursor-pointer py-8 px-6 sm:px-10 flex flex-col items-center justify-center text-center ${dragging ? 'border-neutral-900 bg-white/80 shadow-lg' : error ? 'border-amber-500 bg-amber-50/60' : 'border-neutral-400/70 hover:border-neutral-600 bg-white/20 hover:bg-white/40'}`}>
      {file ? <>
        <div className="relative w-14 h-14 rounded-2xl bg-neutral-100 border border-neutral-300 flex items-center justify-center mb-3"><FileText className="w-7 h-7" /><button onClick={e => {e.stopPropagation(); setFile(null); setError(''); setResult(null); setStage('idle');}} title="Remove file" className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-neutral-900 text-white flex items-center justify-center"><X className="w-3.5 h-3.5" /></button></div>
        <p className="text-sm font-semibold text-neutral-900 break-all">{file.name}</p><p className="text-xs text-neutral-500 mt-1">{size(file.size)} · {file.type}</p>
        {!error && <p className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100/80 text-emerald-900 text-[11px]"><CheckCircle2 className="w-3.5 h-3.5" /> Ready to upload</p>}
      </> : <><div className="w-9 h-9 rounded-full border border-neutral-400 flex items-center justify-center mb-3 bg-white/40"><Upload className="w-4 h-4" /></div><div className="text-[14px] text-neutral-900">Drop a file here, or <span className="underline underline-offset-4 font-medium">browse</span></div><p className="mt-1 text-[11.5px] text-neutral-500">JPG, PNG or PDF. Up to 10 MB.</p></>}
    </div>
    <div className="mt-4 sm:mt-5 flex flex-wrap items-center justify-center gap-2 text-xs text-neutral-600"><span>No file handy? Try a sample:</span>
      <button onClick={() => sample('/sample-photo.jpg', 'sample-photo.jpg', 'image/jpeg')} className="inline-flex items-center gap-1 px-3 py-1 rounded-full border border-neutral-300 bg-white/60 hover:bg-white">Sample photo <ArrowUpRight className="w-3 h-3" /></button>
      <button onClick={() => sample('/sample-invoice.pdf', 'sample-invoice.pdf', 'application/pdf')} className="inline-flex items-center gap-1 px-3 py-1 rounded-full border border-neutral-300 bg-white/60 hover:bg-white">Sample PDF <ArrowUpRight className="w-3 h-3" /></button>
    </div>
    {error && <p role="alert" className="mt-4 text-xs text-amber-900 bg-amber-50 border border-amber-300 rounded-xl px-3 py-2 flex gap-2 items-center"><AlertCircle className="w-4 h-4" />{error}</p>}
    <div className="mt-6 sm:mt-7 flex flex-col items-center"><button disabled={!file || !!error || !signedIn || !configured || stage === 'uploading' || stage === 'processing'} onClick={process} className="inline-flex items-center gap-2 px-8 py-2.5 rounded-full text-xs sm:text-sm font-medium bg-black text-white disabled:opacity-40 disabled:cursor-not-allowed hover:bg-neutral-800">
      {stage === 'uploading' || stage === 'processing' ? <><Loader2 className="w-4 h-4 animate-spin" />{stage === 'uploading' ? 'Uploading...' : 'Processing...'}</> : <>Process file <ArrowRight className="w-3.5 h-3.5" /></>}</button>
      {!signedIn && <p className="mt-2 text-[11px] text-neutral-600">Sign in to process files.</p>}</div>
    {(stage === 'uploading' || stage === 'processing') && <div role="status" className="mt-6 w-full max-w-[500px] p-4 bg-white/95 rounded-2xl border border-neutral-300 shadow-xl text-xs text-neutral-700 flex gap-2 items-center"><Loader2 className="w-4 h-4 animate-spin" />{stage === 'uploading' ? 'Uploading to S3...' : 'Processing with AWS. Waiting for result...'}</div>}
    {result && <div className="mt-6 w-full max-w-[540px] p-5 bg-white/95 rounded-2xl border border-neutral-300 shadow-xl text-sm"><div className="flex items-center gap-2 font-semibold text-emerald-800"><CheckCircle2 className="w-5 h-5" /> Processing complete</div><p className="mt-2 text-neutral-700">{result.name}</p><p className="text-xs text-neutral-500">{size(result.size)} → {size(result.processedSize || 0)}</p>{result.extractedText && <p className="mt-3 p-3 bg-neutral-100 rounded-lg text-xs text-neutral-700 whitespace-pre-wrap max-h-36 overflow-auto">{result.extractedText}</p>}<div className="flex justify-between mt-4 pt-3 border-t border-neutral-200"><button onClick={onGoToFiles} className="inline-flex items-center gap-1 text-xs underline"><Eye className="w-4 h-4" />View in My files</button><button onClick={() => cloud.download(result.fileId).catch(err => setError(err.message))} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-neutral-900 text-white text-xs"><Download className="w-4 h-4" />Download</button></div></div>}
  </div>;
}
