/* global monaco */
import { compile_and_parse } from './ctp';
import CTP_EXAMPLE from 'CTP/tests/data/example.cpp';
import LZString from 'lz-string';

const COMPILERS = [
  ['GCC trunk', 'gsnapshot'],
  ['GCC 10.2', 'g102'],
  ['GCC 10.1', 'g101'],
  ['GCC 9.3', 'g93'],
  ['GCC 9.2', 'g92'],
  ['GCC 9.1', 'g91'],
  ['GCC 8.3', 'g83'],
  ['GCC 8.2', 'g82'],
  ['GCC 8.1', 'g81'],
  ['GCC 7.5', 'g75'],
  ['GCC 7.4', 'g74']
  // ['GCC 7.3', 'g73'], Problem with std::string_view
  // ['GCC 7.2', 'g72']
];

const COMPILER_MESSAGE_RE = /<source>:(\d+):(\d+): ((?:fatal )?error|warning):\s+(.+)/;
const DEFAULT_PLAYGROUND_DATA = {
  code: CTP_EXAMPLE,
  compiler: 'g102',
  compiler_flags: '-fpermissive -std=c++17',
  show_compiler_log: true
};

export class Playground {
  constructor (editor_model) {
    this._data = { ...DEFAULT_PLAYGROUND_DATA };
    this._compiling = null;
    this._output_is_compiling = null;

    this._model = editor_model;
    this._on_change = null;

    // Setup compiler options.
    this._compiler_picker_select = document.getElementById('compiler-picker');
    for (const compiler of COMPILERS) {
      this._compiler_picker_select.options[this._compiler_picker_select.options.length] = new Option(compiler[0], compiler[1]);
    }
    this._compiler_status = document.getElementById('compiler-status');
    this._compiler_flags_input = document.getElementById('compiler-flags');
    this._show_compiler_log_input = document.getElementById('show-compiler-log-input');
    this._output_node = document.getElementById('output');

    this._model.onDidChangeContent(() => {
      this._data.code = this._model.getValue();
      this.compile();
    });
    this._compiler_picker_select.addEventListener('change', e => {
      this._data.compiler = e.target.value;
      this.compile();
    });
    this._compiler_flags_input.addEventListener('input', e => {
      this._data.compiler_flags = e.target.value;
      this.compile();
    });
    this._show_compiler_log_input.addEventListener('change', e => {
      this._data.show_compiler_log = e.target.checked;
      this.compile();
    });
  }

  serialize () {
    return this._data;
  }

  deserialize (data) {
    if (!data) {
      return;
    }
    for (const key of Object.keys(this._data)) {
      if (Object.prototype.hasOwnProperty.call(data, key)) {
        if (typeof this._data[key] === 'boolean') {
          this._data[key] = data[key] === 'true';
        } else {
          this._data[key] = data[key];
        }
      }
    }
    this._update_ui();
  }

  reset () {
    this._data = { ...DEFAULT_PLAYGROUND_DATA };
    this._update_ui();
  }

  register_on_change (callback) {
    this._on_change = callback;
  }

  _update_ui () {
    this._model.setValue(this._data.code);
    for (const option of this._compiler_picker_select.options) {
      if (option.value === this._data.compiler) {
        option.selected = 'selected';
      }
    }
    this._compiler_flags_input.value = this._data.compiler_flags;
    this._show_compiler_log_input.checked = this._data.show_compiler_log;
  }

  compile () {
    if (this._on_change) {
      this._on_change();
    }

    clearTimeout(this._output_is_compiling);
    this._output_is_compiling = setTimeout(() => {
      this._output_node.innerHTML = '';
      const para = document.createElement('span');
      const node = document.createTextNode('<Compiling...>');
      para.classList.add('info');
      para.appendChild(node);
      this._output_node.appendChild(para);

      // Spin compiler status.
      this._compiler_status.style.color = null;
      this._compiler_status.classList.remove('fa-check-circle');
      this._compiler_status.classList.add('fa-spinner');
    }, 500);

    if (this._compiling !== null) {
      this._compiling.cancel();
    }
    this._compiling = compile_and_parse(this._data.compiler, this._data.compiler_flags, this._data.show_compiler_log,
      this._data.code);
    this._compiling.promise.then(([succeeded, printers]) => this._output(succeeded, printers));
  }

