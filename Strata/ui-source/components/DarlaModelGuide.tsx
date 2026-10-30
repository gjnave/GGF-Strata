import { tr } from '../lib/i18n';
import { navigate } from '../lib/router';
import { useNative, nativeSettled, subscribeNative } from '../lib/native';
import { useStore } from '../lib/store';
import { useSyncExternalStore } from 'react';
import { Btn } from './ui';
import '../styles/ggf-darla-guide.css';

/** Shown on a fresh install before any local checkpoint has been prepared. */
export function DarlaModelGuide() {
    const native = useNative();
    const settled = useSyncExternalStore(subscribeNative, nativeSettled);
    const library = useStore(s => s.library);
    const hasModel = !!native?.installed?.models.some(model => model.ready)
        || !!library?.variants.some(model => model.state === 'installed' || model.state === 'loaded');
    if (!settled || hasModel) return null;
    return <section className="ggf-darla-guide" aria-labelledby="ggf-darla-title">
      <img className="ggf-darla-guide__avatar" src="/darla-guide.png" alt={tr("DARLA, your model setup guide")} />
      <div className="ggf-darla-guide__copy">
        <span className="eyebrow">{tr("Getting started with DARLA")}</span>
        <h2 id="ggf-darla-title">{tr("Choose a model before you start chatting")}</h2>
        <p>{tr("Strata is running, but no local model is downloaded yet. I'll help you pick one in the Models page.")}</p>
        <ol>
          <li>{tr("Choose one model family: Qwen3.6, Qwen3.8, or DeepSeek V4.1 Flash.")}</li>
          <li>{tr("Choose a quantization for that model. Smaller downloads generally need less RAM and VRAM; larger ones usually retain more quality.")}</li>
          <li>{tr("Review the hardware and disk estimates, then confirm the download in the app. Once it finishes, load the model to use the agent.")}</li>
        </ol>
        <p className="small muted">{tr("Browsing choices will not download anything. You can change the model storage folder in Storage settings first.")}</p>
        <Btn variant="primary" icon="models" onClick={() => navigate('models')}>{tr("Choose a model and quantization")}</Btn>
      </div>
    </section>;
}
