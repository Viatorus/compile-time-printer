import 'normalize.css';
import 'font-awesome/css/font-awesome.css';
import 'CSS/style.scss';
import { editor } from './editor';
import { Playground, PlaygroundControl } from './playground';

// A function is used for dragging and moving.
function dragElement (element) {
  let md; // remember mouse down info
  const first = document.getElementById('editor-panel');
  const second = document.getElementById('output-panel');

  element.onmousedown = onMouseDown;

  function onMouseDown (e) {
    md = {
      e,
      firstWidth: first.offsetWidth,
      secondWidth: second.offsetWidth
    };
    document.onmousemove = onMouseMove;
    document.onmouseup = () => {
      document.onmousemove = document.onmouseup = null;
    };
  }

  const sep_width = element.offsetWidth;
  const sep_part = '% - ' + (sep_width / 2) + 'px)';

  function onMouseMove (e) {
    const delta = {
      x: e.clientX - md.e.clientX,
      y: e.clientY - md.e.clientY
    };
    // Prevent negative-sized elements
    delta.x = Math.min(Math.max(delta.x, -md.firstWidth), md.secondWidth);
    const w1 = md.firstWidth + delta.x + sep_width;
    const w2 = md.secondWidth - delta.x + 2 * sep_width;
    first.style.width = 'calc(' + (w1 / window.innerWidth) * 100 + sep_part;
    second.style.width = 'calc(' + (w2 / window.innerWidth) * 100 + sep_part;
  }
}

dragElement(document.getElementById('separator'));

window.addEventListener('load', (event) => {
  const playground = new Playground(editor.getModel());
  const playground_control = new PlaygroundControl(playground);
  playground_control.init();
  playground.compile();

  document.getElementById('header').style.visibility = null;
  document.getElementById('playground').style.visibility = null;
});
