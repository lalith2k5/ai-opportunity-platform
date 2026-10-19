
import type { ReactNode } from 'react';

function renderInline(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let lastIdx = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = regex.exec(text)) !== null) {
    if (m.index > lastIdx) parts.push(text.slice(lastIdx, m.index));
    const tok = m[0];
    if (tok.startsWith('**')) {
      parts.push(
        <strong key={key++} className="font-semibold text-ink">
          {tok.slice(2, -2)}
        </strong>,
      );
    } else {
      parts.push(
        <code
          key={key++}
          className="font-mono text-2xs bg-overlay border border-edge px-1 py-0.5 rounded"
        >
          {tok.slice(1, -1)}
        </code>,
      );
    }
    lastIdx = m.index + tok.length;
  }
  if (lastIdx < text.length) parts.push(text.slice(lastIdx));
  return parts;
}

export default function ChatMarkdown({ content }: { content: string }) {
  const lines = content.split('\n');
  const blocks: ReactNode[] = [];
  let currentList: { type: 'ul' | 'ol'; items: string[] } | null = null;
  let currentPara: string[] = [];
  let key = 0;

  const flushPara = () => {
    if (currentPara.length) {
      blocks.push(
        <p key={key++} className="text-sm leading-relaxed mb-3">
          {renderInline(currentPara.join(' '))}
        </p>,
      );
      currentPara = [];
    }
  };

  const flushList = () => {
    if (currentList) {
      const items = currentList.items;
      const isUl = currentList.type === 'ul';
      blocks.push(
        isUl ? (
          <ul key={key++} className="list-disc pl-5 mb-3 space-y-1.5">
            {items.map((it, i) => (
              <li key={i} className="text-sm leading-relaxed">
                {renderInline(it)}
              </li>
            ))}
          </ul>
        ) : (
          <ol key={key++} className="list-decimal pl-5 mb-3 space-y-1.5">
            {items.map((it, i) => (
              <li key={i} className="text-sm leading-relaxed">
                {renderInline(it)}
              </li>
            ))}
          </ol>
        ),
      );
      currentList = null;
    }
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      flushPara();
      flushList();
      continue;
    }

    const h2 = line.match(/^##\s+(.+)$/);
    const h3 = line.match(/^###\s+(.+)$/);
    const h4 = line.match(/^####\s+(.+)$/);
    const ul = line.match(/^[-*]\s+(.+)$/);
    const ol = line.match(/^\d+\.\s+(.+)$/);

    if (h2) {
      flushPara();
      flushList();
      blocks.push(
        <h3 key={key++} className="text-sm font-semibold text-ink mt-5 mb-2 tracking-tight">
          {renderInline(h2[1])}
        </h3>,
      );
      continue;
    }
    if (h3) {
      flushPara();
      flushList();
      blocks.push(
        <h4 key={key++} className="text-xs font-semibold text-ink uppercase tracking-wider mt-4 mb-1.5">
          {renderInline(h3[1])}
        </h4>,
      );
      continue;
    }
    if (h4) {
      flushPara();
      flushList();
      blocks.push(
        <h5 key={key++} className="text-xs font-medium text-ink-2 mt-3 mb-1">
          {renderInline(h4[1])}
        </h5>,
      );
      continue;
    }
    if (ul) {
      flushPara();
      if (!currentList || currentList.type !== 'ul') {
        flushList();
        currentList = { type: 'ul', items: [] };
      }
      currentList.items.push(ul[1]);
      continue;
    }
    if (ol) {
      flushPara();
      if (!currentList || currentList.type !== 'ol') {
        flushList();
        currentList = { type: 'ol', items: [] };
      }
      currentList.items.push(ol[1]);
      continue;
    }

    currentPara.push(line);
  }
  flushPara();
  flushList();

  return <div className="text-ink-2">{blocks}</div>;
}
