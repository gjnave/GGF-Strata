import { useNative } from '../lib/native';
import { Screen } from '../components/layout';
import '../styles/ggf-hardware-guide.css';

const families = [
  { id: 'qwen36', title: 'Qwen3.6 35B-A3B', gpu: '24 GB tested here', context: '256K model limit; 128K tested here', note: '128K used about 14 GB total GPU memory idle and 20 GB while reading a 100K prompt on this RTX 4090.' },
  { id: 'qwen38', title: 'Qwen3.8 Flash-Next', gpu: '12 GB published example', context: '256K native; 512K offered experimentally', note: 'Includes GSQ-RCO, Coder, Swift, Gyro, Unsloth and NVFP4 options. Longer contexts need more graphics memory.' },
  { id: 'deepseek41', title: 'DeepSeek V4.1 Flash', gpu: '12 GB minimum', context: '1M model limit; 8K measured; up to 256K offered before pack inspection', note: 'Longer contexts are possible if the pack reports support. Beyond 256K is shown as untested. Large prompts can be slow.' },
];
const group = (family: string) => family === 'deepseek41' ? 'deepseek41' : family === 'qwen36' ? 'qwen36' : 'qwen38';
const label = (family: string, model: string) => ['qwen', 'qwen36', 'deepseek41', 'gyro', 'nvfp4'].includes(family) ? model : `${family === 'coder' ? 'Coder' : family[0].toUpperCase() + family.slice(1)} ${model}`;
const gb = (n?: number | null) => n == null ? '—' : `${n.toLocaleString()} GB`;
const pcFit = (value?: string | null) => ({ fits: 'Fits estimate', tight: 'Tight', spills: 'Uses SSD; slower', no_card: 'GPU unsupported', unknown: 'Check plan' } as Record<string, string>)[value ?? ''] ?? 'Check plan';

export function HardwareGuide() {
  const native = useNative();
  const rows = native?.catalog?.families.flatMap(f => f.sizes.map(s => ({ ...s, family: f.family }))) ?? [];
  const ram = native?.hardware?.ram_gb;
  const gpu = native?.hardware?.gpus.map(g => `${g.name}: ${g.vram_gb} GB`).join(' + ');
  return <Screen title="Hardware guide" sub="Choose a model, then compare its quantizations with your computer" width="wide">
    <div className="ggf-guide">
      <p><strong>This computer:</strong> {gpu ?? 'GPU not detected'} · {ram == null ? 'RAM not detected' : `${ram.toFixed(1)} GB system RAM`}. Figures are estimates for the model. Leave room for Windows, the agent and other generation apps.</p>
      <p><strong>RAM and VRAM are separate.</strong> In the RAM column, “RAM” means system memory beside the GPU; “combined” means that model's catalog estimate counts RAM and VRAM together. Download is required SSD space, not memory use.</p>
      <p><strong>Context:</strong> the number of tokens one conversation can hold. A model's advertised or offered maximum is not a guarantee that it fits your hardware. Pick the context in Models when loading it; each larger setting uses more memory.</p>
      {families.map(f => <section key={f.id} className="ggf-guide__family">
        <h2>{f.title}</h2><p>{f.note}</p>
        <div className="ggf-guide__scroll"><table><thead><tr><th>Option / quant</th><th>GPU guidance</th><th>RAM guidance</th><th>Download</th><th>Context guidance</th><th>This PC</th><th>Files here</th></tr></thead><tbody>
          {rows.filter(r => group(r.family) === f.id && !(r.family === 'deepseek41' && /^UD-Q8/i.test(r.model))).map(r => <tr key={`${r.family}-${r.model}`}>
            <th scope="row">{label(r.family, r.model)}</th><td>{r.family === 'nvfp4' ? 'NVIDIA only; check plan' : f.gpu}</td><td>{gb(r.ram_needed_gb)} {r.family !== 'deepseek41' && (r as typeof r & { mem_total?: boolean }).mem_total ? 'combined' : 'RAM'}</td><td>{gb(r.download_gb)}</td><td>{f.context}</td><td>{pcFit(r.on_this_pc)}</td><td>{r.installed ? 'Downloaded' : 'Download needed'}</td>
          </tr>)}
        </tbody></table></div>
      </section>)}
      <p><strong>For this installation:</strong> Qwen3.6 UD-Q4_K_XL passed a 100,047-token input and full agent file tools at 128K. Other quantizations have not completed the same local tests. DeepSeek's 34 GB figure for 1.75 bpw means system RAM beside a suitable GPU.</p>
      <p>Sources: <a href="https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md">Strata model guide</a> · <a href="https://github.com/Niko1221/Strata/blob/main/docs/DEEPSEEK41.md">DeepSeek details</a>. Catalog figures update with Strata; the local test note describes this computer only.</p>
      <a className="ggf-guide__back" href="#/models">← Back to Models</a>
    </div>
  </Screen>;
}
