import { marked } from 'marked';

/**
 * Parse markdown text to HTML
 */
export function parseMarkdown(markdown: string): string {
  if (!markdown) return '';

  try {
    return marked.parse(markdown) as string;
  } catch (error) {
    console.error('Error parsing markdown:', error);
    return markdown;
  }
}
