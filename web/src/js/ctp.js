/* global pyodide, languagePluginLoader */
import CTP_SOURCE from 'CTP/include/ctp/ctp.hpp';
import CTP_PY_SOURCE from 'CTP/src/compile_time_printer/ctp.py';
import CTP_WRAPPER_PY_SOURCE from './ctp_wrapper.py';

// Use pyodide to run python code in js.
let parse = null;
const load_python = languagePluginLoader.then(() => {
  pyodide.runPython(CTP_PY_SOURCE);
  pyodide.runPython(CTP_WRAPPER_PY_SOURCE);
  parse = pyodide.pyimport('parse');
});

function compile (compiler, compiler_flags, code) {
  const body = {
    source: code,
    options: {
      userArguments: compiler_flags + ' -fno-diagnostics-color -fsyntax-only'
    }
  };
  return fetch(`https://godbolt.org/api/compiler/${compiler}/compile`, {
    headers: {
      accept: 'application/json',
      'content-type': 'application/json'
    },
    body: JSON.stringify(body),
    method: 'POST'
  })
    .then(e => e.json())
    .then(e => [e.code === 0, e.stderr.map(x => x.text)]);
}

const CTP_INCLUDE = /#\s*include\s*<ctp\/ctp\.hpp>/;
const CTP_INCLUDE_GLOBAL = /#\s*include\s*<ctp\/ctp\.hpp>/g;
const CTP_LOC = CTP_SOURCE.split('\n').length - 1;

function include_ctp_header (code) {
  // Find out at which line the include is for better compiler log messages.
  let line_nbr = -1;
  const lines = code.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (CTP_INCLUDE.test(lines[i])) {
      line_nbr = i + 1;
      break;
    }
  }
  if (line_nbr === -1) {
    return [[0, 0], code];
  }
  // Replace only first include with the content and the rest leave blank.
  code = code.replace(CTP_INCLUDE, CTP_SOURCE);
  code = code.replaceAll(CTP_INCLUDE_GLOBAL, '');
  return [[CTP_LOC, line_nbr], code];
}

export function compile_and_parse (compiler, compiler_flags, show_compiler_log, code) {
  let timeout, include_offset;
  [include_offset, code] = include_ctp_header(code);

  const promise = new Promise(function (resolve, reject) {
    timeout = setTimeout(function () {
      compile(compiler, compiler_flags, code)
        .then(([succeeded, log]) =>
          load_python
            .then(() => [succeeded, parse(include_offset, log, show_compiler_log)])
        )
        .then(resolve).catch(reject);
    }, 500);
  });
  return {
    promise: promise,
    cancel: function () {
      clearTimeout(timeout);
    }
  };
}
