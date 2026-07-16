import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function ReportMarkdown({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ children }) => (
          <h1 className="ac-display mb-6 text-3xl tracking-tight text-[var(--paper)] md:text-4xl">
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2 className="ac-display mb-4 mt-12 border-b border-[var(--line)] pb-2 text-xl text-[var(--gold-bright)] md:text-2xl">
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 className="ac-display mb-3 mt-8 text-lg text-[var(--paper)]">{children}</h3>
        ),
        p: ({ children }) => (
          <p className="ac-serif mb-4 text-[1.02rem] leading-[1.75] text-[var(--paper-dim)]">
            {children}
          </p>
        ),
        ul: ({ children }) => (
          <ul className="ac-serif mb-4 list-disc space-y-2 pl-6 text-[var(--paper-dim)]">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="ac-serif mb-4 list-decimal space-y-2 pl-6 text-[var(--paper-dim)]">
            {children}
          </ol>
        ),
        li: ({ children }) => <li className="leading-[1.7]">{children}</li>,
        a: ({ href, children }) => (
          <a
            href={href}
            className="text-[var(--gold-bright)] underline decoration-[var(--gold-deep)] underline-offset-2 hover:text-[var(--paper)]"
            target="_blank"
            rel="noopener noreferrer"
          >
            {children}
          </a>
        ),
        table: ({ children }) => (
          <div className="mb-6 overflow-x-auto border border-[var(--line)]">
            <table className="w-full min-w-[32rem] border-collapse text-left text-sm">
              {children}
            </table>
          </div>
        ),
        thead: ({ children }) => (
          <thead className="bg-[rgba(197,161,94,0.12)] text-[var(--gold-bright)]">{children}</thead>
        ),
        th: ({ children }) => (
          <th className="border-b border-[var(--line)] px-4 py-3 font-semibold">{children}</th>
        ),
        td: ({ children }) => (
          <td className="border-b border-[var(--line)] px-4 py-3 text-[var(--paper-dim)]">
            {children}
          </td>
        ),
        tr: ({ children }) => <tr className="even:bg-[rgba(255,255,255,0.02)]">{children}</tr>,
        code: ({ className, children }) => {
          const isBlock = className?.includes("language-");
          if (isBlock) {
            return (
              <pre className="mb-6 overflow-x-auto border border-[var(--line)] bg-[rgba(5,7,11,0.6)] p-4 text-sm text-[var(--paper)]">
                <code>{children}</code>
              </pre>
            );
          }
          return (
            <code className="rounded bg-[rgba(197,161,94,0.15)] px-1.5 py-0.5 font-mono text-[0.9em] text-[var(--gold-bright)]">
              {children}
            </code>
          );
        },
        pre: ({ children }) => <>{children}</>,
        hr: () => <hr className="my-10 border-[var(--line)]" />,
        strong: ({ children }) => (
          <strong className="font-semibold text-[var(--paper)]">{children}</strong>
        ),
        em: ({ children }) => <em className="italic text-[var(--mist)]">{children}</em>,
        blockquote: ({ children }) => (
          <blockquote className="ac-serif mb-4 border-l-2 border-[var(--gold)] pl-4 italic text-[var(--mist)]">
            {children}
          </blockquote>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
