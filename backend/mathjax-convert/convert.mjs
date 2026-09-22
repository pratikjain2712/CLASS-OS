/**
 * MathML → SVG converter using MathJax server-side rendering.
 * Usage: node convert.mjs '<math>...</math>'
 * Outputs: SVG string to stdout
 */
import { mathjax } from 'mathjax-full/js/mathjax.js';
import { MathML } from 'mathjax-full/js/input/mathml.js';
import { SVG } from 'mathjax-full/js/output/svg.js';
import { liteAdaptor } from 'mathjax-full/js/adaptors/liteAdaptor.js';
import { RegisterHTMLHandler } from 'mathjax-full/js/handlers/html.js';

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);

const doc = mathjax.document('', {
  InputJax: new MathML(),
  // fontCache:'none' avoids shared <defs> that WeasyPrint can't resolve
  // across multiple inline SVG fragments in the same HTML document
  OutputJax: new SVG({ fontCache: 'none' }),
});

const input = process.argv[2] || '';
if (!input) {
  process.exit(0);
}

const isDisplay = /display\s*=\s*["']block["']/i.test(input);
const node = doc.convert(input, { display: isDisplay });
process.stdout.write(adaptor.outerHTML(node));