  _output (compilation_succeeded, printers) {
    clearTimeout(this._output_is_compiling);

    this._output_node.innerHTML = '';
    let compile_warning = false;
    const widgets = [];
    for (const printer of printers) {
      const para = document.createElement('span');
      const node = document.createTextNode(printer.message);
      if (printer.error_output) {
        para.classList.add('stderr');
      } else {
        para.classList.add('stdout');
      }
      para.appendChild(node);
      this._output_node.appendChild(para);

      if (printer.compiler_output) {
        compile_warning = true;
        const match = COMPILER_MESSAGE_RE.exec(printer.message);
        if (match) {
          const line = parseInt(match[1]);
          if (line > this._model.getLineCount()) {
            continue;
          }
          const start = this._model.getLineFirstNonWhitespaceColumn(line);
          const end = this._model.getLineLastNonWhitespaceColumn(line);
          const severity = match[3] === 'warning' ? 2 : 3;
          widgets.push(
            {
              severity: severity,
              source: match[4],
              message: match[3],
              startLineNumber: line,
              startColumn: start,
              endLineNumber: line,
              endColumn: end
            }
          );
        }
      }
    }
    // Set compiler status.
    this._compiler_status.style.color = null;
    if (compilation_succeeded) {
      this._compiler_status.classList.add('fa-check-circle');
    } else {
      this._compiler_status.classList.add('fa-times-circle');
    }
    if (compile_warning || !compilation_succeeded) {
      this._compiler_status.style.color = 'rgb(255, 101, 0)';
    } else {
      this._compiler_status.style.color = 'rgb(18, 187, 18)';
    }
    this._compiler_status.classList.remove('fa-spinner');

    monaco.editor.setModelMarkers(this._model, 'compilerId', widgets);
  }
}

export class PlaygroundControl {
  constructor (playground) {
    this._playground = playground;
    this._save_playground = true;
    this._short_link = true;

    const reset_btn = document.getElementById('reset-btn');
    reset_btn.addEventListener('click', e => {
      this._playground.reset();
    });

    this._share_link = document.getElementById('share-link');
    document.getElementById('share-link-to-clipboard-btn').addEventListener('click', e => {
      navigator.clipboard.writeText(this._share_link.value);
    });

    document.getElementById('share-link-length').addEventListener('change', e => {
      this._short_link = e.target.value === 'Short';
      this._display_share_link();
    });

    // Open/close share panel.
    const share_panel = document.getElementById('share-panel');
    const open_share_panel_btn = document.getElementById('open-share-panel-btn');
    share_panel.style.top = (open_share_panel_btn.offsetHeight + 5) + 'px';
    open_share_panel_btn.addEventListener('click', () => {
      if (share_panel.style.visibility === 'visible') {
        share_panel.style.visibility = 'hidden';
      } else {
        share_panel.style.visibility = 'visible';
        this._display_share_link();
      }
    });
    window.addEventListener('click', (e) => {
      if (!share_panel.contains(e.target) && !open_share_panel_btn.contains(e.target)) {
        share_panel.style.visibility = 'hidden';
      }
    });

    // Align buttons width and height.
    const github_btn = document.getElementById('github');
    const max_w = Math.max(github_btn.offsetWidth, open_share_panel_btn.offsetWidth, reset_btn.offsetWidth) + 'px';
    github_btn.style.width = max_w;
    reset_btn.style.width = max_w;
    open_share_panel_btn.style.width = max_w;
    document.getElementById('header').style.height = document.getElementById('compiler-picker').offsetHeight + 'px';

    this._playground.register_on_change(() => this._save_to_storage());
  }

  init () {
    let data = this._decode_share_url(window.location.href);
    if (!data) {
      data = this._load_from_storage();
    } else {
      this._save_playground = false;
    }
    this._playground.deserialize(data);
  }

  _load_from_storage () {
    const data = {};
    for (const key of Object.keys(DEFAULT_PLAYGROUND_DATA)) {
      const value = window.localStorage.getItem(key);
      if (value !== null) {
        data[key] = value;
      }
    }
    return data;
  }

  _save_to_storage () {
    if (this._save_playground) {
      const data = this._playground.serialize();
      for (const key of Object.keys(data)) {
        window.localStorage.setItem(key, data[key]);
      }
    }
  }

  _display_share_link () {
    const link = this._create_share_link();
    const url = location.protocol + '//' + location.host + location.pathname + link;
    if (this._short_link) {
      fetch('https://viatorus.pythonanywhere.com/short', {
        method: 'POST',
        body: url
      })
        .then(e => {
          if (e.ok) {
            return e.text();
          }
          return 'Failed to load.';
        })
        .then(txt => { this._share_link.value = txt; });
      this._share_link.value = '';
    } else {
      this._share_link.value = url;
    }
  }

  _create_share_link () {
    const params = [];
    for (const [key, value] of Object.entries(this._playground.serialize())) {
      params.push(`${key}=${encodeURIComponent(value)}`);
    }
    return '#' + LZString.compressToBase64(params.join('&'));
  }

  _decode_share_url (url) {
    const i = url.indexOf('#');
    if (i >= 0) {
      const decoded = LZString.decompressFromBase64(url.slice(i + 1));
      const data = {};
      for (const param of decoded.split('&')) {
        const [name, value] = param.split('=');
        if (typeof value === 'string') {
          data[name] = decodeURIComponent(value);
        }
      }
      return data;
    }
    return null;
  }
}
