import type { ReactNode } from "react";
import { isSafeUrl } from "../../lib/format";

/**
 * Small, safe Markdown renderer for challenge descriptions.
 *
 * It builds React elements directly and never injects HTML, so a description
 * can't run scripts. Supported: # headings, paragraphs, - and 1. lists,
 * ``` code blocks, `code`, **bold**, *italic* and [links](https://...).
 */
const INLINE = /(`[^`\n]+`|\*\*[^*\n]+\*\*|\*[^*\n]+\*|\[[^\]\n]+\]\([^)\s]+\))/g;
const LINK = /^\[([^\]]+)\]\(([^)\s]+)\)$/;

function renderInline(text: string): ReactNode[] {
  return text.split(INLINE).map((part, index) => {
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      return (
        <code key={index} className="rounded bg-gray-800 px-2 font-mono text-xs text-gray-50">
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return (
        <strong key={index} className="font-semibold text-gray-50">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    const link = LINK.exec(part);
    if (link) {
      // Only http(s) links become clickable; anything else stays plain text.
      if (!isSafeUrl(link[2])) return link[1];
      return (
        <a
          key={index}
          href={link[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-brand-400 transition-colors duration-200 hover:underline"
        >
          {link[1]}
        </a>
      );
    }
    return part;
  });
}

const HEADING_CLASSES = [
  "text-lg font-semibold text-gray-50",
  "text-base font-semibold text-gray-50",
  "text-sm font-semibold text-gray-50",
];

const UNORDERED = /^\s*[-*]\s+/;
const ORDERED = /^\s*\d+[.)]\s+/;

function renderBlocks(source: string): ReactNode[] {
  const lines = source.replace(/\r\n?/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (line.trim() === "") {
      index += 1;
      continue;
    }

    if (line.trimStart().startsWith("```")) {
      const code: string[] = [];
      index += 1;
      while (index < lines.length && !lines[index].trimStart().startsWith("```")) {
        code.push(lines[index]);
        index += 1;
      }
      index += 1; // closing fence
      blocks.push(
        <pre
          key={blocks.length}
          className="overflow-x-auto rounded-lg border border-gray-800 bg-gray-950 p-4 font-mono text-xs text-gray-300"
        >
          {code.join("\n")}
        </pre>,
      );
      continue;
    }

    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    if (heading) {
      blocks.push(
        <p key={blocks.length} role="heading" aria-level={heading[1].length + 2}
          className={HEADING_CLASSES[heading[1].length - 1]}>
          {renderInline(heading[2])}
        </p>,
      );
      index += 1;
      continue;
    }

    const listPattern = UNORDERED.test(line) ? UNORDERED : ORDERED.test(line) ? ORDERED : null;
    if (listPattern) {
      const items: string[] = [];
      while (index < lines.length && listPattern.test(lines[index])) {
        items.push(lines[index].replace(listPattern, ""));
        index += 1;
      }
      const children = items.map((item, itemIndex) => <li key={itemIndex}>{renderInline(item)}</li>);
      blocks.push(
        listPattern === UNORDERED ? (
          <ul key={blocks.length} className="flex list-disc flex-col gap-2 pl-6">{children}</ul>
        ) : (
          <ol key={blocks.length} className="flex list-decimal flex-col gap-2 pl-6">{children}</ol>
        ),
      );
      continue;
    }

    const paragraph: string[] = [];
    while (
      index < lines.length &&
      lines[index].trim() !== "" &&
      !lines[index].trimStart().startsWith("```") &&
      !/^#{1,3}\s+/.test(lines[index]) &&
      !UNORDERED.test(lines[index]) &&
      !ORDERED.test(lines[index])
    ) {
      paragraph.push(lines[index]);
      index += 1;
    }
    blocks.push(
      <p key={blocks.length} className="whitespace-pre-line">
        {renderInline(paragraph.join("\n"))}
      </p>,
    );
  }
  return blocks;
}

export function Markdown({ source }: { source: string }) {
  return <div className="flex flex-col gap-4 text-sm text-gray-300">{renderBlocks(source)}</div>;
}
